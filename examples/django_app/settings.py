"""
Django settings example with RootSense configuration.

Add this configuration to your Django project's settings.py file.
"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # RootSense middleware - add near the end but before error handling middleware
    'rootsense.integrations.django.RootSenseDjangoMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# ROOTSENSE CONFIGURATION
# ============================================================================

ROOTSENSE = {
    # Required settings
    'api_key': 'your-api-key',  # Replace with your RootSense API key
    'project_id': 'your-project-id',  # Replace with your project ID
    
    # Optional settings
    'api_url': 'https://api.rootsense.ai',  # RootSense API endpoint
    'environment': 'production',  # Environment name (production, staging, development, etc.)
    'release': None,  # Application version/release (e.g., '1.0.0' or git commit hash)
    'server_name': None,  # Server hostname (auto-detected if not specified)
    
    # Data collection settings
    'send_default_pii': False,  # Whether to send PII (emails, IPs, usernames) by default
    'enable_prometheus': True,  # Enable Prometheus metrics collection
    'max_breadcrumbs': 100,  # Maximum number of breadcrumbs to store
    
    # Performance settings
    'sample_rate': 1.0,  # Sample rate for events (0.0 to 1.0, 1.0 = 100%)
    'buffer_size': 1000,  # Maximum events in buffer before dropping
    'flush_interval': 5.0,  # Seconds between buffer flushes
    'max_retries': 3,  # Maximum retry attempts for failed requests
    'timeout': 10.0,  # Request timeout in seconds
    
    # Debug settings
    'debug': True,  # Enable debug logging
}

# ============================================================================
# ENVIRONMENT-BASED CONFIGURATION (Optional)
# ============================================================================

import os

# You can also load RootSense config from environment variables
ROOTSENSE = {
    'api_key': os.environ.get('ROOTSENSE_API_KEY', 'your-api-key'),
    'project_id': os.environ.get('ROOTSENSE_PROJECT_ID', 'your-project-id'),
    'environment': os.environ.get('DJANGO_ENV', 'production'),
    'debug': DEBUG,  # Use Django's DEBUG setting
    'send_default_pii': False,
    'enable_prometheus': True,
}
