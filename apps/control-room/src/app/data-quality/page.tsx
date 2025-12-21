import { DQIssuesList } from '@/components/dq-issues-list';
import { getDataQualityIssues } from '@/lib/data';

export const revalidate = 60;

export default async function DataQualityPage() {
  const issues = await getDataQualityIssues();

  const passedCount = issues.filter(i => i.passed).length;
  const failedCount = issues.filter(i => !i.passed).length;
  const criticalCount = issues.filter(i => !i.passed && i.severity === 'critical').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Quality</h1>
        <p className="text-muted-foreground">
          Monitor data quality checks and resolve issues
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Checks</p>
          <p className="text-2xl font-bold">{issues.length}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Passed</p>
          <p className="text-2xl font-bold text-green-600">{passedCount}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Failed</p>
          <p className="text-2xl font-bold text-yellow-600">{failedCount}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Critical</p>
          <p className="text-2xl font-bold text-red-600">{criticalCount}</p>
        </div>
      </div>

      {/* Issues List */}
      <div className="rounded-lg border bg-card">
        <DQIssuesList issues={issues.filter(i => !i.passed)} />
      </div>
    </div>
  );
}
