"""FastAPI integration example with auto-instrumentation.

This example shows how to use RootSense with FastAPI.
All database queries, HTTP requests, and errors are captured automatically!
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import rootsense
import os

# Create FastAPI app
app = FastAPI()

# Initialize RootSense
rootsense.init(
    api_key=os.getenv("ROOTSENSE_API_KEY"),
    project_id=os.getenv("ROOTSENSE_PROJECT_ID"),
    environment=os.getenv("ENVIRONMENT", "production"),
    service_name="my-fastapi-app",
    service_version="1.0.0",
    enable_auto_instrumentation=True  # Default: True
)

# That's it! FastAPI is now fully instrumented:
# - HTTP requests: auto-tracked
# - SQLAlchemy queries: auto-tracked
# - Background tasks: auto-tracked
# - Dependencies: auto-tracked
# - Errors: auto-captured
# - Auto-resolution: enabled

# Database setup
DATABASE_URL = "postgresql://localhost/myapp"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/api/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """List all users.
    
    This SQLAlchemy query is automatically tracked!
    - Query execution time
    - SQL text
    - Database name
    - If fails: incident created
    - When succeeds: incident auto-resolved
    """
    users = db.query(User).all()
    return users

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID.
    
    Automatically tracked with auto-resolution!
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user.
    
    Database INSERT automatically tracked!
    """
    db_user = User(email=user.email, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/external-data")
async def fetch_external_data():
    """Fetch data from external API.
    
    HTTP request is automatically tracked!
    """
    import httpx
    
    # This async HTTP request is automatically tracked!
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.example.com/data')
        response.raise_for_status()
        return response.json()

def process_in_background(user_id: int):
    """Background task processing.
    
    This background task is automatically tracked!
    - Execution time
    - Any database queries inside
    - Any errors that occur
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        # Process user...
    finally:
        db.close()

@app.post("/api/users/{user_id}/process")
def trigger_background_task(
    user_id: int,
    background_tasks: BackgroundTasks
):
    """Trigger background processing.
    
    Background task execution is automatically tracked!
    """
    background_tasks.add_task(process_in_background, user_id)
    return {"message": "Processing started"}

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler.
    
    All exceptions are automatically captured by RootSense!
    This handler is optional - just for custom responses.
    """
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# What gets tracked automatically:
# --------------------------------
# 1. HTTP Requests:
#    - GET /api/users
#    - POST /api/users
#    - GET /api/users/{id}
#    - All with timing and status codes
#
# 2. Database Queries:
#    - db.query(User).all()
#    - db.query(User).filter(...).first()
#    - db.add() / db.commit()
#    - All with execution time
#
# 3. Background Tasks:
#    - Execution time tracked
#    - Any errors captured
#    - Database queries inside tracked
#
# 4. Dependencies:
#    - get_db() dependency tracked
#    - Execution time measured
#
# 5. External HTTP Calls:
#    - httpx async requests
#    - With full request/response tracking
#
# 6. Errors:
#    - All unhandled exceptions
#    - With stack traces
#    - With request context
#
# 7. Auto-Resolution:
#    - Automatic when operations recover
#    - No manual intervention needed
