import { AdvisorSummary } from '@/components/advisor-summary';
import { getAdvisorRecommendations } from '@/lib/data';

export const revalidate = 300; // 5 minutes

export default async function AdvisorPage() {
  const recommendations = await getAdvisorRecommendations();

  // Group by category
  const byCategory = recommendations.reduce((acc, rec) => {
    acc[rec.category] = acc[rec.category] || { count: 0, savings: 0, highImpact: 0 };
    acc[rec.category].count++;
    acc[rec.category].savings += rec.total_estimated_savings || 0;
    acc[rec.category].highImpact += rec.high_impact_count || 0;
    return acc;
  }, {} as Record<string, { count: number; savings: number; highImpact: number }>);

  const totalSavings = Object.values(byCategory).reduce((sum, c) => sum + c.savings, 0);
  const totalRecommendations = Object.values(byCategory).reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Azure Advisor</h1>
        <p className="text-muted-foreground">
          Cost, security, and optimization recommendations
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Recommendations</p>
          <p className="text-2xl font-bold">{totalRecommendations}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Estimated Annual Savings</p>
          <p className="text-2xl font-bold text-green-600">
            ${totalSavings.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Categories</p>
          <p className="text-2xl font-bold">{Object.keys(byCategory).length}</p>
        </div>
      </div>

      {/* Category Breakdown */}
      <AdvisorSummary categories={byCategory} />
    </div>
  );
}
