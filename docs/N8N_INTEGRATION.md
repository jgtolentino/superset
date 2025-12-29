# n8n Integration Guide for Superset

This guide outlines integration points for building n8n nodes to automate Superset dashboard operations.

## Overview

n8n can integrate with Superset using its REST API to automate:
- Dashboard imports/exports
- Dataset management
- Chart creation
- User management
- Automated reporting

## Authentication

### REST API Authentication Flow

```javascript
// 1. Login to get access token
POST /api/v1/security/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password",
  "provider": "db",
  "refresh": true
}

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

// 2. Use token in subsequent requests
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Token Management

- Access tokens expire after a configurable time (default: 15 minutes)
- Refresh tokens can be used to get new access tokens
- Store tokens securely in n8n credentials

## Key API Endpoints

### Dashboard Operations

#### List Dashboards
```
GET /api/v1/dashboard/
Authorization: Bearer {token}

Query parameters:
- q: JSON query filter
- page_size: Results per page
- page: Page number
```

#### Get Dashboard
```
GET /api/v1/dashboard/{id}
Authorization: Bearer {token}
```

#### Import Dashboard
```
POST /api/v1/dashboard/import/
Authorization: Bearer {token}
Content-Type: multipart/form-data

Form data:
- formData: Dashboard JSON file
- overwrite: Boolean (optional)
```

#### Export Dashboard
```
GET /api/v1/dashboard/export/?q=!(ids:!({id}))
Authorization: Bearer {token}

Returns: ZIP file containing dashboard JSON
```

### Dataset Operations

#### List Datasets
```
GET /api/v1/dataset/
Authorization: Bearer {token}
```

#### Create Dataset
```
POST /api/v1/dataset/
Authorization: Bearer {token}
Content-Type: application/json

{
  "database": 1,
  "schema": "public",
  "table_name": "my_table"
}
```

### Chart Operations

#### List Charts
```
GET /api/v1/chart/
Authorization: Bearer {token}
```

#### Get Chart
```
GET /api/v1/chart/{id}
Authorization: Bearer {token}
```

## n8n Node Structure

### Basic Node Implementation

```typescript
import {
    IExecuteFunctions,
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
} from 'n8n-workflow';

export class SupersetDashboard implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'Superset Dashboard',
        name: 'supersetDashboard',
        icon: 'file:superset.svg',
        group: ['transform'],
        version: 1,
        description: 'Interact with Apache Superset dashboards',
        defaults: {
            name: 'Superset Dashboard',
        },
        inputs: ['main'],
        outputs: ['main'],
        credentials: [
            {
                name: 'supersetApi',
                required: true,
            },
        ],
        properties: [
            {
                displayName: 'Operation',
                name: 'operation',
                type: 'options',
                options: [
                    {
                        name: 'Import Dashboard',
                        value: 'import',
                        description: 'Import a dashboard from JSON',
                    },
                    {
                        name: 'Export Dashboard',
                        value: 'export',
                        description: 'Export a dashboard to JSON',
                    },
                    {
                        name: 'List Dashboards',
                        value: 'list',
                        description: 'List all dashboards',
                    },
                ],
                default: 'list',
            },
            // Add operation-specific parameters
        ],
    };

    async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
        const items = this.getInputData();
        const returnData: INodeExecutionData[] = [];
        const operation = this.getNodeParameter('operation', 0) as string;
        
        // Get credentials
        const credentials = await this.getCredentials('supersetApi');
        const baseUrl = credentials.baseUrl as string;
        
        // Authenticate
        const accessToken = await this.authenticate(
            baseUrl,
            credentials.username as string,
            credentials.password as string
        );
        
        // Execute operation
        for (let i = 0; i < items.length; i++) {
            if (operation === 'import') {
                // Import dashboard logic
            } else if (operation === 'export') {
                // Export dashboard logic
            } else if (operation === 'list') {
                // List dashboards logic
            }
        }
        
        return [returnData];
    }
    
    private async authenticate(
        baseUrl: string,
        username: string,
        password: string
    ): Promise<string> {
        // Authentication implementation
        const response = await this.helpers.request({
            method: 'POST',
            url: `${baseUrl}/api/v1/security/login`,
            json: true,
            body: {
                username,
                password,
                provider: 'db',
                refresh: true,
            },
        });
        
        return response.access_token;
    }
}
```

### Credential Type

```typescript
import {
    ICredentialType,
    INodeProperties,
} from 'n8n-workflow';

