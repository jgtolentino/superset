#!/usr/bin/env python3
"""
Superset Dashboard Import Script
Imports dashboards from JSON files into Superset using REST API
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
import urllib.error
import urllib.parse


class SupersetDashboardImporter:
    """Handles dashboard imports to Superset via REST API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        
    def authenticate(self) -> bool:
        """Authenticate with Superset and get access token"""
        print("🔐 Authenticating to Superset...")
        
        login_url = f"{self.base_url}/api/v1/security/login"
        login_data = {
            "username": self.username,
            "password": self.password,
            "provider": "db",
            "refresh": True
        }
        
        try:
            req = urllib.request.Request(
                login_url,
                data=json.dumps(login_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    self.access_token = result.get('access_token')
                    print("✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Authentication failed (HTTP {response.status})")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"❌ Authentication failed: {e}")
            print(f"   Response: {e.read().decode('utf-8')[:200]}")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def import_dashboard(self, dashboard_file: Path) -> bool:
        """Import a single dashboard from JSON file"""
        if not self.access_token:
            print("❌ Not authenticated")
            return False
        
        print(f"\n📊 Importing dashboard: {dashboard_file.name}")
        
        try:
            with open(dashboard_file, 'r') as f:
                dashboard_data = json.load(f)
            
            # Validate dashboard data structure
            if not isinstance(dashboard_data, dict):
                print(f"❌ Invalid dashboard format in {dashboard_file.name}")
                return False
            
            # Use Superset's import endpoint
            import_url = f"{self.base_url}/api/v1/dashboard/import/"
            
            # Prepare multipart form data
            boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
            
            # Build multipart body
            body_parts = []
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(b'Content-Disposition: form-data; name="formData"; filename="dashboard.json"')
            body_parts.append(b'Content-Type: application/json')
            body_parts.append(b'')
            body_parts.append(json.dumps(dashboard_data).encode('utf-8'))
            body_parts.append(f'--{boundary}--'.encode())
            body_parts.append(b'')
            
            body = b'\r\n'.join(body_parts)
            
            req = urllib.request.Request(
                import_url,
                data=body,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': f'multipart/form-data; boundary={boundary}'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status in [200, 201]:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"✅ Dashboard imported successfully")
                    if 'message' in result:
                        print(f"   {result['message']}")
                    return True
                else:
                    print(f"❌ Import failed (HTTP {response.status})")
                    return False
                    
        except FileNotFoundError:
            print(f"❌ File not found: {dashboard_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {dashboard_file.name}: {e}")
            return False
        except urllib.error.HTTPError as e:
            print(f"❌ Import failed (HTTP {e.code})")
            error_detail = e.read().decode('utf-8')
            print(f"   Response: {error_detail[:500]}")
            return False
        except Exception as e:
            print(f"❌ Import error: {e}")
            return False
    
    def import_directory(self, directory: Path) -> Dict[str, int]:
        """Import all dashboard JSON files from a directory"""
        if not directory.is_dir():
            print(f"❌ Not a directory: {directory}")
            return {'success': 0, 'failed': 0}
        
        json_files = list(directory.glob('*.json'))
        
        if not json_files:
            print(f"⚠️  No JSON files found in {directory}")
            return {'success': 0, 'failed': 0}
        
        print(f"\n📁 Found {len(json_files)} dashboard file(s)")
        
        results = {'success': 0, 'failed': 0}
        
        for json_file in json_files:
            if self.import_dashboard(json_file):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results


def validate_environment() -> tuple[str, str, str]:
    """Validate required environment variables"""
    required_vars = {
        'BASE_URL': os.getenv('BASE_URL'),
        'SUPERSET_ADMIN_USER': os.getenv('SUPERSET_ADMIN_USER'),
        'SUPERSET_ADMIN_PASS': os.getenv('SUPERSET_ADMIN_PASS')
    }
    
    missing = [var for var, val in required_vars.items() if not val]
    
    if missing:
        print("❌ BLOCKED: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet these in ~/.zshrc or export before running script")
        sys.exit(2)
    
    return (
        required_vars['BASE_URL'],
        required_vars['SUPERSET_ADMIN_USER'],
        required_vars['SUPERSET_ADMIN_PASS']
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Import Superset dashboards from JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import single dashboard
  %(prog)s dashboard.json
  
  # Import all dashboards from directory
  %(prog)s dashboards/
  
  # Import with explicit path
  %(prog)s /path/to/dashboard.json

Environment Variables (required):
  BASE_URL              Superset instance URL
  SUPERSET_ADMIN_USER   Admin username
  SUPERSET_ADMIN_PASS   Admin password
        """
    )
    
    parser.add_argument(
        'path',
        type=str,
        help='Path to dashboard JSON file or directory containing JSON files'
    )
    
    parser.add_argument(
        '--skip-auth-check',
        action='store_true',
        help='Skip initial authentication check (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    base_url, username, password = validate_environment()
    
    print("=== Superset Dashboard Import ===")
    print(f"Base URL: {base_url}")
    print(f"Path: {args.path}")
    
    # Initialize importer
    importer = SupersetDashboardImporter(base_url, username, password)
    
    # Authenticate
    if not args.skip_auth_check:
        if not importer.authenticate():
            sys.exit(1)
    
    # Determine if path is file or directory
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ Path does not exist: {path}")
        sys.exit(1)
    
    # Import dashboards
    if path.is_file():
        success = importer.import_dashboard(path)
        print("\n=== Import Complete ===")
        sys.exit(0 if success else 1)
    
    elif path.is_dir():
        results = importer.import_directory(path)
        
        print("\n=== Import Summary ===")
        print(f"✅ Successful: {results['success']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📊 Total: {results['success'] + results['failed']}")
        
        sys.exit(0 if results['failed'] == 0 else 1)
    
    else:
        print(f"❌ Invalid path type: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
