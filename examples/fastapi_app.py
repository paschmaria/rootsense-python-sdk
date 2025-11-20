"""FastAPI application example with RootSense integration.

This example demonstrates:
- FastAPI integration using RootSenseFastAPI
- Automatic error capture from FastAPI routes
- Async/await support
- Request context tracking
- Background tasks integration
- WebSocket error handling

Installation:
    pip install rootsense[fastapi]

Run:
    uvicorn fastapi_app:app --reload
    
Test endpoints:
    http://localhost:8000/               # API info
    http://localhost:8000/docs           # Swagger UI
    http://localhost:8000/error          # Trigger error
    http://localhost:8000/async-error    # Async error
    http://localhost:8000/user/123       # User route
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import rootsense
from rootsense.integrations.fastapi import RootSenseFastAPI
import asyncio
import random
import time


# Pydantic models
class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", description="Currency code")
    method: str = Field(default="credit_card", description="Payment method")
    user_id: Optional[str] = Field(None, description="User ID")


class PaymentResponse(BaseModel):
    status: str
    transaction_id: str
    amount: float
    message: str


# Create FastAPI app
app = FastAPI(
    title="RootSense FastAPI Demo",
    description="Demo application with RootSense error tracking",
    version="1.0.0"
)

# Initialize RootSense for FastAPI
# This automatically:
# - Captures all unhandled exceptions
# - Adds request context (URL, method, headers, etc.)
# - Tracks async operations
# - Exposes /metrics endpoint for Prometheus
RootSenseFastAPI(
    app,
    api_key="your-api-key",  # Replace with your actual API key
    project_id="your-project-id",  # Replace with your project ID
    environment="production",
    send_default_pii=False,
    enable_prometheus=True,
    debug=True
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to RootSense FastAPI Demo",
        "docs": "/docs",
        "endpoints": [
            "/",
            "/error",
            "/async-error",
            "/user/{user_id}",
            "/payment",
            "/slow",
            "/background-task",
            "/metrics"
        ]
    }


@app.get("/error")
async def trigger_error():
    """Endpoint that deliberately throws an error."""
    rootsense.push_breadcrumb(
        message="User requested /error endpoint",
        category="navigation",
        level="info"
    )
    
    rootsense.set_tag("error_type", "deliberate")
    
    # This will be automatically captured by RootSense
    raise ValueError("This is a deliberate error for testing!")


@app.get("/async-error")
async def trigger_async_error():
    """Endpoint with error in async operation."""
    rootsense.push_breadcrumb(
        message="Starting async operation",
        category="async",
        level="info"
    )
    
    # Simulate async operation
    await asyncio.sleep(0.1)
    
    rootsense.push_breadcrumb(
        message="Async operation failed",
        category="async",
        level="error"
    )
    
    raise RuntimeError("Error in async operation!")


@app.get("/user/{user_id}")
async def get_user(user_id: str):
    """User-specific route with context."""
    # Set user context
    rootsense.set_user(
        id=user_id,
        username=f"user_{user_id}",
        email=f"user{user_id}@example.com"
    )
    
    # Add tags
    user_num = int(user_id) if user_id.isdigit() else 0
    rootsense.set_tag("user_type", "premium" if user_num % 2 == 0 else "free")
    
    # Simulate errors for some users
    if user_num % 5 == 0:
        rootsense.push_breadcrumb(
            message=f"Database query for user {user_id}",
            category="database",
            level="info"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load profile for user {user_id}"
        )
    
    return {
        "user_id": user_id,
        "username": f"user_{user_id}",
        "status": "active",
        "plan": "premium" if user_num % 2 == 0 else "free"
    }


@app.post("/payment", response_model=PaymentResponse)
async def process_payment(payment: PaymentRequest):
    """Payment processing endpoint."""
    # Add payment context
    rootsense.set_context("payment", {
        "amount": payment.amount,
        "currency": payment.currency,
        "method": payment.method
    })
    
    if payment.user_id:
        rootsense.set_user(id=payment.user_id)
    
    rootsense.push_breadcrumb(
        message="Payment processing started",
        category="payment",
        level="info",
        data={"amount": payment.amount}
    )
    
    # Validate payment
    if payment.amount > 10000:
        rootsense.push_breadcrumb(
            message="Payment exceeds limit",
            category="validation",
            level="error"
        )
        raise HTTPException(
            status_code=400,
            detail="Payment amount exceeds limit"
        )
    
    # Simulate async payment processing
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    # Random payment failures
    if random.random() < 0.1:  # 10% failure rate
        rootsense.push_breadcrumb(
            message="Payment gateway error",
            category="payment",
            level="error"
        )
        raise HTTPException(
            status_code=502,
            detail="Payment gateway connection failed"
        )
    
    transaction_id = f"txn_{int(time.time())}"
    
    return PaymentResponse(
        status="success",
        transaction_id=transaction_id,
        amount=payment.amount,
        message="Payment processed successfully"
    )


@app.get("/slow")
async def slow_endpoint():
    """Endpoint with deliberate slowness."""
    rootsense.push_breadcrumb(
        message="Starting slow async operation",
        category="performance",
        level="info"
    )
    
    # Simulate slow async operation
    duration = random.uniform(1, 3)
    await asyncio.sleep(duration)
    
    rootsense.set_tag("slow_operation", "true")
    rootsense.set_context("performance", {
        "duration_seconds": duration
    })
    
    return {
        "message": "Slow operation completed",
        "duration": duration
    }


async def slow_background_task(task_id: str):
    """Simulated background task that may fail."""
    try:
        rootsense.push_breadcrumb(
            message=f"Background task {task_id} started",
            category="background_task",
            level="info"
        )
        
        await asyncio.sleep(2)
        
        # Random failures
        if random.random() < 0.3:
            raise RuntimeError(f"Background task {task_id} failed!")
        
        rootsense.push_breadcrumb(
            message=f"Background task {task_id} completed",
            category="background_task",
            level="info"
        )
    except Exception as e:
        rootsense.capture_exception(e)


@app.post("/background-task")
async def create_background_task(background_tasks: BackgroundTasks):
    """Create a background task."""
    task_id = f"task_{int(time.time())}"
    
    rootsense.set_tag("background_task_id", task_id)
    background_tasks.add_task(slow_background_task, task_id)
    
    return {
        "message": "Background task created",
        "task_id": task_id
    }


@app.get("/database-error")
async def database_error():
    """Simulate database connection error."""
    rootsense.push_breadcrumb(
        message="Attempting async database connection",
        category="database",
        level="info"
    )
    
    await asyncio.sleep(0.1)
    
    rootsense.push_breadcrumb(
        message="Database connection timeout",
        category="database",
        level="error",
        data={"timeout": 30}
    )
    
    raise HTTPException(
        status_code=503,
        detail="Database connection pool exhausted"
    )


@app.get("/nested-async-error")
async def nested_async_error():
    """Error in nested async calls."""
    async def level1():
        rootsense.push_breadcrumb(message="Async Level 1", category="trace", level="debug")
        await asyncio.sleep(0.01)
        return await level2()
    
    async def level2():
        rootsense.push_breadcrumb(message="Async Level 2", category="trace", level="debug")
        await asyncio.sleep(0.01)
        return await level3()
    
    async def level3():
        rootsense.push_breadcrumb(message="Async Level 3 - Error!", category="trace", level="error")
        raise RuntimeError("Error in nested async function at level 3")
    
    return await level1()


@app.middleware("http")
async def add_custom_context(request: Request, call_next):
    """Add custom context to each request."""
    # Add request ID
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time())}")
    rootsense.set_tag("request_id", request_id)
    
    # Add user agent info
    if "user-agent" in request.headers:
        rootsense.set_tag("user_agent", request.headers["user-agent"][:100])
    
    # Process request
    response = await call_next(request)
    
    # Add response status
    rootsense.set_tag("response_status", response.status_code)
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions."""
    # These are already captured by RootSense middleware
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom handler for general exceptions."""
    # Already captured by RootSense middleware
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    print("Starting FastAPI app with RootSense integration...")
    print("Visit http://localhost:8000/docs for Swagger UI")
    print("Prometheus metrics available at http://localhost:8000/metrics")
    
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
