# Databricks notebook source
# MAGIC %md
# MAGIC # Control Room Status - Gold Layer
# MAGIC
# MAGIC Track Databricks job run status for the Control Room dashboard.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.control_room_status (
    job_id STRING NOT NULL,
    job_name STRING NOT NULL,
    job_type STRING,
    last_run_id STRING,
    last_run_status STRING,
    last_run_start TIMESTAMP,
    last_run_end TIMESTAMP,
    last_run_duration_seconds INT,
    next_scheduled_run TIMESTAMP,
    error_message STRING,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (job_id)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Databricks Jobs API

# COMMAND ----------

import requests
import json
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType
from pyspark.sql.functions import current_timestamp

# Get workspace URL and token
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
try:
    token = dbutils.secrets.get("ppm-secrets", "databricks-token")
except:
    # In development, try to use the notebook token
    token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# COMMAND ----------

# List all jobs
jobs_url = f"https://{workspace_url}/api/2.1/jobs/list"
response = requests.get(jobs_url, headers=headers)

if response.status_code != 200:
    print(f"Error listing jobs: {response.text}")
    dbutils.notebook.exit("FAILED: Could not list jobs")

jobs = response.json().get("jobs", [])
print(f"Found {len(jobs)} jobs")

# Filter to PPM jobs only
ppm_jobs = [j for j in jobs if "[PPM]" in j.get("settings", {}).get("name", "")]
print(f"Found {len(ppm_jobs)} PPM jobs")

# COMMAND ----------

# Get run history for each job
job_statuses = []

for job in ppm_jobs:
    job_id = str(job["job_id"])
    job_name = job["settings"]["name"]

    # Determine job type from name
    if "Sync" in job_name or "Ingest" in job_name:
        job_type = "ingestion"
    elif "Transform" in job_name:
        job_type = "transformation"
    elif "Gold" in job_name or "Compute" in job_name:
        job_type = "computation"
    else:
        job_type = "utility"

    # Get latest run
    runs_url = f"https://{workspace_url}/api/2.1/jobs/runs/list"
    runs_response = requests.get(
        runs_url,
        headers=headers,
        params={"job_id": job_id, "limit": 1}
    )

    last_run = None
    if runs_response.status_code == 200:
        runs = runs_response.json().get("runs", [])
        if runs:
            last_run = runs[0]

    # Extract run details
    status = {
        "job_id": job_id,
        "job_name": job_name,
        "job_type": job_type,
        "last_run_id": None,
        "last_run_status": None,
        "last_run_start": None,
        "last_run_end": None,
        "last_run_duration_seconds": None,
        "next_scheduled_run": None,
        "error_message": None
    }

    if last_run:
        status["last_run_id"] = str(last_run.get("run_id"))
        state = last_run.get("state", {})
        status["last_run_status"] = state.get("result_state") or state.get("life_cycle_state")

        start_time = last_run.get("start_time")
        end_time = last_run.get("end_time")

        if start_time:
            status["last_run_start"] = datetime.fromtimestamp(start_time / 1000)
        if end_time:
            status["last_run_end"] = datetime.fromtimestamp(end_time / 1000)

        if start_time and end_time:
            status["last_run_duration_seconds"] = int((end_time - start_time) / 1000)

        if status["last_run_status"] == "FAILED":
            status["error_message"] = state.get("state_message", "Unknown error")

    # Get next scheduled run
    schedule = job.get("settings", {}).get("schedule")
    if schedule and schedule.get("pause_status") == "UNPAUSED":
        # Simplified - just note it's scheduled
        status["next_scheduled_run"] = None  # Would need to calculate from cron

    job_statuses.append(status)

# COMMAND ----------

# Convert to DataFrame
schema = StructType([
    StructField("job_id", StringType(), False),
    StructField("job_name", StringType(), False),
    StructField("job_type", StringType(), True),
    StructField("last_run_id", StringType(), True),
    StructField("last_run_status", StringType(), True),
    StructField("last_run_start", TimestampType(), True),
    StructField("last_run_end", TimestampType(), True),
    StructField("last_run_duration_seconds", IntegerType(), True),
    StructField("next_scheduled_run", TimestampType(), True),
    StructField("error_message", StringType(), True)
])

status_df = spark.createDataFrame(job_statuses, schema)
status_df = status_df.withColumn("updated_at", current_timestamp())

display(status_df)

# COMMAND ----------

status_df.createOrReplaceTempView("status_updates")

spark.sql(f"""
MERGE INTO {catalog}.gold.control_room_status AS target
USING status_updates AS source
ON target.job_id = source.job_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# Show summary
display(spark.sql(f"""
SELECT
    last_run_status,
    COUNT(*) as job_count
FROM {catalog}.gold.control_room_status
GROUP BY last_run_status
"""))

print("Control room status refresh complete!")
