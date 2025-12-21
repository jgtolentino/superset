import { NextRequest, NextResponse } from 'next/server';
import { getJobStatus } from '@/lib/data';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');

    let jobs = await getJobStatus();

    if (status) {
      jobs = jobs.filter((j) => j.last_run_status === status);
    }

    return NextResponse.json({
      data: jobs,
      meta: {
        total_jobs: jobs.length,
        success: jobs.filter((j) => j.last_run_status === 'SUCCESS').length,
        failed: jobs.filter((j) => j.last_run_status === 'FAILED').length,
        running: jobs.filter((j) => j.last_run_status === 'RUNNING').length,
      },
    });
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch jobs' } },
      { status: 500 }
    );
  }
}
