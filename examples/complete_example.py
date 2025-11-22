"""Complete example showing RootSense with OpenTelemetry auto-instrumentation.

This example demonstrates:
1. SDK initialization with auto-instrumentation
2. Automatic error detection and capture
3. Auto-resolution when operations recover
4. Database query tracking (automatic)
5. HTTP request tracking (automatic)
6. Redis operation tracking (automatic)
"""

import time
import logging
import rootsense

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.INFO)

# Initialize RootSense with auto-instrumentation
print("\n=== Initializing RootSense ===")
rootsense.init(
    api_key="demo-api-key",
    project_id="demo-project",
    environment="development",
    service_name="demo-app",
    service_version="1.0.0",
    enable_auto_instrumentation=True,  # Enables OpenTelemetry
    debug=True  # See what's being captured
)

print("\u2705 RootSense initialized with auto-instrumentation")
print("   - Django ORM queries: auto-tracked")
print("   - SQLAlchemy queries: auto-tracked")
print("   - HTTP requests (requests, httpx): auto-tracked")
print("   - Redis operations: auto-tracked")
print("   - Celery tasks: auto-tracked")
print("   - Auto-resolution: enabled for all operation types")


# Example 1: Manual error capture
print("\n=== Example 1: Manual Error Capture ===")
try:
    result = 1 / 0
except ZeroDivisionError as e:
    event_id = rootsense.capture_exception(e, context={
        "operation": "division",
        "user_id": "12345"
    })
    print(f"✅ Error captured: {event_id}")
    print(f"   Fingerprint: error:ZeroDivisionError:division")
    print(f"   → Incident created in RootSense")


# Example 2: Simulated database error and recovery
print("\n=== Example 2: Database Error & Auto-Resolution ===")

print("\n📊 Simulating database connection error...")
try:
    # Simulate a database error
    raise Exception("Database connection timeout: postgresql://db:5432")
except Exception as e:
    event_id = rootsense.capture_exception(e, context={
        "operation_type": "db",
        "database": "postgresql",
        "query": "SELECT * FROM users",
        "table": "users"
    })
    print(f"❌ Error captured: {event_id}")
    print(f"   Fingerprint: db:postgresql:SELECT:users")
    print(f"   → Incident created")

print("\n⏳ Waiting 2 seconds (simulating fix deployment)...")
time.sleep(2)

print("\n✅ Simulating successful database query...")
# In a real app with OpenTelemetry instrumentation, this would be automatic:
# User.objects.all()  # Django
# session.query(User).all()  # SQLAlchemy
# Both would trigger success signals automatically!

client = rootsense.get_client()
if client:
    # Manually send success signal (normally automatic via OpenTelemetry)
    client.transport.send_success_signal(
        fingerprint="db:postgresql:SELECT:users",
        context={
            "operation_type": "db",
            "database": "postgresql",
            "query": "SELECT * FROM users",
            "success": True
        }
    )
    print("✅ Success signal sent")
    print("   → Incident will auto-resolve if consistently successful")


# Example 3: HTTP endpoint error and recovery
print("\n=== Example 3: HTTP Endpoint Error & Auto-Resolution ===")

print("\n📊 Simulating HTTP 500 error...")
try:
    raise Exception("Internal server error on GET /api/users")
except Exception as e:
    event_id = rootsense.capture_exception(e, context={
        "operation_type": "http",
        "method": "GET",
        "endpoint": "/api/users",
        "status_code": 500
    })
    print(f"❌ Error captured: {event_id}")
    print(f"   Fingerprint: http:GET:/api/users")
    print(f"   → Incident created")

print("\n⏳ Waiting 2 seconds (simulating fix deployment)...")
time.sleep(2)

print("\n✅ Simulating successful HTTP request...")
# In a real app with Django/Flask/FastAPI:
# Just accessing the endpoint would trigger success signal automatically!
if client:
    client.transport.send_success_signal(
        fingerprint="http:GET:/api/users",
        context={
            "operation_type": "http",
            "method": "GET",
            "endpoint": "/api/users",
            "status_code": 200,
            "success": True
        }
    )
    print("✅ Success signal sent")
    print("   → Incident will auto-resolve")


# Example 4: Redis operation error and recovery
print("\n=== Example 4: Redis Error & Auto-Resolution ===")

print("\n📊 Simulating Redis connection error...")
try:
    raise Exception("Redis connection refused: localhost:6379")
except Exception as e:
    event_id = rootsense.capture_exception(e, context={
        "operation_type": "redis",
        "command": "GET",
        "key": "user:12345"
    })
    print(f"❌ Error captured: {event_id}")
    print(f"   Fingerprint: redis:GET")
    print(f"   → Incident created")

print("\n⏳ Waiting 2 seconds (simulating Redis restart)...")
time.sleep(2)

print("\n✅ Simulating successful Redis operation...")
# In a real app with redis-py:
# r.get("user:12345")  # Automatically tracked and success signal sent!
if client:
    client.transport.send_success_signal(
        fingerprint="redis:GET",
        context={
            "operation_type": "redis",
            "command": "GET",
            "success": True
        }
    )
    print("✅ Success signal sent")
    print("   → Incident will auto-resolve")


# Show summary
print("\n=== Summary ===")
print("✨ RootSense captures errors and tracks recovery automatically!")
print("")
print("What happens automatically with auto-instrumentation:")
print("  1. All errors captured with context")
print("  2. Database queries tracked (Django ORM, SQLAlchemy)")
print("  3. HTTP requests tracked (requests, httpx, urllib)")
print("  4. Redis operations tracked")
print("  5. Celery tasks tracked")
print("  6. Success signals sent when operations recover")
print("  7. Incidents auto-resolve when consistently successful")
print("")
print("No manual instrumentation needed! 🎉")

# Clean shutdown
print("\n=== Shutting Down ===")
if client:
    client.close()
    print("✅ RootSense client closed")
