'use client';

import { useState } from 'react';
import { ArrowUpDown, ExternalLink, AlertTriangle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Project {
  project_id: string;
  name: string;
  program_id?: string;
  status?: string;
  priority?: string;
  owner?: string;
  budget: number;
  actual: number;
  variance: number;
  burnRate: number;
}

interface ProjectsTableProps {
  projects: Project[];
}

export function ProjectsTable({ projects }: ProjectsTableProps) {
  const [sortField, setSortField] = useState<keyof Project>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filter, setFilter] = useState<string>('');

  const handleSort = (field: keyof Project) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedProjects = [...projects]
    .filter(
      (p) =>
        p.name.toLowerCase().includes(filter.toLowerCase()) ||
        p.owner?.toLowerCase().includes(filter.toLowerCase())
    )
    .sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal || '');
      const bStr = String(bVal || '');
      return sortDirection === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700';
      case 'completed':
        return 'bg-blue-100 text-blue-700';
      case 'on_hold':
        return 'bg-yellow-100 text-yellow-700';
      case 'cancelled':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div>
      {/* Search */}
      <div className="border-b p-4">
        <input
          type="text"
          placeholder="Search projects..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center gap-1 text-sm font-medium"
                >
                  Project <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Owner</th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('budget')}
                  className="flex items-center gap-1 text-sm font-medium ml-auto"
                >
                  Budget <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('actual')}
                  className="flex items-center gap-1 text-sm font-medium ml-auto"
                >
                  Actual <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('variance')}
                  className="flex items-center gap-1 text-sm font-medium ml-auto"
                >
                  Variance <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-center text-sm font-medium">Health</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {sortedProjects.map((project) => (
              <tr key={project.project_id} className="hover:bg-muted/50">
                <td className="px-4 py-3">
                  <span className="font-medium">{project.name}</span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      'rounded-full px-2 py-1 text-xs font-medium',
                      getStatusColor(project.status)
                    )}
                  >
                    {project.status || 'Unknown'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">
                  {project.owner || '-'}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  {formatCurrency(project.budget)}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  {formatCurrency(project.actual)}
                </td>
                <td
                  className={cn(
                    'px-4 py-3 text-right text-sm font-medium',
                    project.variance > 0 ? 'text-red-600' : 'text-green-600'
                  )}
                >
                  {project.variance >= 0 ? '+' : ''}
                  {formatCurrency(project.variance)}
                </td>
                <td className="px-4 py-3 text-center">
                  {project.burnRate > 100 ? (
                    <AlertTriangle className="mx-auto h-4 w-4 text-yellow-500" />
                  ) : (
                    <CheckCircle className="mx-auto h-4 w-4 text-green-500" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
