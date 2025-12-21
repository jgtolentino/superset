# Databricks notebook source
# MAGIC %md
# MAGIC # Azure Resource Graph Ingestion
# MAGIC
# MAGIC This notebook ingests Azure resources and Advisor recommendations
# MAGIC into the bronze layer using Azure Resource Graph API.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

print(f"Using catalog: {catalog}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Dependencies

# COMMAND ----------

# MAGIC %pip install azure-identity azure-mgmt-resourcegraph azure-mgmt-advisor

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Tables

# COMMAND ----------

# Create bronze table for Resource Graph data
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.bronze.azure_rg_raw (
    resource_id STRING NOT NULL,
    resource_type STRING,
    resource_group STRING,
    subscription_id STRING,
    location STRING,
    tags MAP<STRING, STRING>,
    properties STRING,
    advisor_recommendations STRING,
    ingested_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
""")

print("Created/verified bronze.azure_rg_raw table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Azure Authentication

# COMMAND ----------

import json
from datetime import datetime

# Get Azure credentials from secrets
try:
    tenant_id = dbutils.secrets.get("ppm-secrets", "azure-tenant-id")
    client_id = dbutils.secrets.get("ppm-secrets", "azure-client-id")
    client_secret = dbutils.secrets.get("ppm-secrets", "azure-client-secret")
    subscription_ids = dbutils.secrets.get("ppm-secrets", "azure-subscription-ids").split(",")

    print(f"Loaded credentials for {len(subscription_ids)} subscription(s)")
except Exception as e:
    print(f"Warning: Could not load Azure secrets: {e}")
    print("Skipping Azure ingestion - set secrets in 'ppm-secrets' scope")
    dbutils.notebook.exit("SKIPPED: Azure secrets not configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Resource Graph

# COMMAND ----------

from azure.identity import ClientSecretCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

# Authenticate
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

rg_client = ResourceGraphClient(credential)

# COMMAND ----------

# Resource Graph query for all resources with tags
RESOURCES_QUERY = """
Resources
| project
    id,
    type,
    resourceGroup,
    subscriptionId,
    location,
    tags,
    properties
| limit 10000
"""

# Query Azure Advisor recommendations
ADVISOR_QUERY = """
AdvisorResources
| where type == 'microsoft.advisor/recommendations'
| project
    id,
    name,
    resourceGroup,
    subscriptionId,
    properties
| limit 5000
"""

# COMMAND ----------

def query_resource_graph(query: str, subscriptions: list) -> list:
    """Execute a Resource Graph query across subscriptions."""
    request = QueryRequest(
        query=query,
        subscriptions=subscriptions
    )

    results = []
    response = rg_client.resources(request)
    results.extend(response.data)

    # Handle pagination
    while response.skip_token:
        request.options = {"$skipToken": response.skip_token}
        response = rg_client.resources(request)
        results.extend(response.data)

    return results

# COMMAND ----------

# Fetch resources
print("Fetching resources from Resource Graph...")
resources = query_resource_graph(RESOURCES_QUERY, subscription_ids)
print(f"Retrieved {len(resources)} resources")

# Fetch advisor recommendations
print("Fetching Advisor recommendations...")
advisor_recs = query_resource_graph(ADVISOR_QUERY, subscription_ids)
print(f"Retrieved {len(advisor_recs)} recommendations")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process and Write to Bronze

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, MapType, TimestampType
from pyspark.sql.functions import lit, current_timestamp

# Build recommendation lookup by resource
rec_by_resource = {}
for rec in advisor_recs:
    impacted_resource = rec.get("properties", {}).get("resourceMetadata", {}).get("resourceId", "")
    if impacted_resource:
        if impacted_resource not in rec_by_resource:
            rec_by_resource[impacted_resource] = []
        rec_by_resource[impacted_resource].append(rec)

# Prepare records for bronze table
records = []
for resource in resources:
    resource_id = resource.get("id", "")
    tags = resource.get("tags") or {}

    # Get recommendations for this resource
    recs = rec_by_resource.get(resource_id, [])

    records.append({
        "resource_id": resource_id,
        "resource_type": resource.get("type"),
        "resource_group": resource.get("resourceGroup"),
        "subscription_id": resource.get("subscriptionId"),
        "location": resource.get("location"),
        "tags": tags,
        "properties": json.dumps(resource.get("properties", {})),
        "advisor_recommendations": json.dumps(recs) if recs else None,
    })

print(f"Prepared {len(records)} records for ingestion")

# COMMAND ----------

# Convert to DataFrame
schema = StructType([
    StructField("resource_id", StringType(), False),
    StructField("resource_type", StringType(), True),
    StructField("resource_group", StringType(), True),
    StructField("subscription_id", StringType(), True),
    StructField("location", StringType(), True),
    StructField("tags", MapType(StringType(), StringType()), True),
    StructField("properties", StringType(), True),
    StructField("advisor_recommendations", StringType(), True),
])

df = spark.createDataFrame(records, schema)
df = df.withColumn("ingested_at", current_timestamp())

# COMMAND ----------

# Write with merge (upsert by resource_id)
df.createOrReplaceTempView("new_resources")

spark.sql(f"""
MERGE INTO {catalog}.bronze.azure_rg_raw AS target
USING new_resources AS source
ON target.resource_id = source.resource_id
WHEN MATCHED THEN UPDATE SET
    resource_type = source.resource_type,
    resource_group = source.resource_group,
    subscription_id = source.subscription_id,
    location = source.location,
    tags = source.tags,
    properties = source.properties,
    advisor_recommendations = source.advisor_recommendations,
    ingested_at = source.ingested_at
WHEN NOT MATCHED THEN INSERT *
""")

print(f"Merged {len(records)} resources to bronze.azure_rg_raw")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Show summary stats
display(spark.sql(f"""
SELECT
    resource_type,
    COUNT(*) as count,
    COUNT(advisor_recommendations) as with_recommendations
FROM {catalog}.bronze.azure_rg_raw
GROUP BY resource_type
ORDER BY count DESC
LIMIT 20
"""))

# COMMAND ----------

print("Azure Resource Graph ingestion complete!")
