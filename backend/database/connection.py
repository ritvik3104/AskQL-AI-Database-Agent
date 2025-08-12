# backend/database/connection.py

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
import os

# Import the settings we created in the core module
from backend.core.config import settings

def get_database():
    """
    Creates and returns a LangChain SQLDatabase object based on the
    active profile in the config.yaml file.
    """
    db_config = settings.get('database', {})
    
    # --- FIX: Safer access to the active_database key ---
    active_db_profile_name = db_config.get('active_database')
    if not active_db_profile_name:
        raise ValueError("FATAL ERROR: 'active_database' key is missing or empty in your config.yaml.")

    db_profiles = db_config.get('profiles', {})
    db_profile = db_profiles.get(active_db_profile_name)
    if not db_profile:
        raise ValueError(f"FATAL ERROR: The active profile '{active_db_profile_name}' was not found in the database_profiles section of your config.yaml.")

    db_type = db_profile.get('type')

    if db_type == "sqlite":
        # Handle SQLite connection
        db_path = os.path.join("backend", db_profile['db_path'])
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database not found at {db_path}. Please run init_db.py.")
        db_uri = f"sqlite:///{db_path}"
    
    elif db_type == "postgresql":
        # Handle PostgreSQL connection
        db_uri = (
            f"postgresql+psycopg2://{db_profile['user']}:{db_profile['password']}"
            f"@{db_profile['host']}:{db_profile['port']}/{db_profile['database_name']}"
        )

    elif db_type == "mysql":
        # Handle MySQL connection
        db_uri = (
            f"mysql+mysqlclient://{db_profile['user']}:{db_profile['password']}"
            f"@{db_profile['host']}:{db_port}/{db_profile['database_name']}"
        )
        
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    print(f"Connecting to {db_type} database...")
    
    # Create the LangChain SQLDatabase object
    return SQLDatabase.from_uri(db_uri)

# Create a single database instance to be used across the application
db = get_database()
