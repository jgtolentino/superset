'use client';

import { useState } from 'react';
import { AlertTriangle, Database, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DQIssue {
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

interface DQIssuesListProps {
  issues: DQIssue[];
}

export function DQIssuesList({ issues }: DQIssuesListProps) {
  const [filter, setFilter] = useState<string>('all');

  const filteredIssues = issues.filter((issue) => {
    if (filter === 'all') return true;
    return issue.severity === filter;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-500 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-500 bg-blue-50 border-blue-200';
    }
  };

  const handleCreateAction = async (issue: DQIssue) => {
    try {
      const response = await fetch('/api/notion/actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `DQ Issue: ${issue.check_type} on ${issue.table_name}`,
          description: `Expected: ${issue.expected_value}\nActual: ${issue.actual_value}`,
          source: 'dq',
          source_id: issue.metric_id,
          priority: issue.severity === 'critical' ? 'high' : 'medium',
        }),
      });

      if (response.ok) {
        alert('Action created in Notion!');
      } else {
        throw new Error('Failed to create action');
      }
    } catch (error) {
      alert('Failed to create action. Check console for details.');
      console.error(error);
    }
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-2 border-b p-4">
        {['all', 'critical', 'warning', 'info'].map((f) => (
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

      {/* Issues List */}
      <div className="divide-y">
        {filteredIssues.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No issues found
          </div>
        ) : (
          filteredIssues.map((issue) => (
            <div key={issue.metric_id} className="p-4 hover:bg-muted/50">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded-full',
                      getSeverityColor(issue.severity)
                    )}
                  >
                    <Database className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {issue.check_type} check failed
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {issue.table_name}
                      {issue.column_name && ` / ${issue.column_name}`}
                    </p>
                    <div className="mt-2 flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">
                        Expected: {issue.expected_value || 'N/A'}
                      </span>
                      <ArrowRight className="h-3 w-3" />
                      <span className="font-medium text-red-500">
                        Actual: {issue.actual_value || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'rounded-full border px-2 py-0.5 text-xs font-medium',
                      getSeverityColor(issue.severity)
                    )}
                  >
                    {issue.severity}
                  </span>
                  <button
                    onClick={() => handleCreateAction(issue)}
                    className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    Create Action
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
