# RootSense Python SDK

[![PyPI version](https://badge.fury.io/py/rootsense.svg)](https://badge.fury.io/py/rootsense)
[![Python versions](https://img.shields.io/pypi/pyversions/rootsense.svg)](https://pypi.org/project/rootsense/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python SDK for RootSense - AI-powered incident management and error tracking platform.

## Features

- 🚨 **Automatic Error Tracking**: Capture exceptions and errors automatically
- 📊 **Performance Monitoring**: Track request timing, database queries, and custom operations
- 🔍 **Distributed Tracing**: Monitor requests across microservices
- 🎯 **Context Enrichment**: Automatic user, request, and environment context
- 🔌 **Framework Integrations**: Native support for Flask, FastAPI, Django, and more
- ⚡ **Async Support**: Full async/await support for modern Python applications
- 🛡️ **PII Protection**: Built-in data sanitization and sensitive data redaction

## Installation

```bash
pip install rootsense
```

### Framework-Specific Installation

```bash
# For Flask
pip install rootsense[flask]

# For FastAPI
pip install rootsense[fastapi]

# For Django
pip install rootsense[django]

# For development
pip install rootsense[dev]
```

## Quick Start

### Basic Usage

```python
import rootsense

# Initialize RootSense
rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

# Capture an exception
try:
    1 / 0
except Exception as e:
    rootsense.capture_exception(e)

# Capture a message
rootsense.capture_message("User login successful", level="info")
```

### Flask Integration

```python
from flask import Flask
import rootsense
from rootsense.integrations.flask import capture_flask_errors

app = Flask(__name__)

# Initialize RootSense
rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id"
)

# Add RootSense middleware
capture_flask_errors(app)

@app.route("/")
def index():
    return "Hello World!"
```

### FastAPI Integration

```python
from fastapi import FastAPI
import rootsense
from rootsense.integrations.fastapi import capture_fastapi_errors

app = FastAPI()

# Initialize RootSense
rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id"
)

# Add RootSense middleware
capture_fastapi_errors(app)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}
```

### Django Integration

```python
# In your settings.py

from rootsense.integrations.django import init_django

# Initialize RootSense
init_django(
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

# Add middleware
MIDDLEWARE = [
    # ... other middleware
    'rootsense.integrations.django.DjangoMiddleware',
]
```

## Advanced Features

### Performance Monitoring

```python
from rootsense.performance import PerformanceMonitor, track_performance

monitor = PerformanceMonitor()

# Using context manager
with monitor.track("database_query", query_type="SELECT"):
    # Your code here
    result = db.query("SELECT * FROM users")

# Using decorator
@track_performance("api_call", service="external_api")
def call_external_api():
    # API call code
    pass
```

### Distributed Tracing

```python
from rootsense.tracing import get_tracer, trace_function

tracer = get_tracer()

# Using context manager
with tracer.trace("user_service.get_user") as span:
    user = get_user_from_db(user_id)
    span.set_tag("user_id", user_id)
    span.set_tag("found", user is not None)

# Using decorator
@trace_function("payment_service.process_payment")
def process_payment(amount, currency):
    # Payment processing code
    pass
```

### Database Monitoring

```python
from rootsense.performance import DatabaseMonitor

db_monitor = DatabaseMonitor()

with db_monitor.track_query(
    "SELECT * FROM users WHERE id = %s",
    operation="SELECT",
    database="main"
):
    result = cursor.execute(query, (user_id,))

# Get statistics
stats = db_monitor.get_stats()
print(f"Total queries: {stats['query_count']}")
print(f"Average time: {stats['average_time']:.2f}s")
```

### Context Management

```python
from rootsense import set_user, set_tag, set_context, push_breadcrumb

# Set user context
set_user({
    "id": "user-123",
    "email": "user@example.com",
    "username": "john_doe"
})

# Add custom tags
set_tag("environment", "production")
set_tag("version", "1.2.3")

# Add custom context
set_context("payment", {
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card"
})

# Add breadcrumbs for debugging
push_breadcrumb(
    category="auth",
    message="User logged in",
    level="info"
)
```

## Configuration

### Environment Variables

You can configure RootSense using environment variables:

```bash
export ROOTSENSE_API_KEY="your-api-key"
export ROOTSENSE_PROJECT_ID="your-project-id"
export ROOTSENSE_ENVIRONMENT="production"
export ROOTSENSE_DEBUG="false"
```

Then initialize without parameters:

```python
import rootsense

rootsense.init()  # Reads from environment variables
```

### Configuration Options

```python
rootsense.init(
    api_key="your-api-key",              # Required: Your API key
    project_id="your-project-id",        # Required: Your project ID
    environment="production",             # Optional: Environment name
    backend_url="https://api.rootsense.ai",  # Optional: Backend URL
    debug=False,                          # Optional: Enable debug logging
    enable_prometheus=True,               # Optional: Enable Prometheus metrics
    send_default_pii=False,               # Optional: Send PII by default
    sample_rate=1.0,                      # Optional: Error sampling rate (0.0-1.0)
    max_breadcrumbs=100,                  # Optional: Max breadcrumbs to store
    buffer_size=1000,                     # Optional: Event buffer size
)
```

## Examples

See the [examples](./examples) directory for complete working examples:

- [Flask Example](./examples/flask_app.py)
- [FastAPI Example](./examples/fastapi_app.py)
- [Django Example](./examples/django_app/)
- [Performance Monitoring](./examples/performance_example.py)
- [Distributed Tracing](./examples/tracing_example.py)

## Testing

Run tests with pytest:

```bash
pip install rootsense[dev]
pytest

# With coverage
pytest --cov=rootsense --cov-report=html
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Links

- [Documentation](https://docs.rootsense.ai)
- [Homepage](https://rootsense.ai)
- [PyPI](https://pypi.org/project/rootsense/)
- [GitHub](https://github.com/paschmaria/rootsense-python-sdk)
- [Issues](https://github.com/paschmaria/rootsense-python-sdk/issues)

## Support

For support, email support@rootsense.ai or join our [Discord community](https://discord.gg/rootsense).
