import { KPICard } from '@/components/kpi-card';
import { HealthSummary } from '@/components/health-summary';
import { RecentAlerts } from '@/components/recent-alerts';
import { getKPIs, getJobStatus, getDataQualityIssues } from '@/lib/data';

export const revalidate = 60; // Revalidate every 60 seconds

export default async function OverviewPage() {
  const [kpis, jobStatus, dqIssues] = await Promise.all([
    getKPIs(),
    getJobStatus(),
    getDataQualityIssues(),
  ]);

  // Calculate summary metrics
  const totalBudget = kpis.find(k => k.metric_name === 'budget' && k.dimension === 'portfolio')?.value || 0;
  const totalActual = kpis.find(k => k.metric_name === 'actual' && k.dimension === 'portfolio')?.value || 0;
  const totalVariance = kpis.find(k => k.metric_name === 'variance' && k.dimension === 'portfolio')?.value || 0;

  const projectBudgets = kpis.filter(k => k.metric_name === 'budget' && k.dimension === 'project');
  const atRiskProjects = kpis.filter(
    k => k.metric_name === 'burn_rate' && k.dimension === 'project' && k.value > 100
  ).length;

  const failingJobs = jobStatus.filter(j => j.last_run_status === 'FAILED').length;
  const lastSuccessfulRun = jobStatus
    .filter(j => j.last_run_status === 'SUCCESS')
    .sort((a, b) => new Date(b.last_run_end || 0).getTime() - new Date(a.last_run_end || 0).getTime())[0];

  const criticalIssues = dqIssues.filter(i => i.severity === 'critical' && !i.passed);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-muted-foreground">
          Portfolio health and key metrics at a glance
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Budget"
          value={totalBudget}
          unit="USD"
          format="currency"
        />
        <KPICard
          title="Actuals YTD"
          value={totalActual}
          unit="USD"
          format="currency"
        />
        <KPICard
          title="Variance"
          value={totalVariance}
          unit="USD"
          format="currency"
          status={totalVariance > 0 ? 'error' : 'success'}
        />
        <KPICard
          title="At-Risk Projects"
          value={atRiskProjects}
          unit="projects"
          status={atRiskProjects > 0 ? 'warning' : 'success'}
        />
      </div>

      {/* Health Summary */}
      <div className="grid gap-4 md:grid-cols-2">
        <HealthSummary
          lastSuccessfulRun={lastSuccessfulRun?.last_run_end}
          failingJobsCount={failingJobs}
          criticalIssuesCount={criticalIssues.length}
          totalJobs={jobStatus.length}
        />
        <RecentAlerts
          alerts={[
            ...criticalIssues.slice(0, 3).map(i => ({
              type: 'dq' as const,
              message: `${i.check_type} check failed on ${i.table_name}`,
              severity: i.severity,
              timestamp: i.check_date,
            })),
            ...jobStatus
              .filter(j => j.last_run_status === 'FAILED')
              .slice(0, 2)
              .map(j => ({
                type: 'job' as const,
                message: `Job "${j.job_name}" failed`,
                severity: 'critical' as const,
                timestamp: j.last_run_end,
              })),
          ]}
        />
      </div>
    </div>
  );
}
