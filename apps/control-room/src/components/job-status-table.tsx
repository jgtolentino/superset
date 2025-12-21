'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, Loader2, Clock, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Job {
  job_id: string;
  job_name: string;
  job_type?: string;
  last_run_status?: string | null;
  last_run_start?: string | null;
  last_run_end?: string | null;
  last_run_duration_seconds?: number | null;
  error_message?: string | null;
}

interface JobStatusTableProps {
  jobs: Job[];
}

export function JobStatusTable({ jobs }: JobStatusTableProps) {
  const [filter, setFilter] = useState<string>('all');

  const filteredJobs = jobs.filter((job) => {
    if (filter === 'all') return true;
    if (filter === 'failed') return job.last_run_status === 'FAILED';
    if (filter === 'success') return job.last_run_status === 'SUCCESS';
    if (filter === 'running') return job.last_run_status === 'RUNNING';
    return true;
  });

  const getStatusIcon = (status?: string | null) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'FAILED':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'RUNNING':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatDuration = (seconds?: number | null) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-2 border-b p-4">
        {['all', 'success', 'failed', 'running'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
              filter === f
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            )}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Job Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Last Run</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Duration</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredJobs.map((job) => (
              <tr key={job.job_id} className="hover:bg-muted/50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(job.last_run_status)}
                    <span className="text-sm">{job.last_run_status || 'Unknown'}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="font-medium">{job.job_name}</span>
                  {job.error_message && (
                    <p className="text-xs text-red-500 mt-1">
                      {job.error_message.slice(0, 100)}...
                    </p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-muted px-2 py-1 text-xs">
                    {job.job_type || 'Unknown'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">
                  {job.last_run_end
                    ? new Date(job.last_run_end).toLocaleString()
                    : '-'}
                </td>
                <td className="px-4 py-3 text-sm">
                  {formatDuration(job.last_run_duration_seconds)}
                </td>
                <td className="px-4 py-3">
                  <a
                    href={`${process.env.NEXT_PUBLIC_DATABRICKS_HOST || '#'}/#job/${job.job_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                  >
                    View <ExternalLink className="h-3 w-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
