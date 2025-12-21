import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: number;
  unit: string;
  format?: 'number' | 'currency' | 'percent';
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'success' | 'warning' | 'error';
}

const statusColors = {
  success: 'border-green-200 bg-green-50',
  warning: 'border-yellow-200 bg-yellow-50',
  error: 'border-red-200 bg-red-50',
  default: 'border-border bg-card',
};

export function KPICard({
  title,
  value,
  unit,
  format = 'number',
  trend,
  trendValue,
  status,
}: KPICardProps) {
  const formattedValue = formatValue(value, format);

  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-colors',
        statusColors[status || 'default']
      )}
    >
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold">{formattedValue}</span>
        {format !== 'currency' && (
          <span className="text-sm text-muted-foreground">{unit}</span>
        )}
      </div>
      {trend && (
        <div className="mt-2 flex items-center gap-1 text-sm">
          <TrendIcon direction={trend} />
          <span
            className={cn(
              trend === 'up' && 'text-green-600',
              trend === 'down' && 'text-red-600',
              trend === 'stable' && 'text-muted-foreground'
            )}
          >
            {trendValue !== undefined ? `${trendValue}%` : ''} vs last period
          </span>
        </div>
      )}
    </div>
  );
}

function TrendIcon({ direction }: { direction: 'up' | 'down' | 'stable' }) {
  switch (direction) {
    case 'up':
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    case 'stable':
      return <Minus className="h-4 w-4 text-muted-foreground" />;
  }
}

function formatValue(value: number, format: 'number' | 'currency' | 'percent'): string {
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    case 'percent':
      return `${value.toFixed(1)}%`;
    default:
      return value.toLocaleString();
  }
}
