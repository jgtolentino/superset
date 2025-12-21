/**
 * Data fetching functions for Control Room.
 *
 * In production, these query Databricks SQL directly.
 * In development, they return mock data if MOCK_DATA=true.
 */

import { DatabricksClient } from './databricks';

// Types
export interface KPI {
  metric_id: string;
  metric_name: string;
  dimension: string;
  dimension_value: string;
  period: string;
  value: number;
  unit: string;
}

export interface JobStatus {
  job_id: string;
  job_name: string;
  job_type?: string;
  last_run_status?: string | null;
  last_run_start?: string | null;
  last_run_end?: string | null;
  last_run_duration_seconds?: number | null;
  error_message?: string | null;
}

export interface DQIssue {
  metric_id: string;
  table_name: string;
  check_type: string;
  column_name?: string | null;
  expected_value?: string | null;
  actual_value?: string | null;
  severity: string;
  check_date: string;
  passed: boolean;
}

export interface AdvisorRec {
  category: string;
  recommendation_count: number;
  total_estimated_savings: number;
  high_impact_count: number;
}

export interface Project {
  project_id: string;
  name: string;
  program_id?: string;
  status?: string;
  priority?: string;
  owner?: string;
  budget_total?: number;
  currency?: string;
}

// Mock data for development
const MOCK_KPIS: KPI[] = [
  { metric_id: '1', metric_name: 'budget', dimension: 'portfolio', dimension_value: 'total', period: '2024-01-01', value: 5000000, unit: 'USD' },
  { metric_id: '2', metric_name: 'actual', dimension: 'portfolio', dimension_value: 'total', period: '2024-01-01', value: 4200000, unit: 'USD' },
  { metric_id: '3', metric_name: 'variance', dimension: 'portfolio', dimension_value: 'total', period: '2024-01-01', value: -800000, unit: 'USD' },
  { metric_id: '4', metric_name: 'budget', dimension: 'project', dimension_value: 'p1', period: '2024-01-01', value: 1000000, unit: 'USD' },
  { metric_id: '5', metric_name: 'actual', dimension: 'project', dimension_value: 'p1', period: '2024-01-01', value: 850000, unit: 'USD' },
  { metric_id: '6', metric_name: 'burn_rate', dimension: 'project', dimension_value: 'p1', period: '2024-01-01', value: 85, unit: 'percent' },
  { metric_id: '7', metric_name: 'burn_rate', dimension: 'project', dimension_value: 'p2', period: '2024-01-01', value: 110, unit: 'percent' },
];

const MOCK_JOBS: JobStatus[] = [
  { job_id: '1', job_name: '[PPM] Notion Sync Bronze', job_type: 'ingestion', last_run_status: 'SUCCESS', last_run_end: new Date().toISOString(), last_run_duration_seconds: 45 },
  { job_id: '2', job_name: '[PPM] Transform Silver', job_type: 'transformation', last_run_status: 'SUCCESS', last_run_end: new Date().toISOString(), last_run_duration_seconds: 120 },
  { job_id: '3', job_name: '[PPM] Compute Gold Marts', job_type: 'computation', last_run_status: 'FAILED', last_run_end: new Date().toISOString(), last_run_duration_seconds: 60, error_message: 'Out of memory' },
  { job_id: '4', job_name: '[PPM] Azure Advisor Transform', job_type: 'transformation', last_run_status: 'SUCCESS', last_run_end: new Date().toISOString(), last_run_duration_seconds: 30 },
];

const MOCK_DQ_ISSUES: DQIssue[] = [
  { metric_id: '1', table_name: 'silver.notion_projects', check_type: 'null_rate', column_name: 'owner', expected_value: '<= 10%', actual_value: '15%', severity: 'warning', check_date: new Date().toISOString().split('T')[0], passed: false },
  { metric_id: '2', table_name: 'silver.notion_budget_lines', check_type: 'referential_integrity', column_name: 'project_id', expected_value: '0 orphans', actual_value: '3 orphans', severity: 'critical', check_date: new Date().toISOString().split('T')[0], passed: false },
  { metric_id: '3', table_name: 'bronze.notion_raw_pages', check_type: 'freshness', column_name: null, expected_value: '< 24 hours', actual_value: '2 hours', severity: 'info', check_date: new Date().toISOString().split('T')[0], passed: true },
];

const MOCK_ADVISOR: AdvisorRec[] = [
  { category: 'Cost', recommendation_count: 12, total_estimated_savings: 15000, high_impact_count: 3 },
  { category: 'Security', recommendation_count: 5, total_estimated_savings: 0, high_impact_count: 2 },
  { category: 'Reliability', recommendation_count: 8, total_estimated_savings: 0, high_impact_count: 1 },
];

