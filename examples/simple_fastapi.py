"""Simple FastAPI example with RootSense."""

from fastapi import FastAPI
import rootsense
from rootsense.middleware.fastapi import capture_fastapi_errors
from rootsense.context import set_user, add_breadcrumb

app = FastAPI(title="RootSense FastAPI Example")

# Initialize RootSense
rootsense.init(
    connection_string="rootsense://your-api-key@api.rootsense.ai/your-project-id",
    environment="development",
    debug=True
)

# Add RootSense integration
capture_fastapi_errors(app)

@app.get("/")
async def root():
    return {"message": "Hello from RootSense + FastAPI!"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Set user context
    set_user({"id": user_id})
    
    add_breadcrumb("api", f"Fetching user {user_id}")
    
    return {"id": user_id, "name": "John Doe"}

@app.post("/error")
async def trigger_error():
    # This will be automatically captured by RootSense
    raise ValueError("Test error for demonstration")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
