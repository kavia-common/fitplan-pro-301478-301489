from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database.connection import engine

# Create FastAPI app with metadata for OpenAPI documentation
app = FastAPI(
    title="FitPlan Pro API",
    description="Backend API for FitPlan Pro workout management application. "
                "Provides endpoints for workout generation, exercise management, "
                "workout logging, progress tracking, and user goal management.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and status endpoints"
        },
        {
            "name": "workouts",
            "description": "Workout management operations"
        },
        {
            "name": "exercises",
            "description": "Exercise library operations"
        },
        {
            "name": "logs",
            "description": "Workout logging operations"
        },
        {
            "name": "progress",
            "description": "Progress tracking operations"
        },
        {
            "name": "goals",
            "description": "User goal management operations"
        }
    ]
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "https://vscode-internal-21591-beta.beta01.cloud.kavia.ai:3000",  # Production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    
    Initializes database connection and performs any necessary
    startup tasks. The database tables should already exist
    (created by the database container), so we only verify
    the connection here.
    """
    # Verify database connection
    try:
        with engine.connect():
            print("✓ Database connection established successfully")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    
    Performs cleanup tasks when the application shuts down.
    """
    engine.dispose()
    print("✓ Database connection closed")


# PUBLIC_INTERFACE
@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint.
    
    Returns the API status and basic information.
    
    Returns:
        dict: Status message and API information
    """
    return {
        "status": "healthy",
        "message": "FitPlan Pro API is running",
        "version": "1.0.0"
    }
