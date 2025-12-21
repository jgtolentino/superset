# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Actions - Bronze to Silver

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.notion_actions (
    action_id STRING NOT NULL,
    project_id STRING,
    title STRING NOT NULL,
    description STRING,
    assignee STRING,
    due_date DATE,
    status STRING,
    source STRING,
    source_id STRING,
    priority STRING,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    last_modified TIMESTAMP NOT NULL,
    synced_at TIMESTAMP NOT NULL,
    PRIMARY KEY (action_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import col, get_json_object, to_date, coalesce, lit, element_at

bronze_df = spark.sql(f"SELECT * FROM {catalog}.bronze.notion_raw_pages WHERE database_name = 'actions'")

silver_df = bronze_df.select(
    col("page_id").alias("action_id"),
    get_json_object(element_at(col("properties"), lit("Project")), "$.relation[0].id").alias("project_id"),
    coalesce(
        get_json_object(element_at(col("properties"), lit("Title")), "$.title[0].plain_text"),
        lit("Untitled Action")
    ).alias("title"),
    get_json_object(element_at(col("properties"), lit("Description")), "$.rich_text[0].plain_text").alias("description"),
    get_json_object(element_at(col("properties"), lit("Assignee")), "$.people[0].name").alias("assignee"),
    to_date(get_json_object(element_at(col("properties"), lit("Due Date")), "$.date.start")).alias("due_date"),
    get_json_object(element_at(col("properties"), lit("Status")), "$.select.name").alias("status"),
    get_json_object(element_at(col("properties"), lit("Source")), "$.select.name").alias("source"),
    get_json_object(element_at(col("properties"), lit("Source ID")), "$.rich_text[0].plain_text").alias("source_id"),
    get_json_object(element_at(col("properties"), lit("Priority")), "$.select.name").alias("priority"),
    coalesce((get_json_object(col("raw_payload"), "$.archived") == "true"), lit(False)).alias("is_archived"),
    col("last_edited_time").alias("last_modified"),
    col("synced_at")
)

silver_df.createOrReplaceTempView("actions_updates")
spark.sql(f"""
MERGE INTO {catalog}.silver.notion_actions AS target
USING actions_updates AS source ON target.action_id = source.action_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print("Actions transformation complete!")
