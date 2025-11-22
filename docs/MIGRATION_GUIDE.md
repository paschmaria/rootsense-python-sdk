# Migration Guide: Phase 0 Refactoring

This guide helps you migrate to the new OpenTelemetry-based instrumentation.

## What Changed

### Major Changes

1. **Removed**: `PrometheusCollector` - functionality moved to `ErrorCollector`
2. **Added**: OpenTelemetry auto-instrumentation with custom exporters
3. **Added**: Auto-resolution tracking for all operation types
4. **Simplified**: Configuration API (removed duplicate `init()` functions)
5. **Enhanced**: Support for DB queries, HTTP, Redis, Celery automatically

### Breaking Changes

#### 1. PrometheusCollector Removed

**Before:**
```python
from rootsense.collectors import PrometheusCollector

prometheus = PrometheusCollector(config)
prometheus.track_request(...)
```

**After:**
```python
# Metrics are automatically collected via OpenTelemetry
# No manual tracking needed!
import rootsense

rootsense.init(
    api_key="your-key",
    project_id="your-project",
    enable_auto_instrumentation=True  # Default
)
```

#### 2. Configuration Changes

**Before:**
```python
import rootsense
from rootsense.config import init

# Two ways to initialize (confusing)
init(api_key="...", project_id="...")
# OR
rootsense.init(api_key="...", project_id="...")
```

**After:**
```python
import rootsense

# One clear way
rootsense.init(
    api_key="your-key",
    project_id="your-project",
    enable_auto_instrumentation=True,  # New option
    service_name="my-service",          # New option
    service_version="1.0.0"             # New option
)
```

#### 3. Manual Database Monitoring Removed

**Before:**
```python
from rootsense.performance import DatabaseMonitor

# Manual tracking required
db_monitor = DatabaseMonitor(config)
db_monitor.track_query(query, duration)
```

**After:**
```python
# Database queries automatically tracked via OpenTelemetry
import rootsense

rootsense.init(
    api_key="your-key",
    project_id="your-project"
)

# All Django ORM and SQLAlchemy queries tracked automatically!
```

## Migration Steps

### Step 1: Update Dependencies

Install the new version with auto-instrumentation:

```bash
# If using Django
pip install --upgrade rootsense[django,instrumentation]

# If using Flask
pip install --upgrade rootsense[flask,instrumentation]

# If using FastAPI
pip install --upgrade rootsense[fastapi,instrumentation]

# Or install everything
pip install --upgrade rootsense[all]
```

### Step 2: Update Initialization

**Before:**
```python
import rootsense
from rootsense.config import Config

config = Config(
    api_key="your-key",
    project_id="your-project"
)
client = rootsense.RootSenseClient(config)
```

**After:**
```python
import rootsense

rootsense.init(
    api_key="your-key",
    project_id="your-project",
    service_name="my-app",  # Recommended: add service name
    environment="production"
)
```

### Step 3: Remove Manual Instrumentation

**Before (Django):**
```python
# settings.py
import rootsense
from rootsense.middleware.django import RootSenseMiddleware

rootsense.init(...)

MIDDLEWARE = [
    'rootsense.middleware.django.RootSenseMiddleware',
    # ... other middleware
]
```

**After (Django):**
```python
# settings.py
import rootsense

# Just initialize - middleware and instrumentation handled automatically
rootsense.init(
    api_key="your-key",
    project_id="your-project",
    service_name="my-django-app"
)

# No need to add middleware manually!
# OpenTelemetry handles everything
```

**Before (Flask):**
```python
from flask import Flask
import rootsense
from rootsense.middleware.flask import init_flask

app = Flask(__name__)
rootsense.init(...)
init_flask(app)
```

**After (Flask):**
```python
from flask import Flask
import rootsense

app = Flask(__name__)

# Just initialize - Flask auto-instrumented
rootsense.init(
    api_key="your-key",
    project_id="your-project",
    service_name="my-flask-app"
)
```

### Step 4: Remove Custom Metrics Collection

If you were manually collecting metrics:

**Before:**
```python
from rootsense.collectors import PrometheusCollector

prometheus = PrometheusCollector(config)

# Manual metric recording
prometheus.counter('requests_total').inc()
prometheus.histogram('request_duration_seconds').observe(duration)
```

**After:**
```python
# Metrics collected automatically!
# No code changes needed

# If you want custom metrics, use OpenTelemetry directly:
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
counter = meter.create_counter(
    "requests_total",
    description="Total requests"
)
counter.add(1)
```

### Step 5: Test Auto-Resolution

Verify auto-resolution works:

```python
import rootsense

rootsense.init(
    api_key="your-key",
    project_id="your-project",
    debug=True  # Enable debug logging
)

# Trigger an error
try:
    1 / 0
except Exception as e:
    rootsense.capture_exception(e)

# Check logs for:
# "OpenTelemetry auto-instrumentation initialized"
# "Auto-instrumentation enabled for: Django, SQLAlchemy, ..."
```

## New Features You Get

### 1. Automatic Database Query Tracking

```python
# Django ORM - all queries tracked automatically
User.objects.filter(email="test@example.com")

# SQLAlchemy - all queries tracked automatically
session.query(User).filter_by(email="test@example.com").first()
```

### 2. Automatic HTTP Request Tracking

```python
# All outgoing HTTP requests tracked automatically
import requests
requests.get("https://api.example.com/data")

import httpx
httpx.get("https://api.example.com/data")
```

### 3. Automatic Redis Tracking

```python
# All Redis operations tracked automatically
import redis
r = redis.Redis()
r.get("key")
r.set("key", "value")
```

### 4. Automatic Celery Task Tracking

```python
# All Celery tasks tracked automatically
from celery import Celery

app = Celery('tasks')

@app.task
def process_data(data):
    # Task execution tracked automatically
    pass
```

### 5. Auto-Resolution for All Operations

When any operation (HTTP, DB, Redis, Celery) recovers from errors:
- Success signals sent automatically
- Incidents auto-resolved
- No manual intervention needed

## Rollback Plan

If you need to rollback:

```bash
# Install previous version
pip install rootsense==0.0.9  # Replace with your version

# Revert code changes
git checkout main -- <files>
```

## Need Help?

- Check [OpenTelemetry Integration docs](./OPENTELEMETRY_INTEGRATION.md)
- Check [Auto-Resolution docs](./AUTO_RESOLUTION.md)
- Enable debug logging: `rootsense.init(..., debug=True)`
- Contact support: support@rootsense.ai
