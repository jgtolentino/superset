/**
 * Databricks SQL client for querying lakehouse data.
 */

interface DatabricksConfig {
  host: string;
  token: string;
  httpPath: string;
  catalog: string;
}

interface QueryResult<T> {
  data: T[];
}

export class DatabricksClient {
  private config: DatabricksConfig;

  constructor() {
    this.config = {
      host: process.env.DATABRICKS_HOST || '',
      token: process.env.DATABRICKS_TOKEN || '',
      httpPath: process.env.DATABRICKS_HTTP_PATH || '',
      catalog: process.env.DATABRICKS_CATALOG || 'main',
    };

    if (!this.config.host || !this.config.token) {
      console.warn('Databricks credentials not configured. Using mock data.');
    }
  }

  async query<T>(sql: string): Promise<T[]> {
    if (!this.config.host || !this.config.token) {
      throw new Error('Databricks not configured');
    }

    const host = this.config.host.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const url = `https://${host}/api/2.0/sql/statements`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        warehouse_id: this.extractWarehouseId(),
        statement: sql,
        wait_timeout: '30s',
      }),
      cache: 'no-store',
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Databricks query failed: ${response.status} ${error}`);
    }

    const result = await response.json();

    // Check if query is still running
    if (result.status?.state === 'PENDING' || result.status?.state === 'RUNNING') {
      // Poll for results
      return this.pollForResults<T>(result.statement_id);
    }

    if (result.status?.state === 'FAILED') {
      throw new Error(`Query failed: ${result.status.error?.message}`);
    }

    // Parse results
    return this.parseResults<T>(result);
  }

  private extractWarehouseId(): string {
    // Extract warehouse ID from HTTP path
    // Format: /sql/1.0/warehouses/{warehouse_id}
    const match = this.config.httpPath.match(/warehouses\/([a-f0-9]+)/i);
    return match?.[1] || '';
  }

  private async pollForResults<T>(statementId: string): Promise<T[]> {
    const host = this.config.host.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const url = `https://${host}/api/2.0/sql/statements/${statementId}`;

    for (let i = 0; i < 30; i++) {
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.config.token}`,
        },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error(`Failed to poll results: ${response.status}`);
      }

      const result = await response.json();

      if (result.status?.state === 'SUCCEEDED') {
        return this.parseResults<T>(result);
      }

      if (result.status?.state === 'FAILED') {
        throw new Error(`Query failed: ${result.status.error?.message}`);
      }
    }

    throw new Error('Query timed out');
  }

  private parseResults<T>(result: any): T[] {
    const manifest = result.manifest;
    const data = result.result?.data_array || [];

    if (!manifest?.schema?.columns) {
      return [];
    }

    const columns = manifest.schema.columns.map((c: any) => c.name);

    return data.map((row: any[]) => {
      const obj: any = {};
      columns.forEach((col: string, idx: number) => {
        obj[col] = row[idx];
      });
      return obj as T;
    });
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.query('SELECT 1 as test');
      return true;
    } catch {
      return false;
    }
  }
}