export class SupersetApi implements ICredentialType {
    name = 'supersetApi';
    displayName = 'Superset API';
    documentationUrl = 'https://superset.apache.org/docs/api';
    properties: INodeProperties[] = [
        {
            displayName: 'Base URL',
            name: 'baseUrl',
            type: 'string',
            default: '',
            placeholder: 'https://superset.example.com',
            description: 'The base URL of your Superset instance',
        },
        {
            displayName: 'Username',
            name: 'username',
            type: 'string',
            default: '',
            description: 'Superset username',
        },
        {
            displayName: 'Password',
            name: 'password',
            type: 'string',
            typeOptions: {
                password: true,
            },
            default: '',
            description: 'Superset password',
        },
    ];
}
```

## Example Workflows

### Automated Dashboard Import

```json
{
  "name": "Import Superset Dashboards",
  "nodes": [
    {
      "parameters": {},
      "name": "Cron",
      "type": "n8n-nodes-base.cron",
      "position": [250, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "operation": "import",
        "dashboardJson": "={{$json.dashboard}}"
      },
      "name": "Superset Dashboard",
      "type": "n8n-nodes-custom.supersetDashboard",
      "position": [450, 300],
      "credentials": {
        "supersetApi": "Superset Production"
      }
    }
  ]
}
```

### Dashboard Export and Backup

```json
{
  "name": "Backup Superset Dashboards",
  "nodes": [
    {
      "parameters": {
        "operation": "list"
      },
      "name": "List Dashboards",
      "type": "n8n-nodes-custom.supersetDashboard"
    },
    {
      "parameters": {
        "operation": "export",
        "dashboardId": "={{$json.id}}"
      },
      "name": "Export Dashboard",
      "type": "n8n-nodes-custom.supersetDashboard"
    },
    {
      "parameters": {
        "path": "=/backups/dashboard_{{$json.id}}.json",
        "data": "={{$json.dashboard}}"
      },
      "name": "Save to File",
      "type": "n8n-nodes-base.writeFile"
    }
  ]
}
```

## Error Handling

### Common Error Responses

```javascript
// Authentication error
{
  "message": "Invalid login credentials"
}

// Authorization error
{
  "message": "You don't have permission to access this resource"
}

// Not found
{
  "message": "Dashboard not found"
}

// Validation error
{
  "message": "Invalid dashboard format",
  "errors": [...]
}
```

### Retry Logic

Implement retry logic for transient errors:

```javascript
async function retryRequest(fn, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            if (error.statusCode >= 500 || error.statusCode === 429) {
                await sleep(1000 * Math.pow(2, i)); // Exponential backoff
                continue;
            }
            throw error;
        }
    }
}
```

## Testing

### Using the Import Script

Test API integration using the provided Python script:

```bash
# Set environment variables
export BASE_URL="https://superset.example.com"
export SUPERSET_ADMIN_USER="admin"
export SUPERSET_ADMIN_PASS="password"

# Test authentication
./scripts/import_dashboard.py examples/dashboards/sample_dashboard.json
```

### API Testing with curl

```bash
# Login
ACCESS_TOKEN=$(curl -X POST "${BASE_URL}/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password","provider":"db"}' \
  | jq -r '.access_token')

# List dashboards
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/api/v1/dashboard/"

# Get specific dashboard
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/api/v1/dashboard/1"
```

## Security Considerations

1. **Credentials Storage**: Use n8n's encrypted credential storage
2. **Token Expiration**: Implement token refresh logic
3. **HTTPS Only**: Always use HTTPS in production
4. **Rate Limiting**: Implement rate limiting to avoid overwhelming the API
5. **Audit Logging**: Log all dashboard operations for audit trail

## Resources

- [Superset REST API Documentation](https://superset.apache.org/docs/api)
- [n8n Node Development Guide](https://docs.n8n.io/integrations/creating-nodes/)
- [Example Dashboard Import Script](../scripts/import_dashboard.py)

## Next Steps

1. Install n8n: `npm install -g n8n`
2. Create custom node directory: `~/.n8n/custom/`
3. Implement SupersetDashboard node using examples above
4. Test with local Superset instance
5. Publish to n8n community nodes

## Support

For issues or questions:
- Repository: https://github.com/jgtolentino/superset
- Superset Slack: https://apache-superset.slack.com
- n8n Community: https://community.n8n.io
