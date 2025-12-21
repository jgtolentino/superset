import { NextResponse } from 'next/server';
import { DatabricksClient } from '@/lib/databricks';

export async function GET() {
  const checks: Record<string, boolean> = {
    api: true,
    databricks: false,
  };

  // Check Databricks
  try {
    const client = new DatabricksClient();
    checks.databricks = await client.healthCheck();
  } catch {
    checks.databricks = false;
  }

  const healthy = Object.values(checks).every(Boolean);

  return NextResponse.json(
    {
      status: healthy ? 'healthy' : 'degraded',
      checks,
      timestamp: new Date().toISOString(),
    },
    { status: healthy ? 200 : 503 }
  );
}
