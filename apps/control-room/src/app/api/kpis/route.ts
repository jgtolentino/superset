import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getKPIs } from '@/lib/data';

const QuerySchema = z.object({
  from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  dimension: z.string().optional(),
  metric: z.string().optional(),
});

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const params = QuerySchema.parse({
      from: searchParams.get('from') || undefined,
      to: searchParams.get('to') || undefined,
      dimension: searchParams.get('dimension') || undefined,
      metric: searchParams.get('metric') || undefined,
    });

    let kpis = await getKPIs();

    // Apply filters
    if (params.from) {
      kpis = kpis.filter((k) => k.period >= params.from!);
    }
    if (params.to) {
      kpis = kpis.filter((k) => k.period <= params.to!);
    }
    if (params.dimension) {
      kpis = kpis.filter((k) => k.dimension === params.dimension);
    }
    if (params.metric) {
      kpis = kpis.filter((k) => k.metric_name === params.metric);
    }

    return NextResponse.json({
      data: kpis,
      meta: {
        total_records: kpis.length,
        filters: params,
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', details: error.errors } },
        { status: 400 }
      );
    }

    console.error('Failed to fetch KPIs:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch KPIs' } },
      { status: 500 }
    );
  }
}
