# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Programs - Bronze to Silver
# MAGIC
# MAGIC Normalize Notion Programs data from bronze to silver layer.

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

# Create silver schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.silver")

# Create programs table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.notion_programs (
    program_id STRING NOT NULL,
    name STRING NOT NULL,
    owner STRING,
    start_date DATE,
    end_date DATE,
    status STRING,
    description STRING,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    last_modified TIMESTAMP NOT NULL,
    synced_at TIMESTAMP NOT NULL,
    PRIMARY KEY (program_id)
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

print("Created/verified silver.notion_programs table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform Data

# COMMAND ----------

from pyspark.sql.functions import (
    col, from_json, get_json_object, to_date, to_timestamp,
    coalesce, lit, when, current_timestamp
)
from pyspark.sql.types import StringType

# Read bronze data for programs
bronze_df = spark.sql(f"""
SELECT
    page_id,
    database_id,
    last_edited_time,
    properties,
    raw_payload,
    synced_at
FROM {catalog}.bronze.notion_raw_pages
WHERE database_name = 'programs'
""")

print(f"Found {bronze_df.count()} program records in bronze")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Extract Properties from JSON

# COMMAND ----------

# Helper function to extract property values from Notion format
def extract_property_value(df, prop_name, target_col, prop_type="title"):
    """Extract a property value from the properties map."""

    if prop_type == "title":
        # Title type: properties[prop_name][title][0][plain_text]
        return df.withColumn(
            target_col,
            get_json_object(
                col(f"properties.{prop_name}"),
                "$.title[0].plain_text"
            )
        )
    elif prop_type == "rich_text":
        return df.withColumn(
            target_col,
            get_json_object(
                col(f"properties.{prop_name}"),
                "$.rich_text[0].plain_text"
            )
        )
    elif prop_type == "select":
        return df.withColumn(
            target_col,
            get_json_object(
                col(f"properties.{prop_name}"),
                "$.select.name"
            )
        )
    elif prop_type == "date":
        return df.withColumn(
            target_col,
            to_date(get_json_object(
                col(f"properties.{prop_name}"),
                "$.date.start"
            ))
        )
    elif prop_type == "people":
        # Get first person's name
        return df.withColumn(
            target_col,
            get_json_object(
                col(f"properties.{prop_name}"),
                "$.people[0].name"
            )
        )
    else:
        return df

# COMMAND ----------

# Note: Since properties is stored as MAP<STRING, STRING>,
# we need to access it differently

# Transform programs
silver_df = bronze_df.selectExpr(
    "page_id as program_id",
    "last_edited_time as last_modified",
    "synced_at",
    # Check if page is archived from raw_payload
    "get_json_object(raw_payload, '$.archived') = 'true' as is_archived"
)

# For properties stored as MAP<STRING, STRING>, each value is a JSON string
# We need to parse them
from pyspark.sql.functions import element_at

silver_df = bronze_df.select(
    col("page_id").alias("program_id"),
    # Extract Name (title type)
    get_json_object(element_at(col("properties"), lit("Name")), "$.title[0].plain_text").alias("name"),
    # Extract Owner (people type)
    get_json_object(element_at(col("properties"), lit("Owner")), "$.people[0].name").alias("owner"),
    # Extract dates
    to_date(get_json_object(element_at(col("properties"), lit("Start Date")), "$.date.start")).alias("start_date"),
    to_date(get_json_object(element_at(col("properties"), lit("End Date")), "$.date.start")).alias("end_date"),
    # Extract status
    get_json_object(element_at(col("properties"), lit("Status")), "$.select.name").alias("status"),
    # Extract description
    get_json_object(element_at(col("properties"), lit("Description")), "$.rich_text[0].plain_text").alias("description"),
    # Is archived
    (get_json_object(col("raw_payload"), "$.archived") == "true").alias("is_archived"),
    # Timestamps
    col("last_edited_time").alias("last_modified"),
    col("synced_at")
)

# Handle nulls for name
silver_df = silver_df.withColumn(
    "name",
    coalesce(col("name"), lit("Untitled Program"))
)

# Ensure is_archived is not null
silver_df = silver_df.withColumn(
    "is_archived",
    coalesce(col("is_archived"), lit(False))
)

display(silver_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Merge to Silver Table

# COMMAND ----------

# Create temp view for merge
silver_df.createOrReplaceTempView("programs_updates")

# Merge
result = spark.sql(f"""
MERGE INTO {catalog}.silver.notion_programs AS target
USING programs_updates AS source
ON target.program_id = source.program_id
WHEN MATCHED THEN UPDATE SET
    name = source.name,
    owner = source.owner,
    start_date = source.start_date,
    end_date = source.end_date,
    status = source.status,
    description = source.description,
    is_archived = source.is_archived,
    last_modified = source.last_modified,
    synced_at = source.synced_at
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Show row counts
active_count = spark.sql(f"""
SELECT COUNT(*) as count
FROM {catalog}.silver.notion_programs
WHERE is_archived = false
""").collect()[0]["count"]

archived_count = spark.sql(f"""
SELECT COUNT(*) as count
FROM {catalog}.silver.notion_programs
WHERE is_archived = true
""").collect()[0]["count"]

print(f"Active programs: {active_count}")
print(f"Archived programs: {archived_count}")

# COMMAND ----------

# Show sample data
display(spark.sql(f"""
SELECT * FROM {catalog}.silver.notion_programs
WHERE is_archived = false
ORDER BY last_modified DESC
LIMIT 10
"""))

# COMMAND ----------

print("Programs transformation complete!")
