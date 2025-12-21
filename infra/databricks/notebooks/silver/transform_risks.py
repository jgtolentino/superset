# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Risks - Bronze to Silver

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.notion_risks (
    risk_id STRING NOT NULL,
    project_id STRING NOT NULL,
    title STRING NOT NULL,
    description STRING,
    severity STRING,
    probability STRING,
    impact STRING,
    status STRING,
    mitigation STRING,
    owner STRING,
    due_date DATE,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    last_modified TIMESTAMP NOT NULL,
    synced_at TIMESTAMP NOT NULL,
    PRIMARY KEY (risk_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import col, get_json_object, to_date, coalesce, lit, element_at

bronze_df = spark.sql(f"SELECT * FROM {catalog}.bronze.notion_raw_pages WHERE database_name = 'risks'")

silver_df = bronze_df.select(
    col("page_id").alias("risk_id"),
    get_json_object(element_at(col("properties"), lit("Project")), "$.relation[0].id").alias("project_id"),
    coalesce(
        get_json_object(element_at(col("properties"), lit("Title")), "$.title[0].plain_text"),
        lit("Untitled Risk")
    ).alias("title"),
    get_json_object(element_at(col("properties"), lit("Description")), "$.rich_text[0].plain_text").alias("description"),
    get_json_object(element_at(col("properties"), lit("Severity")), "$.select.name").alias("severity"),
    get_json_object(element_at(col("properties"), lit("Probability")), "$.select.name").alias("probability"),
    get_json_object(element_at(col("properties"), lit("Impact")), "$.select.name").alias("impact"),
    get_json_object(element_at(col("properties"), lit("Status")), "$.select.name").alias("status"),
    get_json_object(element_at(col("properties"), lit("Mitigation")), "$.rich_text[0].plain_text").alias("mitigation"),
    get_json_object(element_at(col("properties"), lit("Owner")), "$.people[0].name").alias("owner"),
    to_date(get_json_object(element_at(col("properties"), lit("Due Date")), "$.date.start")).alias("due_date"),
    coalesce((get_json_object(col("raw_payload"), "$.archived") == "true"), lit(False)).alias("is_archived"),
    col("last_edited_time").alias("last_modified"),
    col("synced_at")
)

silver_df.createOrReplaceTempView("risks_updates")
spark.sql(f"""
MERGE INTO {catalog}.silver.notion_risks AS target
USING risks_updates AS source ON target.risk_id = source.risk_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print("Risks transformation complete!")
