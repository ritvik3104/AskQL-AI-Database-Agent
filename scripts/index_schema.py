# scripts/index_schema.py

import os
import sys
import time # --- FIX: Import the time module for adding a delay ---
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import inspect # --- FIX: Import the database-agnostic Inspector ---

# Add the backend directory to the Python path to allow for module imports
# This ensures we can import from 'backend' even when running from the 'scripts' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import db
from backend.core.config import settings

# --- Configuration ---
PINECONE_API_KEY = settings['api_keys']['pinecone']
PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2' # A popular, high-quality model

def create_schema_chunks():
    """
    Creates detailed text descriptions (chunks) for each table and column
    in the connected database using a database-agnostic method.
    """
    print("Extracting schema from the database...")
    
    # --- FIX: Use SQLAlchemy Inspector for cross-database compatibility ---
    inspector = inspect(db._engine)
    table_names = inspector.get_table_names()
    all_chunks = []

    print(f"Found tables: {table_names}")

    for table_name in table_names:
        # Create a detailed chunk for the table itself
        # db.get_table_info is safe as it's a LangChain wrapper around the inspector
        table_info = db.get_table_info([table_name])
        table_chunk = f"Table Name: {table_name}\nTable Schema: {table_info}"
        all_chunks.append({"id": f"table-{table_name}", "text": table_chunk})

        # Create chunks for each column using the inspector
        columns = inspector.get_columns(table_name)
        for col in columns:
            col_name = col['name']
            # The inspector returns a complex type object, so we convert it to a string
            col_type = str(col['type'])
            col_chunk = f"Table: {table_name}, Column: {col_name}, Type: {col_type}"
            all_chunks.append({"id": f"col-{table_name}-{col_name}", "text": col_chunk})
            
    print(f"Created {len(all_chunks)} schema chunks for Pinecone.")
    return all_chunks

def main():
    """
    Main function to create chunks, embed them, and store them in Pinecone.
    """
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set in your .env file.")

    # 1. Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # 2. Delete the old index to ensure a fresh start (optional but recommended)
    if PINECONE_INDEX_NAME in pc.list_indexes().names():
        print(f"Deleting existing index '{PINECONE_INDEX_NAME}' to rebuild it...")
        pc.delete_index(PINECONE_INDEX_NAME)

    # 3. Create a new Pinecone index
    print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384, # The dimension of the all-MiniLM-L6-v2 model
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
    index = pc.Index(PINECONE_INDEX_NAME)

    # 4. Create Schema Chunks
    chunks = create_schema_chunks()
    
    # 5. Initialize Embedding Model
    print("Loading embedding model (this may take a moment)...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # 6. Embed and Upsert to Pinecone
    print("Embedding schema chunks and uploading to Pinecone...")
    vectors_to_upsert = []
    for chunk in chunks:
        embedding = model.encode(chunk['text']).tolist()
        vectors_to_upsert.append({
            "id": chunk['id'],
            "values": embedding,
            "metadata": {"text": chunk['text']}
        })

    # Upsert in batches for efficiency
    index.upsert(vectors=vectors_to_upsert, batch_size=100)
    
    # --- FIX: Add a delay to allow the index stats to update ---
    print("Waiting for Pinecone index to update...")
    time.sleep(10) # Wait for 10 seconds

    print("\n✅ Schema indexing complete!")
    print(f"Total vectors in index: {index.describe_index_stats()['total_vector_count']}")

if __name__ == "__main__":
    main()
