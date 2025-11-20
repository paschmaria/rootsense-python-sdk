"""FastAPI application example with RootSense integration."""

import os
import time
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import rootsense
from rootsense.integrations.fastapi import capture_fastapi_errors
from rootsense.tracing import get_tracer

# Initialize RootSense
rootsense.init(
    api_key=os.getenv("ROOTSENSE_API_KEY", "test_api_key"),
    project_id=os.getenv("ROOTSENSE_PROJECT_ID", "test_project_id"),
    environment="development",
    debug=True
)

app = FastAPI(title="FastAPI with RootSense")

# Add RootSense middleware
capture_fastapi_errors(app)

# Get tracer for distributed tracing
tracer = get_tracer()


class User(BaseModel):
    id: int
    username: str
    email: str


@app.get("/")
async def root():
    return {
        "message": "FastAPI app with RootSense integration",
        "status": "healthy"
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID - demonstrates successful request tracking."""
    with tracer.trace("get_user") as span:
        span.set_tag("user_id", user_id)
        
        # Simulate database query
        await asyncio.sleep(0.1)
        
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "email": f"user{user_id}@example.com"
        }


@app.get("/api/error")
async def trigger_error():
    """Trigger an error - demonstrates error capture."""
    raise ValueError("This is a test error!")


@app.get("/api/http-error")
async def http_error():
    """Trigger HTTP error - demonstrates HTTPException handling."""
    raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/api/slow")
async def slow_endpoint():
    """Slow endpoint - demonstrates performance monitoring."""
    with tracer.trace("slow_operation") as span:
        await asyncio.sleep(2)  # Simulate slow operation
        span.set_tag("duration", 2.0)
        
    return {"message": "Slow operation completed"}


@app.post("/api/users")
async def create_user(user: User):
    """Create user - demonstrates request body tracking."""
    from rootsense.context import set_tag
    
    set_tag("user.id", user.id)
    set_tag("user.username", user.username)
    
    return {
        "message": "User created successfully",
        "user": user.dict()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
