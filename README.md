# RootSense Python SDK

[![Python Version](https://img.shields.io/pypi/pyversions/rootsense)](https://pypi.org/project/rootsense/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python SDK for [RootSense](https://rootsense.ai) - AI-powered incident management and error tracking platform that automatically detects, analyzes, and provides actionable recommendations for production issues.

## Features

- 🚨 **Automatic Error Tracking** - Capture and report exceptions with full stack traces
- 📊 **Prometheus Integration** - Built-in metrics collection and monitoring
- 🔍 **Rich Context** - Automatic capture of request data, user info, and custom context
- 🛡️ **PII Protection** - Configurable data sanitization to protect sensitive information
- ⚡ **Async Transport** - Non-blocking error reporting with buffering and retry logic
- 🔌 **Framework Support** - Native integrations for Flask, FastAPI, and Django
- 🎯 **Fingerprinting** - Smart error grouping based on stack traces and context
- 💾 **Buffered Delivery** - Reliable event delivery with automatic retries

## Installation

### Basic Installation

```bash
pip install rootsense
```

### With Framework Support

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

### 1. Initialize the SDK

```python
import rootsense

rootsense.init(
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)
```

### 2. Capture Exceptions

```python
try:
    # Your code here
    result = risky_operation()
except Exception as e:
    rootsense.capture_exception(e)
    # Handle the exception
```

### 3. Add Context

```python
# Set user information
rootsense.set_user(
    id="user-123",
    email="user@example.com",
    username="johndoe"
)

# Add custom tags
rootsense.set_tag("payment_type", "credit_card")
rootsense.set_tag("plan", "premium")

# Add breadcrumbs for debugging
rootsense.push_breadcrumb(
    message="User clicked checkout",
    category="navigation",
    level="info"
)
```

## Framework Integrations

### Flask

```python
from flask import Flask
from rootsense.integrations.flask import RootSenseFlask

app = Flask(__name__)

# Initialize RootSense for Flask
RootSenseFlask(
    app,
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
```

### FastAPI

```python
from fastapi import FastAPI
from rootsense.integrations.fastapi import RootSenseFastAPI

app = FastAPI()

# Initialize RootSense for FastAPI
RootSenseFastAPI(
    app,
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### Django

Add to your `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'rootsense.integrations.django.RootSenseDjangoMiddleware',
]

ROOTSENSE = {
    'api_key': 'your-api-key',
    'project_id': 'your-project-id',
    'environment': 'production',
    'send_default_pii': False,
}
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | str | **Required** | Your RootSense API key |
| `project_id` | str | **Required** | Your project ID |
| `api_url` | str | `https://api.rootsense.ai` | RootSense API endpoint |
| `environment` | str | `production` | Environment name (production, staging, etc.) |
| `release` | str | `None` | Application version/release |
| `server_name` | str | Auto-detected | Server hostname |
| `enable_prometheus` | bool | `True` | Enable Prometheus metrics collection |
| `send_default_pii` | bool | `False` | Automatically send PII (emails, IPs, usernames) |
| `max_breadcrumbs` | int | `100` | Maximum number of breadcrumbs to store |
| `sample_rate` | float | `1.0` | Sample rate for events (0.0 to 1.0) |
| `debug` | bool | `False` | Enable debug logging |
| `buffer_size` | int | `1000` | Maximum events in buffer before dropping |
| `flush_interval` | float | `5.0` | Seconds between buffer flushes |
| `max_retries` | int | `3` | Maximum retry attempts for failed requests |
| `timeout` | float | `10.0` | Request timeout in seconds |

### Environment Variables

You can also configure the SDK using environment variables:

```bash
export ROOTSENSE_API_KEY="your-api-key"
export ROOTSENSE_PROJECT_ID="your-project-id"
export ROOTSENSE_ENVIRONMENT="production"
export ROOTSENSE_DEBUG="false"
```

## Advanced Usage

### Manual Client Management

```python
from rootsense import RootSenseClient
from rootsense.config import Config

config = Config(
    api_key="your-api-key",
    project_id="your-project-id",
    environment="production"
)

client = RootSenseClient(config)

try:
    # Your code
    pass
except Exception as e:
    client.capture_exception(e)
finally:
    client.close()
```

### Context Managers

```python
with rootsense.configure_scope() as scope:
    scope.set_tag("transaction_id", "txn-12345")
    scope.set_context("payment", {
        "amount": 99.99,
        "currency": "USD"
    })
    
    # Any errors here will include this context
    process_payment()
```

### Custom Fingerprinting

```python
rootsense.capture_exception(
    exception,
    fingerprint=["custom", "grouping", "key"]
)
```

### Capture Messages

```python
# Log a message with level
rootsense.capture_message(
    "Payment processed successfully",
    level="info",
    extra={"transaction_id": "txn-12345"}
)
```

## Prometheus Metrics

When `enable_prometheus=True`, the SDK automatically collects:

- **Request metrics**: `http_requests_total`, `http_request_duration_seconds`
- **Error metrics**: `errors_total`, `error_rate`
- **System metrics**: `process_cpu_seconds_total`, `process_resident_memory_bytes`

Access metrics at `/metrics` endpoint (framework-dependent).

## Best Practices

### 1. Initialize Early

Initialize RootSense as early as possible in your application lifecycle:

```python
# In your main application file
import rootsense

rootsense.init(api_key="...", project_id="...")

# Then import your application code
from myapp import create_app
```

### 2. Use Context Wisely

Add context that helps diagnose issues:

```python
rootsense.set_user(id=user.id, email=user.email)
rootsense.set_tag("feature_flag", get_feature_flag())
rootsense.set_tag("ab_test_variant", get_variant())
```

### 3. Sanitize Sensitive Data

```python
rootsense.init(
    api_key="...",
    project_id="...",
    send_default_pii=False,  # Don't send PII by default
    before_send=lambda event: sanitize_event(event)
)
```

### 4. Use Sampling in High-Traffic Apps

```python
rootsense.init(
    api_key="...",
    project_id="...",
    sample_rate=0.1  # Sample 10% of events
)
```

### 5. Close on Shutdown

Ensure events are flushed on application shutdown:

```python
import atexit
from rootsense import get_client

def cleanup():
    client = get_client()
    if client:
        client.close()

atexit.register(cleanup)
```

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- [Flask application](examples/flask_app.py)
- [FastAPI application](examples/fastapi_app.py)
- [Django application](examples/django_app/)
- [Basic usage](examples/basic_usage.py)
- [Advanced features](examples/advanced_usage.py)

## Troubleshooting

### Events Not Appearing

1. **Check API credentials**: Verify your API key and project ID
2. **Enable debug mode**: Set `debug=True` to see SDK logs
3. **Check network**: Ensure your application can reach `api.rootsense.ai`
4. **Verify initialization**: Make sure `rootsense.init()` is called before errors occur

### High Memory Usage

1. **Reduce buffer size**: Set a lower `buffer_size`
2. **Increase flush interval**: Flush more frequently with lower `flush_interval`
3. **Enable sampling**: Use `sample_rate` to reduce event volume

### Missing Context

1. **Initialize client early**: Call `init()` at application startup
2. **Set context before errors**: Context must be set before exception occurs
3. **Check scope**: Context is thread-local by default

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- 📧 Email: support@rootsense.ai
- 💬 Slack: [Join our community](https://rootsense.ai/slack)
- 📖 Documentation: [docs.rootsense.ai](https://docs.rootsense.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/paschmaria/rootsense-python-sdk/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [RootSense Node.js SDK](https://github.com/paschmaria/rootsense-node-sdk)
- [RootSense Platform](https://rootsense.ai)
