# Auto-Resolution Feature

RootSense automatically detects when incidents are resolved by tracking successful operations after errors occur.

## How It Works

### 1. Error Detection
When an error occurs, RootSense:
- Captures the error details
- Generates a unique fingerprint based on:
  - **HTTP requests**: `http:{method}:{route}`
  - **Database queries**: `db:{system}:{operation}:{table}`
  - **Redis operations**: `redis:{command}`
  - **Celery tasks**: `celery:{task_name}`
- Creates an incident in the backend

### 2. Success Tracking
After an error, RootSense monitors subsequent operations:
- Tracks successful completions for the same fingerprint
- Sends success signals to the backend
- Works for ALL operation types (HTTP, DB, Redis, Celery, etc.)

### 3. Automatic Resolution
When the backend receives success signals:
- Validates the operation is consistently succeeding
- Automatically marks the incident as resolved
- Notifies relevant team members

## Examples

### HTTP Endpoint Recovery
```python
import rootsense

rootsense.init(
    api_key="your-key",
    project_id="your-project",
    enable_auto_instrumentation=True
)

# Error occurs
# Fingerprint: "http:GET:/api/users"
# Incident created

# After fix is deployed:
# GET /api/users succeeds
# Success signal sent automatically
# Incident auto-resolved
```

### Database Query Recovery
```python
# Error: Database connection timeout
# Fingerprint: "db:postgresql:SELECT:users"
# Incident created

# After database is restored:
# SELECT queries succeed
# Success signals sent automatically via OpenTelemetry
# Incident auto-resolved
```

### Redis Operation Recovery
```python
# Error: Redis connection refused
# Fingerprint: "redis:GET"
# Incident created

# After Redis is restarted:
# Redis GET commands succeed
# Success signals sent automatically
# Incident auto-resolved
```

## Configuration

Auto-resolution is enabled by default with OpenTelemetry instrumentation:

```python
import rootsense

# Auto-resolution enabled (default)
rootsense.init(
    api_key="your-key",
    project_id="your-project",
    enable_auto_instrumentation=True  # Default
)

# Disable auto-instrumentation (no auto-resolution)
rootsense.init(
    api_key="your-key",
    project_id="your-project",
    enable_auto_instrumentation=False
)
```

## Supported Operations

Auto-resolution works for:

✅ **HTTP Requests** (via Django, Flask, FastAPI middleware)
✅ **Database Queries** (via Django ORM, SQLAlchemy)
✅ **HTTP Client Requests** (via requests, httpx, urllib)
✅ **Redis Operations** (via redis-py)
✅ **Celery Tasks** (via Celery instrumentation)
✅ **Generic Operations** (via OpenTelemetry spans)

## Best Practices

1. **Deploy fixes gradually**: Auto-resolution requires consistent success signals
2. **Monitor resolution time**: Check backend dashboard for resolution metrics
3. **Use meaningful operation names**: Helps with accurate fingerprinting
4. **Enable for production**: Most valuable in production environments

## Troubleshooting

### Incident not auto-resolving?

**Check:**
1. Auto-instrumentation is enabled
2. OpenTelemetry packages are installed: `pip install rootsense[instrumentation]`
3. Operations are succeeding consistently
4. Fingerprints match (check backend logs)

**Debug:**
```python
import rootsense
import logging

logging.basicConfig(level=logging.DEBUG)

rootsense.init(
    api_key="your-key",
    project_id="your-project",
    debug=True  # Enable debug logging
)
```

### Manual resolution

You can always manually resolve incidents via the RootSense dashboard if auto-resolution doesn't work as expected.
