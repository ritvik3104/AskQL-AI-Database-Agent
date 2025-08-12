# backend/core/config.py

import yaml
from dotenv import load_dotenv
import os
from pathlib import Path

def load_settings():
    """
    Loads settings from .env and config.yaml files using robust file paths.
    """
    # Load environment variables from .env file in the root directory
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    config = None
    try:
        # Create a robust, absolute path to the config.yaml file
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        print(f"DEBUG: Attempting to load config from: {config_path}")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            print("DEBUG: config.yaml loaded successfully.")
            # print(f"DEBUG: Config content: {config}") # Uncomment for deep debugging
            
    except FileNotFoundError:
        print(f"FATAL ERROR: config.yaml not found at the expected path: {config_path}")
        raise
    except Exception as e:
        print(f"FATAL ERROR: Could not parse config.yaml. Error: {e}")
        raise

    if not isinstance(config, dict):
        raise TypeError("FATAL ERROR: config.yaml is not a valid dictionary.")

    # Combine all settings into a single dictionary
    settings = {
        "api_keys": {
            "groq": os.getenv("GROQ_API_KEY"),
            "pinecone": os.getenv("PINECONE_API_KEY")
        },
        "admin": {
            "password": os.getenv("ADMIN_PASSWORD")
        },
        "database": {
            "active_database": config.get('active_database'),
            "profiles": config.get('database_profiles', {})
        },
        "redis": config.get('redis', {})
    }
    return settings

settings = load_settings()
