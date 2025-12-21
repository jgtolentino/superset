import { NextRequest, NextResponse } from 'next/server';
import { getDataQualityIssues } from '@/lib/data';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const severity = searchParams.get('severity');
    const passed = searchParams.get('passed');

    let issues = await getDataQualityIssues();

    if (severity) {
      issues = issues.filter((i) => i.severity === severity);
    }

    if (passed !== null) {
      const passedBool = passed === 'true';
      issues = issues.filter((i) => i.passed === passedBool);
    }

    return NextResponse.json({
      data: issues,
      meta: {
        total_checks: issues.length,
        passed: issues.filter((i) => i.passed).length,
        failed: issues.filter((i) => !i.passed).length,
        critical: issues.filter((i) => i.severity === 'critical' && !i.passed).length,
      },
    });
  } catch (error) {
    console.error('Failed to fetch DQ issues:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch DQ issues' } },
      { status: 500 }
    );
  }
}
