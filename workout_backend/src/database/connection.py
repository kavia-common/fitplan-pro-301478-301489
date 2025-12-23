import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_database_url():
    """
    Get the database URL from environment variables or db_connection.txt.
    
    Priority:
    1. POSTGRES_URL environment variable (if fully formed URL)
    2. Individual PostgreSQL environment variables (POSTGRES_USER, POSTGRES_PASSWORD, etc.)
    3. Fallback to reading db_connection.txt from workout_database container
    
    Returns:
        str: PostgreSQL connection URL
    """
    # Check if POSTGRES_URL is provided and is a full URL
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url and postgres_url.startswith("postgresql://"):
        return postgres_url
    
    # Try to build URL from individual environment variables
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5000")
    
    if all([postgres_user, postgres_password, postgres_db]):
        return f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    # Fallback: read from db_connection.txt in the workout_database container
    try:
        # Assuming the db_connection.txt is accessible from the backend
        db_connection_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "fitplan-pro-301478-301488",
            "workout_database",
            "db_connection.txt"
        )
        
        if os.path.exists(db_connection_file):
            with open(db_connection_file, "r") as f:
                connection_string = f.read().strip()
                # Extract the URL part after 'psql '
                if connection_string.startswith("psql "):
                    return connection_string.replace("psql ", "").strip()
                return connection_string
    except Exception as e:
        print(f"Warning: Could not read db_connection.txt: {e}")
    
    # Default fallback
    return "postgresql://appuser:dbuser123@localhost:5000/myapp"


# Get database URL
DATABASE_URL = get_database_url()

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
)

# Create sessionmaker for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db():
    """
    Dependency function to get database session.
    
    This function is used as a FastAPI dependency to provide
    database sessions to route handlers. It ensures proper
    session lifecycle management.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
