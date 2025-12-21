# Databricks notebook source
# MAGIC %md
# MAGIC # Project Health - Gold Layer
# MAGIC
# MAGIC Compute health scores for each project based on budget, schedule, and risks.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.gold.ppm_project_health (
    project_id STRING NOT NULL,
    health_date DATE NOT NULL,
    overall_score DECIMAL(5, 2),
    budget_score DECIMAL(5, 2),
    schedule_score DECIMAL(5, 2),
    risk_score DECIMAL(5, 2),
    status STRING,
    risk_count INT,
    open_actions INT,
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (project_id, health_date)
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""")

# COMMAND ----------

from pyspark.sql.functions import (
    col, lit, count, sum as spark_sum, when, coalesce,
    current_date, current_timestamp, greatest, least
)
from datetime import date

today = date.today()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculate Budget Score

# COMMAND ----------

# Budget score: 100 if under budget, 0 if 50%+ over
budget_df = spark.sql(f"""
SELECT
    p.project_id,
    p.budget_total,
    COALESCE(SUM(bl.actual_amount), 0) as total_actual
FROM {catalog}.silver.notion_projects p
LEFT JOIN {catalog}.silver.notion_budget_lines bl
    ON p.project_id = bl.project_id
    AND bl.is_archived = false
    AND bl.paid_date IS NOT NULL
WHERE p.is_archived = false
GROUP BY p.project_id, p.budget_total
""")

budget_scores = budget_df.withColumn(
    "budget_score",
    when(
        col("budget_total").isNull() | (col("budget_total") == 0),
        lit(100.0)  # No budget = healthy
    ).when(
        col("total_actual") <= col("budget_total"),
        lit(100.0)  # Under budget
    ).when(
        col("total_actual") >= col("budget_total") * 1.5,
        lit(0.0)  # 50%+ over budget
    ).otherwise(
        # Linear scale between 100 and 0
        100.0 - ((col("total_actual") - col("budget_total")) / (col("budget_total") * 0.5) * 100)
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculate Schedule Score

# COMMAND ----------

# Schedule score: 100 if on time, decreases as end date passes
schedule_df = spark.sql(f"""
SELECT
    project_id,
    start_date,
    end_date,
    status
FROM {catalog}.silver.notion_projects
WHERE is_archived = false
""")

schedule_scores = schedule_df.withColumn(
    "schedule_score",
    when(
        col("status") == "completed",
        lit(100.0)
    ).when(
        col("end_date").isNull(),
        lit(80.0)  # No end date = slightly risky
    ).when(
        col("end_date") >= current_date(),
        lit(100.0)  # Not yet due
    ).when(
        col("end_date") < current_date(),
        # Decrease 10 points per week overdue, min 0
        greatest(lit(0.0), 100.0 - (datediff(current_date(), col("end_date")) / 7 * 10))
    ).otherwise(lit(100.0))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculate Risk Score

# COMMAND ----------

# Risk score: Based on count and severity of open risks
risk_df = spark.sql(f"""
SELECT
    project_id,
    COUNT(*) as risk_count,
    SUM(CASE WHEN severity = 'critical' THEN 4
             WHEN severity = 'high' THEN 3
             WHEN severity = 'medium' THEN 2
             WHEN severity = 'low' THEN 1
             ELSE 1 END) as risk_weight
FROM {catalog}.silver.notion_risks
WHERE is_archived = false
  AND status IN ('open', 'identified')
GROUP BY project_id
""")

# Projects with risks
risk_scores = risk_df.withColumn(
    "risk_score",
    # Max risk weight of 20 = score of 0
    greatest(lit(0.0), 100.0 - (col("risk_weight") * 5))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Count Open Actions

# COMMAND ----------

actions_df = spark.sql(f"""
SELECT
    project_id,
    COUNT(*) as open_actions
FROM {catalog}.silver.notion_actions
WHERE is_archived = false
  AND status IN ('todo', 'in_progress')
GROUP BY project_id
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Combine Scores

# COMMAND ----------

from pyspark.sql.functions import datediff

# Get all projects
all_projects = spark.sql(f"""
SELECT project_id FROM {catalog}.silver.notion_projects WHERE is_archived = false
""")

# Join all scores
health_df = all_projects \
    .join(budget_scores.select("project_id", "budget_score"), "project_id", "left") \
    .join(schedule_scores.select("project_id", "schedule_score"), "project_id", "left") \
    .join(risk_scores.select("project_id", "risk_score", "risk_count"), "project_id", "left") \
    .join(actions_df, "project_id", "left")

# Fill nulls and calculate overall score
health_df = health_df.fillna({
    "budget_score": 100.0,
    "schedule_score": 100.0,
    "risk_score": 100.0,
    "risk_count": 0,
    "open_actions": 0
})

# Overall score is weighted average
health_df = health_df.withColumn(
    "overall_score",
    (col("budget_score") * 0.4 + col("schedule_score") * 0.3 + col("risk_score") * 0.3)
)

# Determine status
health_df = health_df.withColumn(
    "status",
    when(col("overall_score") >= 80, lit("healthy"))
    .when(col("overall_score") >= 50, lit("at_risk"))
    .otherwise(lit("critical"))
)

# Add date and timestamp
health_df = health_df.withColumn("health_date", lit(today)) \
    .withColumn("computed_at", current_timestamp())

display(health_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Gold Table

# COMMAND ----------

health_df.createOrReplaceTempView("health_updates")

spark.sql(f"""
MERGE INTO {catalog}.gold.ppm_project_health AS target
USING health_updates AS source
ON target.project_id = source.project_id
   AND target.health_date = source.health_date
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

# COMMAND ----------

# Show summary
display(spark.sql(f"""
SELECT
    status,
    COUNT(*) as project_count,
    AVG(overall_score) as avg_score
FROM {catalog}.gold.ppm_project_health
WHERE health_date = '{today}'
GROUP BY status
"""))

print("Project health computation complete!")
