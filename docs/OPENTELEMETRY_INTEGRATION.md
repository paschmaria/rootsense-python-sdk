# OpenTelemetry Integration

RootSense uses OpenTelemetry for automatic instrumentation of your application.

## What Gets Instrumented

When you enable auto-instrumentation, RootSense automatically captures:

### Web Frameworks
- **Django**: HTTP requests, ORM queries, middleware operations
- **Flask**: HTTP requests, template rendering, database queries
- **FastAPI**: HTTP requests, dependencies, background tasks

### Database Operations
- **Django ORM**: All database queries with timing and parameters
- **SQLAlchemy**: All database operations across any supported database
- Captures: query text, duration, database name, table name

### HTTP Client Requests
- **requests**: All HTTP calls made with requests library
- **httpx**: All HTTP calls made with httpx (sync and async)
- **urllib**: Standard library HTTP requests
- Captures: URL, method, status code, duration

### Caching & Queue Operations
- **Redis**: All Redis commands (GET, SET, DEL, etc.)
- **Celery**: Task execution, delays, retries
- Captures: command/task name, arguments, duration

### Subprocess Operations
- Spawned subprocesses and shell commands
- Exit codes and execution time

## Installation

### Basic Installation
```bash
pip install rootsense
```

### With Auto-Instrumentation
```bash
# Install with all instrumentation packages
pip install rootsense[instrumentation]

# Or install specific frameworks
pip install rootsense[django]  # Django only
pip install rootsense[flask]   # Flask only
pip install rootsense[fastapi] # FastAPI only
```

## Usage

### Automatic (Recommended)

Simply initialize RootSense at your application startup:

```python
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    enable_auto_instrumentation=True,  # Default: True
    service_name="my-api",              # Optional: auto-detected
    service_version="1.0.0",            # Optional
    environment="production"             # Default: production
)
```

That's it! All supported libraries are automatically instrumented.

### Django Example

```python
# settings.py
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-django-app"
)

# Automatically captures:
# - HTTP requests to all views
# - Database queries via Django ORM  
# - Template rendering
# - Middleware operations
```

### Flask Example

```python
# app.py
from flask import Flask
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-flask-app"
)

app = Flask(__name__)

# Automatically captures:
# - HTTP requests to all routes
# - Database queries via SQLAlchemy
# - External HTTP calls via requests
```

### FastAPI Example

```python
# main.py
from fastapi import FastAPI
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    service_name="my-fastapi-app"
)

app = FastAPI()

# Automatically captures:
# - HTTP requests to all endpoints
# - Database queries
# - Background tasks
# - Dependency injections
```

## How It Works

### Custom OpenTelemetry Exporters

RootSense implements custom OpenTelemetry exporters that:

1. **Capture spans**: All operations create OpenTelemetry spans
2. **Convert to RootSense format**: Spans are converted to our event format
3. **Track auto-resolution**: Success/failure tracked for incident management
4. **Batch and send**: Events are batched and sent to RootSense backend

### Data Flow

```
Your App → OpenTelemetry → RootSense Exporter → RootSense Backend
              ↓                      ↓                    ↓
         Instruments           Converts            Analyzes
         operations            to events           incidents
```

### What Gets Sent

For each operation:
- **Operation type**: HTTP, DB, Redis, etc.
- **Name/route**: Endpoint, query, command
- **Duration**: How long it took
- **Status**: Success or failure
- **Attributes**: Method, parameters, table name, etc.
- **Trace context**: Parent/child relationships

## Configuration Options

```python
import rootsense

rootsense.init(
    # Required
    api_key="your-api-key",
    project_id="your-project-id",
    
    # Auto-instrumentation (default: True)
    enable_auto_instrumentation=True,
    
    # Service identification
    service_name="my-service",      # Auto-detected if not provided
    service_version="1.0.0",        # Optional
    environment="production",       # production, staging, development
    
    # Sampling and performance
    sample_rate=1.0,                # 0.0 to 1.0 (1.0 = capture everything)
    
    # Privacy
    sanitize_pii=True,              # Auto-remove PII from data
    
    # Debugging
    debug=False                     # Enable debug logging
)
```

## Disabling Auto-Instrumentation

If you prefer manual instrumentation:

```python
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    enable_auto_instrumentation=False  # Disable auto-instrumentation
)

# Now only manually captured errors are sent
try:
    # Your code
    pass
except Exception as e:
    rootsense.capture_exception(e)
```

## Performance Impact

OpenTelemetry instrumentation is designed for production use:

- **Minimal overhead**: ~1-2% CPU increase
- **Asynchronous**: Events sent in background
- **Batched**: Multiple events sent together
- **Sampling**: Can reduce sampling rate if needed

## Troubleshooting

### No traces appearing?

1. **Check installation**:
   ```bash
   pip install rootsense[instrumentation]
   ```

2. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   rootsense.init(..., debug=True)
   ```

3. **Verify initialization**:
   ```python
   client = rootsense.init(...)
   print(f"Initialized: {client is not None}")
   ```

### Framework not detected?

Make sure the framework is installed before calling `rootsense.init()`:

```python
# ❌ Wrong order
import rootsense
rootsense.init(...)
import django  # Too late!

# ✅ Correct order
import django
import rootsense
rootsense.init(...)  # Will detect Django
```

## Advanced: Custom Instrumentation

You can add custom spans alongside auto-instrumentation:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def my_function():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("user.id", "12345")
        span.set_attribute("operation.type", "data_processing")
        
        # Your code here
        result = process_data()
        
        span.set_attribute("result.count", len(result))
        return result
```

These custom spans will also be captured by RootSense!
