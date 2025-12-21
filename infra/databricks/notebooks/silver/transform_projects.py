# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Projects - Bronze to Silver
# MAGIC
# MAGIC Normalize Notion Projects data from bronze to silver layer.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

print(f"Using catalog: {catalog}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Silver Table

# COMMAND ----------

# Create projects table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.notion_projects (
    project_id STRING NOT NULL,
    program_id STRING,
    name STRING NOT NULL,
    budget_total DECIMAL(18, 2),
    currency STRING NOT NULL DEFAULT 'USD',
    start_date DATE,
    end_date DATE,
    status STRING,
    priority STRING,
    owner STRING,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    last_modified TIMESTAMP NOT NULL,
    synced_at TIMESTAMP NOT NULL,
    PRIMARY KEY (project_id)
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

print("Created/verified silver.notion_projects table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Data

# COMMAND ----------

from pyspark.sql.functions import (
    col, get_json_object, to_date, coalesce, lit, element_at,
    regexp_extract, when, current_timestamp
)

# Read bronze data for projects
bronze_df = spark.sql(f"""
SELECT
    page_id,
    database_id,
    last_edited_time,
    properties,
    raw_payload,
    synced_at
FROM {catalog}.bronze.notion_raw_pages
WHERE database_name = 'projects'
""")

print(f"Found {bronze_df.count()} project records in bronze")

# COMMAND ----------

# Transform projects
silver_df = bronze_df.select(
    col("page_id").alias("project_id"),
    # Extract Program relation (first related page ID)
    get_json_object(element_at(col("properties"), lit("Program")), "$.relation[0].id").alias("program_id"),
    # Extract Name
    get_json_object(element_at(col("properties"), lit("Name")), "$.title[0].plain_text").alias("name"),
    # Extract Budget Total
    get_json_object(element_at(col("properties"), lit("Budget Total")), "$.number").cast("decimal(18,2)").alias("budget_total"),
    # Extract Currency (select type)
    coalesce(
        get_json_object(element_at(col("properties"), lit("Currency")), "$.select.name"),
        lit("USD")
    ).alias("currency"),
    # Extract dates
    to_date(get_json_object(element_at(col("properties"), lit("Start Date")), "$.date.start")).alias("start_date"),
    to_date(get_json_object(element_at(col("properties"), lit("End Date")), "$.date.start")).alias("end_date"),
    # Extract status and priority
    get_json_object(element_at(col("properties"), lit("Status")), "$.select.name").alias("status"),
    get_json_object(element_at(col("properties"), lit("Priority")), "$.select.name").alias("priority"),
    # Extract Owner
    get_json_object(element_at(col("properties"), lit("Owner")), "$.people[0].name").alias("owner"),
    # Is archived
    (get_json_object(col("raw_payload"), "$.archived") == "true").alias("is_archived"),
    # Timestamps
    col("last_edited_time").alias("last_modified"),
    col("synced_at")
)

# Handle nulls
silver_df = silver_df.withColumn(
    "name",
    coalesce(col("name"), lit("Untitled Project"))
).withColumn(
    "is_archived",
    coalesce(col("is_archived"), lit(False))
)

display(silver_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Merge to Silver Table

# COMMAND ----------

silver_df.createOrReplaceTempView("projects_updates")

spark.sql(f"""
MERGE INTO {catalog}.silver.notion_projects AS target
USING projects_updates AS source
ON target.project_id = source.project_id
WHEN MATCHED THEN UPDATE SET
    program_id = source.program_id,
    name = source.name,
    budget_total = source.budget_total,
    currency = source.currency,
    start_date = source.start_date,
    end_date = source.end_date,
    status = source.status,
    priority = source.priority,
    owner = source.owner,
    is_archived = source.is_archived,
    last_modified = source.last_modified,
    synced_at = source.synced_at
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Show summary by status
display(spark.sql(f"""
SELECT
    status,
    COUNT(*) as project_count,
    SUM(budget_total) as total_budget
FROM {catalog}.silver.notion_projects
WHERE is_archived = false
GROUP BY status
ORDER BY project_count DESC
"""))

# COMMAND ----------

print("Projects transformation complete!")
