# # backend/main.py

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List, Literal
# import redis
# import json
# import hashlib

# # Import the new chains and settings
# from backend.agent.agent import read_only_chain, read_write_chain
# from backend.core.config import settings

# app = FastAPI(
#     title="Auto SQL GPT - Professional Edition",
#     description="An API with role-based access for converting natural language to SQL queries.",
#     version="4.0.0",
# )

# # --- Redis Connection ---
# try:
#     redis_settings = settings.get('redis', {})
#     redis_client = redis.Redis(host=redis_settings.get('host', 'localhost'), port=redis_settings.get('port', 6379), db=redis_settings.get('db', 0), decode_responses=True)
#     redis_client.ping()
#     print("Successfully connected to Redis.")
# except redis.exceptions.ConnectionError as e:
#     print(f"Could not connect to Redis: {e}. Caching will be disabled.")
#     redis_client = None

# # --- Pydantic Models ---
# class QueryRequest(BaseModel):
#     query: str
#     role: Literal['read_only', 'admin']
#     chat_history: List[dict] = []

# class QueryResponse(BaseModel):
#     answer: str
#     chat_history: List[dict]

# class AuthRequest(BaseModel):
#     password: str

# # --- API Endpoints ---
# @app.post("/authenticate")
# def authenticate(request: AuthRequest):
#     """Endpoint to check the admin password."""
#     correct_password = settings.get('admin', {}).get('password')
#     if request.password == correct_password:
#         return {"authenticated": True}
#     else:
#         raise HTTPException(status_code=401, detail="Incorrect password")

# @app.post("/query", response_model=QueryResponse)
# def process_query(request: QueryRequest):
#     """
#     This endpoint receives a query and a role, then invokes the appropriate chain.
#     """
#     print(f"Received query: '{request.query}' with role: '{request.role}'")
    
#     cache_key = f"query:{request.role}:{hashlib.md5(request.query.encode()).hexdigest()}"

#     if redis_client:
#         cached_result = redis_client.get(cache_key)
#         if cached_result:
#             print(f"Cache hit for key: {cache_key}")
#             return json.loads(cached_result)

#     print(f"Cache miss for key: {cache_key}. Invoking chain.")
    
#     is_write = False
#     if request.role == 'admin':
#         result_dict = read_write_chain.invoke({"input": request.query})
#         answer = result_dict.get("answer")
#         is_write = result_dict.get("is_write", False)
#     else: # read_only
#         answer = read_only_chain.invoke({"input": request.query})

#     if redis_client and is_write:
#         print(f"Write operation detected. Flushing Redis cache.")
#         redis_client.flushdb()

#     updated_history = request.chat_history + [{"role": "user", "content": request.query}, {"role": "assistant", "content": answer}]
#     response_data = {"answer": answer, "chat_history": updated_history}

#     if redis_client and not is_write:
#         redis_ttl = settings.get('redis', {}).get('ttl', 3600)
#         redis_client.setex(cache_key, redis_ttl, json.dumps(response_data))
#         print(f"Stored result in cache for key: {cache_key}")

#     return response_data

#````````````````````````````main````````````````````````````````



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal
import redis
import json
import hashlib

# Import the new chains and settings
from backend.agent.agent import read_only_chain, read_write_chain
from backend.core.config import settings

app = FastAPI(
    title="WhisperDB - Conversations, not queries",
    description="Conversational AI interface for databases",
    version="4.1.0", # Version updated for DB info endpoint
)

# --- Redis Connection ---
try:
    redis_settings = settings.get('redis', {})
    redis_client = redis.Redis(host=redis_settings.get('host', 'localhost'), port=redis_settings.get('port', 6379), db=redis_settings.get('db', 0), decode_responses=True)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}. Caching will be disabled.")
    redis_client = None

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    role: Literal['read_only', 'admin']
    chat_history: List[dict] = []

class QueryResponse(BaseModel):
    answer: str
    chat_history: List[dict]

class AuthRequest(BaseModel):
    password: str

# --- API Endpoints ---
@app.get("/db-info")
def get_db_info():
    """Endpoint to get the name of the currently active database."""
    active_db = settings.get('database', {}).get('active_database', 'N/A')
    return {"active_database": active_db}

@app.post("/authenticate")
def authenticate(request: AuthRequest):
    """Endpoint to check the admin password."""
    correct_password = settings.get('admin', {}).get('password')
    if request.password == correct_password:
        return {"authenticated": True}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")

