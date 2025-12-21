# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Azure Advisor - Bronze to Silver

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.azure_advisor_recommendations (
    recommendation_id STRING NOT NULL,
    resource_id STRING NOT NULL,
    category STRING NOT NULL,
    impact STRING,
    impacted_field STRING,
    impacted_value STRING,
    short_description STRING,
    extended_properties STRING,
    estimated_savings DECIMAL(18, 2),
    ingested_at TIMESTAMP NOT NULL,
    PRIMARY KEY (recommendation_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import col, explode, from_json, get_json_object, coalesce, lit, current_timestamp
from pyspark.sql.types import ArrayType, StructType, StructField, StringType

# Read bronze data with recommendations
bronze_df = spark.sql(f"""
SELECT
    resource_id,
    advisor_recommendations,
    ingested_at
FROM {catalog}.bronze.azure_rg_raw
WHERE advisor_recommendations IS NOT NULL
""")

# Parse recommendations array
rec_schema = ArrayType(StructType([
    StructField("id", StringType(), True),
    StructField("properties", StringType(), True)
]))

# Explode recommendations
exploded_df = bronze_df.select(
    col("resource_id"),
    col("ingested_at"),
    explode(from_json(col("advisor_recommendations"), rec_schema)).alias("rec")
)

# Extract recommendation fields
silver_df = exploded_df.select(
    col("rec.id").alias("recommendation_id"),
    col("resource_id"),
    get_json_object(col("rec.properties"), "$.category").alias("category"),
    get_json_object(col("rec.properties"), "$.impact").alias("impact"),
    get_json_object(col("rec.properties"), "$.impactedField").alias("impacted_field"),
    get_json_object(col("rec.properties"), "$.impactedValue").alias("impacted_value"),
    get_json_object(col("rec.properties"), "$.shortDescription.solution").alias("short_description"),
    get_json_object(col("rec.properties"), "$.extendedProperties").alias("extended_properties"),
    # Try to extract savings from extendedProperties
    get_json_object(
        col("rec.properties"),
        "$.extendedProperties.annualSavingsAmount"
    ).cast("decimal(18,2)").alias("estimated_savings"),
    col("ingested_at")
).filter(col("recommendation_id").isNotNull())

# Handle nulls
silver_df = silver_df.withColumn(
    "category",
    coalesce(col("category"), lit("Unknown"))
)

silver_df.createOrReplaceTempView("advisor_updates")

spark.sql(f"""
MERGE INTO {catalog}.silver.azure_advisor_recommendations AS target
USING advisor_updates AS source
ON target.recommendation_id = source.recommendation_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

display(spark.sql(f"""
SELECT category, COUNT(*) as count, SUM(estimated_savings) as total_savings
FROM {catalog}.silver.azure_advisor_recommendations
GROUP BY category
"""))

print("Advisor transformation complete!")
