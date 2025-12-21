import { NextRequest, NextResponse } from 'next/server';
import { getAdvisorRecommendations } from '@/lib/data';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category');

    let recommendations = await getAdvisorRecommendations();

    if (category) {
      recommendations = recommendations.filter((r) => r.category === category);
    }

    const totalSavings = recommendations.reduce(
      (sum, r) => sum + (r.total_estimated_savings || 0),
      0
    );

    return NextResponse.json({
      data: recommendations,
      meta: {
        total_recommendations: recommendations.reduce(
          (sum, r) => sum + r.recommendation_count,
          0
        ),
        total_estimated_savings: totalSavings,
        categories: recommendations.length,
      },
    });
  } catch (error) {
    console.error('Failed to fetch advisor recommendations:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch recommendations' } },
      { status: 500 }
    );
  }
}
