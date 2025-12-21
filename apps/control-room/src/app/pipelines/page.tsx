import { JobStatusTable } from '@/components/job-status-table';
import { getJobStatus } from '@/lib/data';

export const revalidate = 30;

export default async function PipelinesPage() {
  const jobs = await getJobStatus();

  const successCount = jobs.filter(j => j.last_run_status === 'SUCCESS').length;
  const failedCount = jobs.filter(j => j.last_run_status === 'FAILED').length;
  const runningCount = jobs.filter(j => j.last_run_status === 'RUNNING').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Pipelines</h1>
        <p className="text-muted-foreground">
          Monitor Databricks job status and run history
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Jobs</p>
          <p className="text-2xl font-bold">{jobs.length}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Successful</p>
          <p className="text-2xl font-bold text-green-600">{successCount}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Failed</p>
          <p className="text-2xl font-bold text-red-600">{failedCount}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Running</p>
          <p className="text-2xl font-bold text-blue-600">{runningCount}</p>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="rounded-lg border bg-card">
        <JobStatusTable jobs={jobs} />
      </div>
    </div>
  );
}
