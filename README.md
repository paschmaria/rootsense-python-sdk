# RootSense Python SDK

Python SDK for [RootSense](https://rootsense.ai) - AI-powered incident management platform with automatic error tracking, infrastructure monitoring, and intelligent root cause analysis.

## Features

- 🚨 **Automatic Error Tracking** - Capture exceptions with full context
- 📊 **Built-in Metrics** - Prometheus metrics for request count, duration, errors
- 🔍 **Auto-Instrumentation** - Leverage OpenTelemetry to automatically capture:
  - Django ORM database queries
  - Flask/FastAPI HTTP requests
  - SQLAlchemy queries
  - HTTP requests (requests, httpx, urllib)
  - Redis operations
  - Celery tasks
- 🔒 **PII Sanitization** - Automatic redaction of sensitive data
- 🎯 **Smart Grouping** - Fingerprint-based incident grouping
- 🌐 **Framework Support** - Django, Flask, FastAPI, WSGI/ASGI

## Installation

```bash
# Basic installation
pip install rootsense

# With framework support
pip install rootsense[django]
pip install rootsense[flask]
pip install rootsense[fastapi]

# With auto-instrumentation (recommended)
pip install rootsense[instrumentation]

# Full installation
pip install rootsense[all]
```

## Quick Start

### Basic Usage

```python
import rootsense

# Initialize
rootsense.init(
    api_key="your-api-key",
    project_id="your-project",
    environment="production"
)

# Or with connection string
rootsense.init(
    connection_string="rootsense://key@api.rootsense.ai/project"
)

# Capture exceptions
try:
    1 / 0
except Exception as e:
    rootsense.capture_exception(e)
```

### Auto-Instrumentation

Auto-instrumentation is **enabled by default** and leverages OpenTelemetry to automatically capture:

- **Django**: ORM queries, HTTP requests, middleware, views
- **Flask**: HTTP requests, routes
- **SQLAlchemy**: Database queries
- **HTTP Libraries**: requests, httpx, urllib
- **Redis**: All Redis operations
- **Celery**: Task execution

No manual instrumentation needed! Just initialize RootSense:

```python
import rootsense

# Auto-instrumentation happens automatically
rootsense.init(
    api_key="your-api-key",
    project_id="your-project"
)

# All Django ORM queries, HTTP requests, etc. are now automatically tracked!
```

To disable auto-instrumentation:

```python
rootsense.init(
    api_key="your-api-key",
    project_id="your-project",
    auto_instrumentation=False
)
```

### Django Integration

```python
# settings.py
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project",
    environment="production"
)

MIDDLEWARE = [
    # ... other middleware
    'rootsense.middleware.django.DjangoMiddleware',
]
```

With auto-instrumentation enabled, all Django ORM queries are automatically captured and sent to RootSense!

### Flask Integration

```python
from flask import Flask
import rootsense

app = Flask(__name__)

# Initialize RootSense
rootsense.init(
    api_key="your-api-key",
    project_id="your-project"
)

# Add middleware
from rootsense.middleware.flask import FlaskMiddleware
FlaskMiddleware(app)

@app.route("/")
def index():
    return "Hello World"
```

### FastAPI Integration

```python
from fastapi import FastAPI
import rootsense

app = FastAPI()

# Initialize RootSense
rootsense.init(
    api_key="your-api-key",
    project_id="your-project"
)

# Add middleware
from rootsense.middleware.fastapi import FastAPIMiddleware
app.add_middleware(FastAPIMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Configuration

### Connection String Format

```python
rootsense://api_key@host/project_id
```

Example:
```python
rootsense.init(
    connection_string="rootsense://abc123@api.rootsense.ai/my-project"
)
```

### Environment Variables

```bash
export ROOTSENSE_API_KEY="your-api-key"
export ROOTSENSE_PROJECT_ID="your-project"
export ROOTSENSE_ENVIRONMENT="production"
export ROOTSENSE_BASE_URL="https://api.rootsense.ai"
```

Then simply:
```python
import rootsense
rootsense.init()  # Reads from environment variables
```

### Configuration Options

```python
rootsense.init(
    api_key="your-api-key",              # Required
    project_id="your-project",            # Required
    base_url="https://api.rootsense.ai", # Optional
    environment="production",              # Optional, default: "production"
    sanitize_pii=True,                     # Optional, default: True
    debug=False,                           # Optional, default: False
    auto_instrumentation=True              # Optional, default: True
)
```

## Context and Tags

```python
from rootsense import context

# Set user context
context.set_user(
    user_id="123",
    email="user@example.com",
    username="john_doe"
)

# Add tags
context.set_tag("environment", "production")
context.set_tag("version", "1.0.0")

# Add extra context
context.set_context("custom_data", {"key": "value"})

# Add breadcrumbs
context.push_breadcrumb(
    message="User clicked button",
    category="user-action",
    level="info"
)
```

## What Gets Automatically Captured?

With auto-instrumentation enabled (default), RootSense automatically captures:

### Django
- All ORM database queries (SELECT, INSERT, UPDATE, DELETE)
- HTTP request/response data
- View execution
- Middleware execution
- Template rendering

### Flask
- HTTP request/response data
- Route execution
- Before/after request hooks

### Database (via SQLAlchemy or Django ORM)
- Query text
- Query duration
- Database name
- Operation type

### HTTP Requests
- Outgoing HTTP calls via requests, httpx, or urllib
- Request method, URL, headers
- Response status, duration

### Redis
- All Redis commands
- Command duration
- Connection info

### Celery
- Task execution
- Task duration
- Task arguments
- Worker info

## Manual Instrumentation

If you need more control, you can still manually instrument your code:

```python
from rootsense.performance import DatabaseMonitor, PerformanceMonitor

# Track database queries
db_monitor = DatabaseMonitor()
with db_monitor.track_query(
    "SELECT * FROM users WHERE id = %s",
    operation="SELECT",
    database="main"
):
    # Execute query
    pass

# Track custom operations
perf_monitor = PerformanceMonitor()
with perf_monitor.track("custom_operation"):
    # Your code here
    pass
```

## License

MIT

## Support

- Documentation: https://docs.rootsense.ai
- Issues: https://github.com/paschmaria/rootsense-python-sdk/issues
- Email: support@rootsense.ai
