# RootSense Python SDK

[![PyPI version](https://badge.fury.io/py/rootsense.svg)](https://badge.fury.io/py/rootsense)
[![Python Support](https://img.shields.io/pypi/pyversions/rootsense.svg)](https://pypi.org/project/rootsense/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for RootSense - AI-powered incident management that automatically detects, analyzes, and resolves errors in your applications.

## Features

- 🚀 **Automatic Error Detection**: Captures exceptions and errors automatically
- 🔍 **OpenTelemetry Integration**: Auto-instruments Django ORM, SQLAlchemy, HTTP clients, Redis, Celery
- ✅ **Auto-Resolution**: Automatically detects when incidents are resolved
- 🎯 **Smart Fingerprinting**: Groups similar errors intelligently
- 📊 **Built-in Metrics**: Prometheus-compatible metrics included
- 🔒 **PII Sanitization**: Automatically removes sensitive data
- 🌐 **Framework Support**: Django, Flask, FastAPI
- ⚡ **High Performance**: Minimal overhead, async event processing

## Installation

### Basic Installation

```bash
pip install rootsense
```

### With Auto-Instrumentation (Recommended)

```bash
# Install with OpenTelemetry auto-instrumentation
pip install rootsense[instrumentation]

# Or with specific framework
pip install rootsense[django,instrumentation]
pip install rootsense[flask,instrumentation]
pip install rootsense[fastapi,instrumentation]

# Or everything
pip install rootsense[all]
```

## Quick Start

### Initialize SDK

```python
import rootsense

# Initialize with auto-instrumentation (recommended)
rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production",
    service_name="my-app",              # Optional: auto-detected
    enable_auto_instrumentation=True    # Default: True
)
```

That's it! RootSense now automatically:
- Captures all exceptions
- Tracks database queries (Django ORM, SQLAlchemy)
- Monitors HTTP requests (requests, httpx, urllib)
- Tracks Redis operations
- Monitors Celery tasks
- Auto-resolves incidents when operations recover

### Manual Error Capture

```python
import rootsense

try:
    risky_operation()
except Exception as e:
    rootsense.capture_exception(e, context={
        "user_id": "12345",
        "action": "checkout"
    })
```

## Framework Integration

### Django

```python
# settings.py
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-django-app"
)

# That's all! No middleware needed.
# Auto-instruments:
# - HTTP requests
# - Django ORM queries
# - Template rendering
# - Middleware operations
```

### Flask

```python
from flask import Flask
import rootsense

app = Flask(__name__)

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-flask-app"
)

# Auto-instruments:
# - HTTP requests
# - SQLAlchemy queries
# - External HTTP calls
```

### FastAPI

```python
from fastapi import FastAPI
import rootsense

app = FastAPI()

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-fastapi-app"
)

# Auto-instruments:
# - HTTP requests
# - Database operations
# - Background tasks
# - Dependencies
```

## Auto-Resolution

RootSense automatically detects when incidents are resolved:

```python
# Error occurs: Database connection timeout
# Fingerprint: "db:postgresql:SELECT:users"
# → Incident created in RootSense

# After database is restored:
# SELECT queries succeed
# → Success signals sent automatically
# → Incident auto-resolved
```

Works for:
- ✅ HTTP endpoints
- ✅ Database queries
- ✅ Redis operations
- ✅ Celery tasks
- ✅ Any OpenTelemetry span

See [Auto-Resolution Guide](docs/AUTO_RESOLUTION.md) for details.

## Configuration

### Environment Variables

```bash
export ROOTSENSE_API_KEY="your-api-key"
export ROOTSENSE_PROJECT_ID="your-project-id"
export ROOTSENSE_ENVIRONMENT="production"
```

```python
import rootsense

# Reads from environment variables
rootsense.init()
```

### Connection String

```python
import rootsense

rootsense.init(
    connection_string="rootsense://api-key@api.rootsense.ai/project-id"
)
```

### Full Configuration

```python
import rootsense

rootsense.init(
    # Required
    api_key="your-api-key",
    project_id="your-project-id",
    
    # Optional
    backend_url="https://api.rootsense.ai",  # Default
    environment="production",                 # production, staging, development
    service_name="my-service",                # Auto-detected if not provided
    service_version="1.0.0",                  # Optional
    
    # Auto-instrumentation
    enable_auto_instrumentation=True,         # Default: True
    
    # Performance
    sample_rate=1.0,                          # 0.0 to 1.0
    buffer_size=1000,                         # Event buffer size
    max_breadcrumbs=100,                      # Breadcrumb limit
    
    # Privacy
    sanitize_pii=True,                        # Auto-remove PII
    
    # Debugging
    debug=False                               # Enable debug logging
)
```

## What Gets Instrumented

With `enable_auto_instrumentation=True` (default):

### Web Frameworks
- Django (HTTP, ORM, templates, middleware)
- Flask (HTTP, SQLAlchemy)
- FastAPI (HTTP, dependencies, background tasks)

### Database
- Django ORM (all queries)
- SQLAlchemy (all queries)
- Captures: query text, duration, table name

### HTTP Clients
- requests library
- httpx (sync and async)
- urllib (stdlib)
- Captures: URL, method, status, duration

### Caching & Queues
- Redis (all commands)
- Celery (tasks, retries)
- Captures: operation name, duration

### Processes
- Subprocess execution
- Shell commands

See [OpenTelemetry Integration Guide](docs/OPENTELEMETRY_INTEGRATION.md) for details.

## Advanced Usage

### Custom Context

```python
import rootsense

client = rootsense.get_client()
client.error_collector.add_breadcrumb(
    message="User clicked checkout",
    category="user.action",
    level="info"
)

client.error_collector.set_tag("user.tier", "premium")
client.error_collector.set_context("payment", {
    "method": "credit_card",
    "last4": "4242"
})
```

### Disable Auto-Instrumentation

If you prefer manual control:

```python
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    enable_auto_instrumentation=False  # Disable
)

# Now only manually captured errors are sent
try:
    risky_operation()
except Exception as e:
    rootsense.capture_exception(e)
```

### Custom OpenTelemetry Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_data(data):
    with tracer.start_as_current_span("data_processing") as span:
        span.set_attribute("data.size", len(data))
        span.set_attribute("user.id", "12345")
        
        result = expensive_operation(data)
        
        span.set_attribute("result.count", len(result))
        return result
```

These custom spans are automatically captured by RootSense!

## Migration from v0.0.x

Upgrading from an earlier version? See our [Migration Guide](docs/MIGRATION_GUIDE.md).

Key changes:
- ✅ OpenTelemetry auto-instrumentation (no manual tracking needed)
- ✅ Auto-resolution for all operation types
- ❌ Removed `PrometheusCollector` (metrics now automatic)
- ❌ Removed manual database monitoring
- ✅ Simplified configuration

## Documentation

- [Auto-Resolution Guide](docs/AUTO_RESOLUTION.md)
- [OpenTelemetry Integration](docs/OPENTELEMETRY_INTEGRATION.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)
- [API Documentation](https://docs.rootsense.ai/python)

## Performance

RootSense is designed for production:
- **CPU Overhead**: ~1-2%
- **Memory**: ~10-20MB
- **Network**: Batched, compressed events
- **Async**: Non-blocking event processing

## Requirements

- Python 3.8+
- Optional: OpenTelemetry packages for auto-instrumentation

## Support

- 📧 Email: support@rootsense.ai
- 🐛 Issues: [GitHub Issues](https://github.com/paschmaria/rootsense-python-sdk/issues)
- 📚 Docs: [docs.rootsense.ai](https://docs.rootsense.ai)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
