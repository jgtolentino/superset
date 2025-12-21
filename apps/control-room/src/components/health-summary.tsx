import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HealthSummaryProps {
  lastSuccessfulRun?: string | null;
  failingJobsCount: number;
  criticalIssuesCount: number;
  totalJobs: number;
}

export function HealthSummary({
  lastSuccessfulRun,
  failingJobsCount,
  criticalIssuesCount,
  totalJobs,
}: HealthSummaryProps) {
  const overallStatus =
    criticalIssuesCount > 0 || failingJobsCount > totalJobs / 2
      ? 'critical'
      : failingJobsCount > 0
      ? 'warning'
      : 'healthy';

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      label: 'All Systems Healthy',
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    warning: {
      icon: AlertTriangle,
      label: 'Some Issues Detected',
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
    },
    critical: {
      icon: XCircle,
      label: 'Critical Issues',
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
  };

  const config = statusConfig[overallStatus];
  const StatusIcon = config.icon;

  const formatTime = (timestamp?: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b p-4">
        <h3 className="font-semibold">System Health</h3>
      </div>
      <div className="p-4">
        {/* Overall Status */}
        <div
          className={cn(
            'flex items-center gap-3 rounded-lg p-3',
            config.bg
          )}
        >
          <StatusIcon className={cn('h-6 w-6', config.color)} />
          <div>
            <p className={cn('font-medium', config.color)}>{config.label}</p>
            <p className="text-sm text-muted-foreground">
              Last successful run: {formatTime(lastSuccessfulRun)}
            </p>
          </div>
        </div>

        {/* Details */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">
                {totalJobs - failingJobsCount}/{totalJobs}
              </p>
              <p className="text-xs text-muted-foreground">Jobs Running</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle
              className={cn(
                'h-4 w-4',
                criticalIssuesCount > 0 ? 'text-red-500' : 'text-muted-foreground'
              )}
            />
            <div>
              <p className="text-sm font-medium">{criticalIssuesCount}</p>
              <p className="text-xs text-muted-foreground">Critical Issues</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
