# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Checks - Gold Layer
# MAGIC
# MAGIC Run data quality validations and store results.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.data_quality_metrics (
    metric_id STRING NOT NULL,
    check_date DATE NOT NULL,
    table_name STRING NOT NULL,
    check_type STRING NOT NULL,
    column_name STRING,
    expected_value STRING,
    actual_value STRING,
    passed BOOLEAN NOT NULL,
    severity STRING,
    details STRING,
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (metric_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from datetime import date
from pyspark.sql.functions import current_timestamp
import uuid
import json

today = date.today()
results = []

def add_result(table, check_type, column, expected, actual, passed, severity, details=None):
    results.append({
        "metric_id": str(uuid.uuid4()),
        "check_date": today,
        "table_name": table,
        "check_type": check_type,
        "column_name": column,
        "expected_value": str(expected) if expected else None,
        "actual_value": str(actual) if actual else None,
        "passed": passed,
        "severity": severity,
        "details": json.dumps(details) if details else None
    })

# COMMAND ----------

# MAGIC %md
# MAGIC ## Row Count Checks

# COMMAND ----------

# Define expected minimum row counts
tables_to_check = [
    (f"{catalog}.silver.notion_projects", 0),  # At least some projects
    (f"{catalog}.silver.notion_programs", 0),
    (f"{catalog}.silver.notion_budget_lines", 0),
    (f"{catalog}.silver.notion_risks", 0),
    (f"{catalog}.silver.notion_actions", 0),
]

for table_name, min_rows in tables_to_check:
    try:
        count = spark.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()[0]["cnt"]
        passed = count >= min_rows
        severity = "critical" if not passed and min_rows > 0 else "info"

        add_result(
            table=table_name,
            check_type="row_count",
            column=None,
            expected=f">= {min_rows}",
            actual=count,
            passed=passed,
            severity=severity
        )
    except Exception as e:
        add_result(
            table=table_name,
            check_type="row_count",
            column=None,
            expected=f">= {min_rows}",
            actual="ERROR",
            passed=False,
            severity="critical",
            details={"error": str(e)}
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Null Rate Checks

# COMMAND ----------

# Check null rates for key columns
null_checks = [
    (f"{catalog}.silver.notion_projects", "name", 0.0),
    (f"{catalog}.silver.notion_projects", "project_id", 0.0),
    (f"{catalog}.silver.notion_budget_lines", "project_id", 0.0),
    (f"{catalog}.silver.notion_risks", "project_id", 0.1),  # Allow 10% null
]

for table_name, column, max_null_rate in null_checks:
    try:
        result = spark.sql(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) as nulls
            FROM {table_name}
        """).collect()[0]

        total = result["total"]
        nulls = result["nulls"]
        null_rate = nulls / total if total > 0 else 0.0

        passed = null_rate <= max_null_rate
        severity = "warning" if not passed else "info"

        add_result(
            table=table_name,
            check_type="null_rate",
            column=column,
            expected=f"<= {max_null_rate * 100}%",
            actual=f"{null_rate * 100:.2f}%",
            passed=passed,
            severity=severity,
            details={"total": total, "nulls": nulls}
        )
    except Exception as e:
        add_result(
            table=table_name,
            check_type="null_rate",
            column=column,
            expected=f"<= {max_null_rate * 100}%",
            actual="ERROR",
            passed=False,
            severity="warning",
            details={"error": str(e)}
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Referential Integrity Checks

# COMMAND ----------

# Check that FK references exist
ref_checks = [
    (f"{catalog}.silver.notion_projects", "program_id", f"{catalog}.silver.notion_programs", "program_id"),
    (f"{catalog}.silver.notion_budget_lines", "project_id", f"{catalog}.silver.notion_projects", "project_id"),
    (f"{catalog}.silver.notion_risks", "project_id", f"{catalog}.silver.notion_projects", "project_id"),
]

for child_table, child_col, parent_table, parent_col in ref_checks:
    try:
        orphans = spark.sql(f"""
            SELECT COUNT(*) as cnt
            FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
            WHERE c.{child_col} IS NOT NULL
              AND p.{parent_col} IS NULL
        """).collect()[0]["cnt"]

        passed = orphans == 0
        severity = "warning" if not passed else "info"

        add_result(
            table=child_table,
            check_type="referential_integrity",
            column=child_col,
            expected="0 orphans",
            actual=f"{orphans} orphans",
            passed=passed,
            severity=severity,
            details={"parent_table": parent_table}
        )
    except Exception as e:
        add_result(
            table=child_table,
            check_type="referential_integrity",
            column=child_col,
            expected="0 orphans",
            actual="ERROR",
            passed=False,
            severity="warning",
            details={"error": str(e)}
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Freshness Checks

# COMMAND ----------

# Check data freshness (last sync time)
try:
    freshness = spark.sql(f"""
        SELECT
            database_name,
            MAX(synced_at) as last_sync,
            TIMESTAMPDIFF(HOUR, MAX(synced_at), current_timestamp()) as hours_since_sync
        FROM {catalog}.bronze.notion_raw_pages
        GROUP BY database_name
    """).collect()

    for row in freshness:
        hours = row["hours_since_sync"] or 999
        passed = hours < 24  # Data should be less than 24 hours old
        severity = "critical" if hours >= 48 else ("warning" if hours >= 24 else "info")

        add_result(
            table=f"{catalog}.bronze.notion_raw_pages",
            check_type="freshness",
            column=f"database_name={row['database_name']}",
            expected="< 24 hours",
            actual=f"{hours} hours",
            passed=passed,
            severity=severity
        )
except Exception as e:
    add_result(
        table=f"{catalog}.bronze.notion_raw_pages",
        check_type="freshness",
        column=None,
        expected="< 24 hours",
        actual="ERROR",
        passed=False,
        severity="warning",
        details={"error": str(e)}
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Results

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DateType, BooleanType

schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("check_date", DateType(), False),
    StructField("table_name", StringType(), False),
    StructField("check_type", StringType(), False),
    StructField("column_name", StringType(), True),
    StructField("expected_value", StringType(), True),
    StructField("actual_value", StringType(), True),
    StructField("passed", BooleanType(), False),
    StructField("severity", StringType(), True),
    StructField("details", StringType(), True)
])

dq_df = spark.createDataFrame(results, schema)
dq_df = dq_df.withColumn("computed_at", current_timestamp())

dq_df.createOrReplaceTempView("dq_updates")

spark.sql(f"""
MERGE INTO {catalog}.gold.data_quality_metrics AS target
USING dq_updates AS source
ON target.metric_id = source.metric_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# Show summary
display(spark.sql(f"""
SELECT
    passed,
    severity,
    COUNT(*) as check_count
FROM {catalog}.gold.data_quality_metrics
WHERE check_date = '{today}'
GROUP BY passed, severity
ORDER BY passed, severity
"""))

# Show failures
print("\nFailed checks:")
display(spark.sql(f"""
SELECT table_name, check_type, column_name, expected_value, actual_value, severity
FROM {catalog}.gold.data_quality_metrics
WHERE check_date = '{today}' AND passed = false
ORDER BY severity
"""))

print("Data quality checks complete!")
