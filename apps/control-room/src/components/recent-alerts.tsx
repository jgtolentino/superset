import { AlertCircle, Database, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Alert {
  type: 'job' | 'dq' | 'advisor';
  message: string;
  severity: string;
  timestamp?: string | null;
}

interface RecentAlertsProps {
  alerts: Alert[];
}

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  const getIcon = (type: Alert['type']) => {
    switch (type) {
      case 'job':
        return GitBranch;
      case 'dq':
        return Database;
      case 'advisor':
        return AlertCircle;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-500 bg-red-50';
      case 'warning':
        return 'text-yellow-500 bg-yellow-50';
      default:
        return 'text-blue-500 bg-blue-50';
    }
  };

  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b p-4">
        <h3 className="font-semibold">Recent Alerts</h3>
      </div>
      <div className="divide-y">
        {alerts.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            No recent alerts
          </div>
        ) : (
          alerts.slice(0, 5).map((alert, index) => {
            const Icon = getIcon(alert.type);
            return (
              <div key={index} className="flex items-start gap-3 p-4">
                <div
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full',
                    getSeverityColor(alert.severity)
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{alert.message}</p>
                  {alert.timestamp && (
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
