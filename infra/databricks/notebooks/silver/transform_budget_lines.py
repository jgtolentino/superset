# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Budget Lines - Bronze to Silver

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

# Create budget_lines table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.silver.notion_budget_lines (
    budget_line_id STRING NOT NULL,
    project_id STRING NOT NULL,
    category STRING,
    subcategory STRING,
    vendor STRING,
    description STRING,
    amount DECIMAL(18, 2),
    currency STRING NOT NULL DEFAULT 'USD',
    committed_date DATE,
    invoice_date DATE,
    paid_date DATE,
    actual_amount DECIMAL(18, 2),
    notes STRING,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    last_modified TIMESTAMP NOT NULL,
    synced_at TIMESTAMP NOT NULL,
    PRIMARY KEY (budget_line_id)
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true'
)
""")

# COMMAND ----------

from pyspark.sql.functions import col, get_json_object, to_date, coalesce, lit, element_at

bronze_df = spark.sql(f"""
SELECT * FROM {catalog}.bronze.notion_raw_pages
WHERE database_name = 'budget_lines'
""")

silver_df = bronze_df.select(
    col("page_id").alias("budget_line_id"),
    get_json_object(element_at(col("properties"), lit("Project")), "$.relation[0].id").alias("project_id"),
    get_json_object(element_at(col("properties"), lit("Category")), "$.select.name").alias("category"),
    get_json_object(element_at(col("properties"), lit("Subcategory")), "$.select.name").alias("subcategory"),
    get_json_object(element_at(col("properties"), lit("Vendor")), "$.rich_text[0].plain_text").alias("vendor"),
    get_json_object(element_at(col("properties"), lit("Description")), "$.rich_text[0].plain_text").alias("description"),
    get_json_object(element_at(col("properties"), lit("Amount")), "$.number").cast("decimal(18,2)").alias("amount"),
    coalesce(
        get_json_object(element_at(col("properties"), lit("Currency")), "$.select.name"),
        lit("USD")
    ).alias("currency"),
    to_date(get_json_object(element_at(col("properties"), lit("Committed Date")), "$.date.start")).alias("committed_date"),
    to_date(get_json_object(element_at(col("properties"), lit("Invoice Date")), "$.date.start")).alias("invoice_date"),
    to_date(get_json_object(element_at(col("properties"), lit("Paid Date")), "$.date.start")).alias("paid_date"),
    get_json_object(element_at(col("properties"), lit("Actual Amount")), "$.number").cast("decimal(18,2)").alias("actual_amount"),
    get_json_object(element_at(col("properties"), lit("Notes")), "$.rich_text[0].plain_text").alias("notes"),
    (get_json_object(col("raw_payload"), "$.archived") == "true").alias("is_archived"),
    col("last_edited_time").alias("last_modified"),
    col("synced_at")
).withColumn("is_archived", coalesce(col("is_archived"), lit(False)))

silver_df.createOrReplaceTempView("budget_lines_updates")

spark.sql(f"""
MERGE INTO {catalog}.silver.notion_budget_lines AS target
USING budget_lines_updates AS source
ON target.budget_line_id = source.budget_line_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print("Budget lines transformation complete!")
