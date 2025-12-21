# Databricks notebook source
# MAGIC %md
# MAGIC # Budget vs Actual - Gold Layer
# MAGIC
# MAGIC Compute budget KPIs aggregated by program, project, and period.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

# Create gold schema
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.gold")

# Create budget vs actual table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.ppm_budget_vs_actual (
    metric_id STRING NOT NULL,
    metric_name STRING NOT NULL,
    dimension STRING NOT NULL,
    dimension_value STRING NOT NULL,
    period DATE NOT NULL,
    period_type STRING NOT NULL,
    value DECIMAL(18, 2),
    unit STRING NOT NULL DEFAULT 'USD',
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (metric_id)
)
USING DELTA
PARTITIONED BY (period)
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import (
    col, lit, sum as spark_sum, coalesce, date_trunc, concat_ws,
    current_timestamp, uuid, when
)
from datetime import date

# Get active projects with budget lines
budget_data = spark.sql(f"""
SELECT
    p.project_id,
    p.program_id,
    p.name as project_name,
    p.currency,
    bl.amount as budget_amount,
    bl.actual_amount,
    bl.committed_date,
    bl.paid_date,
    bl.category
FROM {catalog}.silver.notion_projects p
LEFT JOIN {catalog}.silver.notion_budget_lines bl
    ON p.project_id = bl.project_id
    AND bl.is_archived = false
WHERE p.is_archived = false
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute Metrics by Project

# COMMAND ----------

# Aggregate by project
project_metrics = budget_data.groupBy("project_id", "project_name", "currency").agg(
    spark_sum("budget_amount").alias("total_budget"),
    spark_sum(when(col("paid_date").isNotNull(), col("actual_amount"))).alias("total_actual"),
    spark_sum(when(col("committed_date").isNotNull(), col("budget_amount"))).alias("total_committed")
)

# Calculate variance and burn rate
project_metrics = project_metrics.withColumn(
    "variance",
    coalesce(col("total_actual"), lit(0)) - coalesce(col("total_budget"), lit(0))
).withColumn(
    "burn_rate_pct",
    when(
        col("total_budget") > 0,
        (coalesce(col("total_actual"), lit(0)) / col("total_budget")) * 100
    ).otherwise(lit(0))
)

display(project_metrics)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Metric Records

# COMMAND ----------

from pyspark.sql.functions import expr, monotonically_increasing_id
import uuid

# Current period (month)
current_period = date.today().replace(day=1)

# Create metric records for each project
records = []

for row in project_metrics.collect():
    project_id = row["project_id"]
    currency = row["currency"] or "USD"

    # Budget metric
    records.append({
        "metric_id": str(uuid.uuid4()),
        "metric_name": "budget",
        "dimension": "project",
        "dimension_value": project_id,
        "period": current_period,
        "period_type": "month",
        "value": float(row["total_budget"] or 0),
        "unit": currency
    })

    # Actual metric
    records.append({
        "metric_id": str(uuid.uuid4()),
        "metric_name": "actual",
        "dimension": "project",
        "dimension_value": project_id,
        "period": current_period,
        "period_type": "month",
        "value": float(row["total_actual"] or 0),
        "unit": currency
    })

    # Variance metric
    records.append({
        "metric_id": str(uuid.uuid4()),
        "metric_name": "variance",
        "dimension": "project",
        "dimension_value": project_id,
        "period": current_period,
        "period_type": "month",
        "value": float(row["variance"] or 0),
        "unit": currency
    })

    # Burn rate metric
    records.append({
        "metric_id": str(uuid.uuid4()),
        "metric_name": "burn_rate",
        "dimension": "project",
        "dimension_value": project_id,
        "period": current_period,
        "period_type": "month",
        "value": float(row["burn_rate_pct"] or 0),
        "unit": "percent"
    })

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute Portfolio Totals

# COMMAND ----------

# Portfolio-level totals
portfolio_totals = project_metrics.agg(
    spark_sum("total_budget").alias("portfolio_budget"),
    spark_sum("total_actual").alias("portfolio_actual")
).collect()[0]

# Add portfolio metrics
records.append({
    "metric_id": str(uuid.uuid4()),
    "metric_name": "budget",
    "dimension": "portfolio",
    "dimension_value": "total",
    "period": current_period,
    "period_type": "month",
    "value": float(portfolio_totals["portfolio_budget"] or 0),
    "unit": "USD"
})

records.append({
    "metric_id": str(uuid.uuid4()),
    "metric_name": "actual",
    "dimension": "portfolio",
    "dimension_value": "total",
    "period": current_period,
    "period_type": "month",
    "value": float(portfolio_totals["portfolio_actual"] or 0),
    "unit": "USD"
})

records.append({
    "metric_id": str(uuid.uuid4()),
    "metric_name": "variance",
    "dimension": "portfolio",
    "dimension_value": "total",
    "period": current_period,
    "period_type": "month",
    "value": float((portfolio_totals["portfolio_actual"] or 0) - (portfolio_totals["portfolio_budget"] or 0)),
    "unit": "USD"
})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Gold Table

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DateType, DecimalType, TimestampType

schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("metric_name", StringType(), False),
    StructField("dimension", StringType(), False),
    StructField("dimension_value", StringType(), False),
    StructField("period", DateType(), False),
    StructField("period_type", StringType(), False),
    StructField("value", DecimalType(18, 2), True),
    StructField("unit", StringType(), False)
])

metrics_df = spark.createDataFrame(records, schema)
metrics_df = metrics_df.withColumn("computed_at", current_timestamp())

# COMMAND ----------

# Write with merge (replace metrics for current period)
metrics_df.createOrReplaceTempView("new_metrics")

spark.sql(f"""
MERGE INTO {catalog}.gold.ppm_budget_vs_actual AS target
USING new_metrics AS source
ON target.metric_id = source.metric_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# Cleanup old metrics for current period (remove duplicates)
spark.sql(f"""
DELETE FROM {catalog}.gold.ppm_budget_vs_actual
WHERE period = '{current_period}'
  AND metric_id NOT IN (
    SELECT metric_id FROM new_metrics
  )
""")

# COMMAND ----------

display(spark.sql(f"""
SELECT metric_name, dimension, SUM(value) as total
FROM {catalog}.gold.ppm_budget_vs_actual
WHERE period = '{current_period}'
GROUP BY metric_name, dimension
"""))

print("Budget vs Actual computation complete!")
