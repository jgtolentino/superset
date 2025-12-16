"""
Superset Production Configuration
Configures PostgreSQL as metadata database (NOT SQLite)

CRITICAL FIX: Prevents "sqlite3.OperationalError: database is locked"
in multi-worker production environments
"""
import os

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Metadata database (Superset's own configuration/logs/dashboards)
# MUST be PostgreSQL in production, NOT SQLite
#
# Supports both naming conventions:
# 1. SUPERSET__SQLALCHEMY_DATABASE_URI (preferred, widely supported)
# 2. SQLALCHEMY_DATABASE_URI (fallback)
SQLALCHEMY_DATABASE_URI = os.getenv(
    'SUPERSET__SQLALCHEMY_DATABASE_URI',
    os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        # Final fallback constructs from individual env vars
        'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'.format(
            user=os.getenv('DATABASE_USER', 'postgres'),
            password=os.getenv('DATABASE_PASSWORD', ''),
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=os.getenv('DATABASE_PORT', '5432'),
            db=os.getenv('DATABASE_DB', 'postgres')
        )
    )
)

# Database connection pool settings
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', '10'))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', '20'))
SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '30'))

# ============================================================================
# SECURITY
# ============================================================================

# Supports both SUPERSET__SECRET_KEY and SUPERSET_SECRET_KEY
SECRET_KEY = os.getenv(
    'SUPERSET__SECRET_KEY',
    os.getenv('SUPERSET_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')
)

# Session configuration
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Disable SQLite check (we're using Postgres)
PREVENT_UNSAFE_DB_CONNECTIONS = False

# ============================================================================
# PERFORMANCE
# ============================================================================

SUPERSET_WEBSERVER_TIMEOUT = int(os.getenv('SUPERSET_WEBSERVER_TIMEOUT', '300'))

# Enable template processing
ENABLE_TEMPLATE_PROCESSING = True

# ============================================================================
# FEATURE FLAGS
# ============================================================================

FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_NATIVE_FILTERS_SET': True,
    'EMBEDDED_SUPERSET': os.getenv('ENABLE_EMBEDDED', 'False') == 'True',
}

# ============================================================================
# LOGGING
# ============================================================================

import logging

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'

# Enable time-based log rotation
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = logging.INFO

# ============================================================================
# CACHING (Optional - Redis)
# ============================================================================

# If Redis is configured, use it for caching
REDIS_HOST = os.getenv('REDIS_HOST', None)
REDIS_PORT = os.getenv('REDIS_PORT', '6379')

if REDIS_HOST:
    CACHE_CONFIG = {
        'CACHE_TYPE': 'redis',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'superset_',
        'CACHE_REDIS_HOST': REDIS_HOST,
        'CACHE_REDIS_PORT': int(REDIS_PORT),
    }

    # Results backend for async queries
    RESULTS_BACKEND = {
        'cache_type': 'redis',
        'cache_default_timeout': 86400,  # 24 hours
        'cache_key_prefix': 'superset_results_',
        'cache_redis_host': REDIS_HOST,
        'cache_redis_port': int(REDIS_PORT),
    }
else:
    # Fallback to simple cache (not recommended for production)
    CACHE_CONFIG = {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300,
    }

# ============================================================================
# EMAIL (Optional)
# ============================================================================

SMTP_HOST = os.getenv('SMTP_HOST', None)

if SMTP_HOST:
    SMTP_STARTTLS = os.getenv('SMTP_STARTTLS', 'True') == 'True'
    SMTP_SSL = os.getenv('SMTP_SSL', 'False') == 'True'
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_MAIL_FROM = os.getenv('SMTP_MAIL_FROM', 'superset@example.com')

# ============================================================================
# CUSTOMIZATION
# ============================================================================

# App name
APP_NAME = os.getenv('APP_NAME', 'Superset')

# Welcome message
WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE', None)

# Custom CSS
CSS_THEME_URL = os.getenv('CSS_THEME_URL', None)
