# Databricks notebook source
# MAGIC %md
# MAGIC # Azure Advisor Summary - Gold Layer

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.azure_advisor_summary (
    summary_date DATE NOT NULL,
    category STRING NOT NULL,
    recommendation_count INT,
    impacted_resources INT,
    total_estimated_savings DECIMAL(18, 2),
    high_impact_count INT,
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (summary_date, category)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import col, lit, count, countDistinct, sum as spark_sum, when, current_date, current_timestamp
from datetime import date

today = date.today()

# Aggregate recommendations by category
summary_df = spark.sql(f"""
SELECT
    category,
    COUNT(*) as recommendation_count,
    COUNT(DISTINCT resource_id) as impacted_resources,
    SUM(COALESCE(estimated_savings, 0)) as total_estimated_savings,
    SUM(CASE WHEN impact = 'High' THEN 1 ELSE 0 END) as high_impact_count
FROM {catalog}.silver.azure_advisor_recommendations
GROUP BY category
""")

summary_df = summary_df.withColumn("summary_date", lit(today)) \
    .withColumn("computed_at", current_timestamp())

display(summary_df)

# COMMAND ----------

summary_df.createOrReplaceTempView("summary_updates")

spark.sql(f"""
MERGE INTO {catalog}.gold.azure_advisor_summary AS target
USING summary_updates AS source
ON target.summary_date = source.summary_date
   AND target.category = source.category
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print("Advisor summary complete!")
