# RootSense Python SDK

[![PyPI version](https://badge.fury.io/py/rootsense.svg)](https://badge.fury.io/py/rootsense)
[![Python versions](https://img.shields.io/pypi/pyversions/rootsense.svg)](https://pypi.org/project/rootsense/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python SDK for RootSense - AI-powered incident management and error tracking platform.

## Features

- 🚨 **Automatic Error Tracking**: Capture exceptions and errors automatically
- 📊 **Performance Monitoring**: Track request timing with built-in Prometheus metrics
- 🔍 **Distributed Tracing**: Monitor requests across microservices
- 🎯 **Context Enrichment**: Automatic user, request, and environment context
- 🔌 **Framework Integrations**: Native support for Flask, FastAPI, Django
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

# Or use connection string
rootsense.init(
    connection_string="rootsense://your-api-key@api.rootsense.ai/your-project-id"
)

# Or use environment variables
# ROOTSENSE_API_KEY=your-api-key
# ROOTSENSE_PROJECT_ID=your-project-id
rootsense.init()  # Auto-reads from environment

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
from rootsense.middleware.flask import capture_flask_errors

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
from rootsense.middleware.fastapi import capture_fastapi_errors

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

## Advanced Features

### Context Management

```python
from rootsense.context import set_user, set_tag, set_context, add_breadcrumb

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
add_breadcrumb(
    category="auth",
    message="User logged in",
    data={"method": "oauth"}
)
```

### Manual Error Tracking

```python
import rootsense

# Capture exception with context
try:
    process_payment(user_id, amount)
except PaymentError as e:
    rootsense.capture_exception(
        e,
        context={
            "service": "payment",
            "endpoint": "/api/payment",
            "user_id": user_id,
            "amount": amount
        }
    )
```

## Configuration

### Connection String Format

```python
rootsense.init(
    connection_string="rootsense://API_KEY@HOST/PROJECT_ID"
)

# Example:
rootsense.init(
    connection_string="rootsense://abc123@api.rootsense.ai/proj-456"
)
```

### Environment Variables

```bash
export ROOTSENSE_API_KEY="your-api-key"
export ROOTSENSE_PROJECT_ID="your-project-id"
export ROOTSENSE_BACKEND_URL="https://api.rootsense.ai"  # optional
```

### Configuration Options

```python
rootsense.init(
    api_key="your-api-key",          # Required: Your API key
    project_id="your-project-id",    # Required: Your project ID
    backend_url="https://api.rootsense.ai",  # Optional
    environment="production",         # Optional: Environment name
    debug=False,                      # Optional: Enable debug logging
    sanitize_pii=True,                # Optional: Auto-sanitize PII
    sample_rate=1.0,                  # Optional: Error sampling (0.0-1.0)
    max_breadcrumbs=100,              # Optional: Max breadcrumbs to store
    buffer_size=1000,                 # Optional: Event buffer size
)
```

## Testing

Run tests with pytest:

```bash
pip install -e ".[dev]"
pytest

# With coverage
pytest --cov=rootsense --cov-report=html
```

## License

MIT License - see [LICENSE](./LICENSE) file

## Links

- [Documentation](https://docs.rootsense.ai)
- [Homepage](https://rootsense.ai)
- [Issues](https://github.com/paschmaria/rootsense-python-sdk/issues)