const MOCK_PROJECTS: Project[] = [
  { project_id: 'p1', name: 'Cloud Migration', status: 'active', priority: 'high', owner: 'Alice', budget_total: 1000000 },
  { project_id: 'p2', name: 'Data Platform', status: 'active', priority: 'high', owner: 'Bob', budget_total: 2000000 },
  { project_id: 'p3', name: 'Mobile App', status: 'on_hold', priority: 'medium', owner: 'Carol', budget_total: 500000 },
];

// Data fetching functions
export async function getKPIs(): Promise<KPI[]> {
  if (process.env.MOCK_DATA === 'true') {
    return MOCK_KPIS;
  }

  const client = new DatabricksClient();
  const catalog = process.env.DATABRICKS_CATALOG || 'main';

  try {
    const result = await client.query<KPI>(`
      SELECT
        metric_id,
        metric_name,
        dimension,
        dimension_value,
        CAST(period AS STRING) as period,
        CAST(value AS DOUBLE) as value,
        unit
      FROM ${catalog}.gold.ppm_budget_vs_actual
      ORDER BY period DESC, dimension, metric_name
      LIMIT 1000
    `);
    return result;
  } catch (error) {
    console.error('Failed to fetch KPIs:', error);
    return MOCK_KPIS;
  }
}

export async function getJobStatus(): Promise<JobStatus[]> {
  if (process.env.MOCK_DATA === 'true') {
    return MOCK_JOBS;
  }

  const client = new DatabricksClient();
  const catalog = process.env.DATABRICKS_CATALOG || 'main';

  try {
    const result = await client.query<JobStatus>(`
      SELECT
        job_id,
        job_name,
        job_type,
        last_run_status,
        CAST(last_run_start AS STRING) as last_run_start,
        CAST(last_run_end AS STRING) as last_run_end,
        last_run_duration_seconds,
        error_message
      FROM ${catalog}.gold.control_room_status
      ORDER BY job_name
    `);
    return result;
  } catch (error) {
    console.error('Failed to fetch job status:', error);
    return MOCK_JOBS;
  }
}

export async function getDataQualityIssues(): Promise<DQIssue[]> {
  if (process.env.MOCK_DATA === 'true') {
    return MOCK_DQ_ISSUES;
  }

  const client = new DatabricksClient();
  const catalog = process.env.DATABRICKS_CATALOG || 'main';

  try {
    const result = await client.query<DQIssue>(`
      SELECT
        metric_id,
        table_name,
        check_type,
        column_name,
        expected_value,
        actual_value,
        severity,
        CAST(check_date AS STRING) as check_date,
        passed
      FROM ${catalog}.gold.data_quality_metrics
      WHERE check_date >= current_date() - INTERVAL 7 DAYS
      ORDER BY passed, severity, check_date DESC
    `);
    return result;
  } catch (error) {
    console.error('Failed to fetch DQ issues:', error);
    return MOCK_DQ_ISSUES;
  }
}

export async function getAdvisorRecommendations(): Promise<AdvisorRec[]> {
  if (process.env.MOCK_DATA === 'true') {
    return MOCK_ADVISOR;
  }

  const client = new DatabricksClient();
  const catalog = process.env.DATABRICKS_CATALOG || 'main';

  try {
    const result = await client.query<AdvisorRec>(`
      SELECT
        category,
        recommendation_count,
        CAST(total_estimated_savings AS DOUBLE) as total_estimated_savings,
        high_impact_count
      FROM ${catalog}.gold.azure_advisor_summary
      WHERE summary_date = (SELECT MAX(summary_date) FROM ${catalog}.gold.azure_advisor_summary)
    `);
    return result;
  } catch (error) {
    console.error('Failed to fetch advisor recommendations:', error);
    return MOCK_ADVISOR;
  }
}

export async function getProjects(): Promise<Project[]> {
  if (process.env.MOCK_DATA === 'true') {
    return MOCK_PROJECTS;
  }

  const client = new DatabricksClient();
  const catalog = process.env.DATABRICKS_CATALOG || 'main';

  try {
    const result = await client.query<Project>(`
      SELECT
        project_id,
        name,
        program_id,
        status,
        priority,
        owner,
        CAST(budget_total AS DOUBLE) as budget_total,
        currency
      FROM ${catalog}.silver.notion_projects
      WHERE is_archived = false
      ORDER BY name
    `);
    return result;
  } catch (error) {
    console.error('Failed to fetch projects:', error);
    return MOCK_PROJECTS;
  }
}