@app.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    """
    This endpoint receives a query and a role, then invokes the appropriate chain.
    """
    print(f"Received query: '{request.query}' with role: '{request.role}'")
    
    cache_key = f"query:{request.role}:{hashlib.md5(request.query.encode()).hexdigest()}"

    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print(f"Cache hit for key: {cache_key}")
            return json.loads(cached_result)

    print(f"Cache miss for key: {cache_key}. Invoking chain.")
    
    is_write = False
    if request.role == 'admin':
        result_dict = read_write_chain.invoke({"input": request.query})
        answer = result_dict.get("answer")
        is_write = result_dict.get("is_write", False)
    else: # read_only
        answer = read_only_chain.invoke({"input": request.query})

    if redis_client and is_write:
        print(f"Write operation detected. Flushing Redis cache.")
        redis_client.flushdb()

    updated_history = request.chat_history + [{"role": "user", "content": request.query}, {"role": "assistant", "content": answer}]
    response_data = {"answer": answer, "chat_history": updated_history}

    if redis_client and not is_write:
        redis_ttl = settings.get('redis', {}).get('ttl', 3600)
        redis_client.setex(cache_key, redis_ttl, json.dumps(response_data))
        print(f"Stored result in cache for key: {cache_key}")

    return response_data



# backend/main.py

# backend/main.py

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware # --- NEW: Import CORS Middleware ---
# from pydantic import BaseModel
# from typing import List, Literal
# import redis
# import json
# import hashlib

# # Import the new chains and settings
# from backend.agent.agent import read_only_chain, read_write_chain
# from backend.core.config import settings

# app = FastAPI(
#     title="WhisperDB - Professional Edition",
#     description="An API with role-based access for converting natural language to SQL queries.",
#     version="4.2.0", # Version updated for CORS fix
# )

# # --- FINAL FIX: Add CORS Middleware ---
# # This allows your HTML frontend (running on http://localhost:3000)
# # to communicate with your backend (running on http://localhost:8000).
# origins = [
#     "http://localhost:3000",
#     "null" # Allow requests from 'file://' origin when double-clicking the html
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # --- Redis Connection ---
# try:
#     redis_settings = settings.get('redis', {})
#     redis_client = redis.Redis(host=redis_settings.get('host', 'localhost'), port=redis_settings.get('port', 6379), db=redis_settings.get('db', 0), decode_responses=True)
#     redis_client.ping()
#     print("Successfully connected to Redis.")
# except redis.exceptions.ConnectionError as e:
#     print(f"Could not connect to Redis: {e}. Caching will be disabled.")
#     redis_client = None

# # --- Pydantic Models ---
# class QueryRequest(BaseModel):
#     query: str
#     role: Literal['read_only', 'admin']
#     chat_history: List[dict] = []

# class QueryResponse(BaseModel):
#     answer: str
#     chat_history: List[dict]

# class AuthRequest(BaseModel):
#     password: str

# # --- API Endpoints ---
# @app.get("/db-info")
# def get_db_info():
#     """Endpoint to get the name of the currently active database."""
#     active_db = settings.get('database', {}).get('active_database', 'N/A')
#     return {"active_database": active_db}

# @app.post("/authenticate")
# def authenticate(request: AuthRequest):
#     """Endpoint to check the admin password."""
#     correct_password = settings.get('admin', {}).get('password')
#     if request.password == correct_password:
#         return {"authenticated": True}
#     else:
#         raise HTTPException(status_code=401, detail="Incorrect password")

# @app.post("/query", response_model=QueryResponse)
# def process_query(request: QueryRequest):
#     """
#     This endpoint receives a query and a role, then invokes the appropriate chain.
#     """
#     print(f"Received query: '{request.query}' with role: '{request.role}'")
    
#     cache_key = f"query:{request.role}:{hashlib.md5(request.query.encode()).hexdigest()}"

#     if redis_client:
#         cached_result = redis_client.get(cache_key)
#         if cached_result:
#             print(f"Cache hit for key: {cache_key}")
#             return json.loads(cached_result)

#     print(f"Cache miss for key: {cache_key}. Invoking chain.")
    
#     is_write = False
#     if request.role == 'admin':
#         result_dict = read_write_chain.invoke({"input": request.query})
#         answer = result_dict.get("answer")
#         is_write = result_dict.get("is_write", False)
#     else: # read_only
#         answer = read_only_chain.invoke({"input": request.query})

#     if redis_client and is_write:
#         print(f"Write operation detected. Flushing Redis cache.")
#         redis_client.flushdb()

#     updated_history = request.chat_history + [{"role": "user", "content": request.query}, {"role": "assistant", "content": answer}]
#     response_data = {"answer": answer, "chat_history": updated_history}

#     if redis_client and not is_write:
#         redis_ttl = settings.get('redis', {}).get('ttl', 3600)
#         redis_client.setex(cache_key, redis_ttl, json.dumps(response_data))
#         print(f"Stored result in cache for key: {cache_key}")

#     return response_data
