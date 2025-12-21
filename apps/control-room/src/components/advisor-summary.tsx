'use client';

import { DollarSign, Shield, Zap, Settings, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CategoryData {
  count: number;
  savings: number;
  highImpact: number;
}

interface AdvisorSummaryProps {
  categories: Record<string, CategoryData>;
}

const categoryConfig: Record<string, { icon: typeof DollarSign; color: string }> = {
  Cost: { icon: DollarSign, color: 'text-green-500 bg-green-50' },
  Security: { icon: Shield, color: 'text-red-500 bg-red-50' },
  Reliability: { icon: Zap, color: 'text-blue-500 bg-blue-50' },
  OperationalExcellence: { icon: Settings, color: 'text-purple-500 bg-purple-50' },
  Performance: { icon: TrendingUp, color: 'text-orange-500 bg-orange-50' },
};

export function AdvisorSummary({ categories }: AdvisorSummaryProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Object.entries(categories).map(([category, data]) => {
        const config = categoryConfig[category] || {
          icon: Settings,
          color: 'text-gray-500 bg-gray-50',
        };
        const Icon = config.icon;

        return (
          <div key={category} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between">
              <div
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-lg',
                  config.color
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              {data.highImpact > 0 && (
                <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">
                  {data.highImpact} high impact
                </span>
              )}
            </div>
            <div className="mt-4">
              <h3 className="font-semibold">{category}</h3>
              <p className="text-2xl font-bold">{data.count}</p>
              <p className="text-sm text-muted-foreground">recommendations</p>
            </div>
            {data.savings > 0 && (
              <div className="mt-4 rounded-lg bg-green-50 p-2">
                <p className="text-sm font-medium text-green-600">
                  ${data.savings.toLocaleString()} potential savings
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
