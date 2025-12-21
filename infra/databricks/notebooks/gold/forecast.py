# Databricks notebook source
# MAGIC %md
# MAGIC # Forecast - Gold Layer
# MAGIC
# MAGIC Compute simple run-rate forecasts for project spending.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.ppm_forecast (
    forecast_id STRING NOT NULL,
    project_id STRING NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_type STRING NOT NULL,
    remaining_budget DECIMAL(18, 2),
    projected_spend DECIMAL(18, 2),
    projected_variance DECIMAL(18, 2),
    confidence STRING,
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (forecast_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import (
    col, lit, when, coalesce, datediff, current_date, current_timestamp
)
from datetime import date
import uuid

today = date.today()

# COMMAND ----------

# Get project data with budget and actuals
project_data = spark.sql(f"""
SELECT
    p.project_id,
    p.budget_total,
    p.start_date,
    p.end_date,
    COALESCE(SUM(bl.actual_amount), 0) as total_actual,
    MIN(bl.paid_date) as first_spend_date,
    MAX(bl.paid_date) as last_spend_date
FROM {catalog}.silver.notion_projects p
LEFT JOIN {catalog}.silver.notion_budget_lines bl
    ON p.project_id = bl.project_id
    AND bl.is_archived = false
    AND bl.paid_date IS NOT NULL
WHERE p.is_archived = false
GROUP BY p.project_id, p.budget_total, p.start_date, p.end_date
""")

# COMMAND ----------

# Calculate run-rate forecast
forecast_df = project_data.withColumn(
    "days_elapsed",
    when(
        col("first_spend_date").isNotNull() & col("last_spend_date").isNotNull(),
        datediff(col("last_spend_date"), col("first_spend_date"))
    ).otherwise(lit(0))
).withColumn(
    "days_remaining",
    when(
        col("end_date").isNotNull() & (col("end_date") > current_date()),
        datediff(col("end_date"), current_date())
    ).otherwise(lit(0))
).withColumn(
    "daily_rate",
    when(
        col("days_elapsed") > 0,
        col("total_actual") / col("days_elapsed")
    ).otherwise(lit(0))
).withColumn(
    "projected_remaining",
    col("daily_rate") * col("days_remaining")
).withColumn(
    "projected_spend",
    col("total_actual") + col("projected_remaining")
).withColumn(
    "remaining_budget",
    coalesce(col("budget_total"), lit(0)) - col("total_actual")
).withColumn(
    "projected_variance",
    col("projected_spend") - coalesce(col("budget_total"), lit(0))
).withColumn(
    "confidence",
    when(col("days_elapsed") < 30, lit("low"))
    .when(col("days_elapsed") < 90, lit("medium"))
    .otherwise(lit("high"))
)

display(forecast_df.select(
    "project_id", "budget_total", "total_actual", "daily_rate",
    "projected_spend", "remaining_budget", "projected_variance", "confidence"
))

# COMMAND ----------

# Generate forecast records
records = []

for row in forecast_df.collect():
    records.append({
        "forecast_id": str(uuid.uuid4()),
        "project_id": row["project_id"],
        "forecast_date": today,
        "forecast_type": "run_rate",
        "remaining_budget": float(row["remaining_budget"] or 0),
        "projected_spend": float(row["projected_spend"] or 0),
        "projected_variance": float(row["projected_variance"] or 0),
        "confidence": row["confidence"] or "low"
    })

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DateType, DecimalType

schema = StructType([
    StructField("forecast_id", StringType(), False),
    StructField("project_id", StringType(), False),
    StructField("forecast_date", DateType(), False),
    StructField("forecast_type", StringType(), False),
    StructField("remaining_budget", DecimalType(18, 2), True),
    StructField("projected_spend", DecimalType(18, 2), True),
    StructField("projected_variance", DecimalType(18, 2), True),
    StructField("confidence", StringType(), True)
])

forecast_records_df = spark.createDataFrame(records, schema)
forecast_records_df = forecast_records_df.withColumn("computed_at", current_timestamp())

forecast_records_df.createOrReplaceTempView("forecast_updates")

spark.sql(f"""
MERGE INTO {catalog}.gold.ppm_forecast AS target
USING forecast_updates AS source
ON target.project_id = source.project_id
   AND target.forecast_date = source.forecast_date
   AND target.forecast_type = source.forecast_type
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

print("Forecast computation complete!")
