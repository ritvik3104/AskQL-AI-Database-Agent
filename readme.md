# 🤖 AskQL - Ask Your DB

**AskQL** is a sophisticated, full-stack application that transforms how users interact with databases. It allows anyone to have a natural language conversation with their data, enabling them to ask complex analytical questions, retrieve information, and even perform administrative actions like modifying data or altering table structures — all without writing a single line of SQL.

Built with a professional-grade tech stack, the application prioritizes security, performance, and user experience. It features a robust, role-based access system and an advanced AI core, making it a powerful and secure tool for any data-driven environment.

---

## ✨ Key Features

### Conversational AI for Database Interaction 💬
- Users can ask complex questions and give commands in plain English.
- The system maintains a memory of the current conversation, allowing for contextual follow-up questions.
- The AI provides friendly, readable answers and automatically includes markdown tables for list-based queries, enhancing readability.

### Advanced RAG with Pinecone for Read-Only Mode 🧠
- The "Read-Only" mode uses a state-of-the-art Retrieval-Augmented Generation (RAG) system for high-level, context-aware reasoning.
- Instead of being overwhelmed by an entire database schema, the AI's context is intelligently built by first querying a Pinecone vector database.
- This retrieves only the most semantically relevant table and column descriptions for a user's specific question, making the AI dramatically more accurate and efficient at handling complex, multi-table analytical queries.

### Few-Shot Prompting for Complex Queries 🎯
- To handle highly complex, multi-step queries, the AI is given a "masterclass" in advanced SQL directly within its instructions.
- The prompt includes concrete examples of how to write sophisticated queries (using subqueries, CTEs, and window functions).
- This few-shot prompting technique significantly improves the AI's ability to solve difficult analytical problems that would otherwise fail.

### Secure Role-Based Access Control (RBAC) 🔐
- The application features a secure login screen where users must choose between a safe "Read/View Only" mode and a password-protected "Admin" mode.
- The backend uses two completely separate and isolated logic chains for each role, ensuring a read-only user can never access data-modifying capabilities.

### Full Database Privileges for Admin Role ✍️
- Authenticated admins can perform a complete range of database operations, including SELECT, UPDATE, INSERT, DELETE, and Data Definition Language (DDL) commands like ALTER TABLE.
- The Admin mode is equipped with the same "god-level" prompting as the read-only mode, ensuring it can handle both simple and complex queries with high accuracy.
- Features intelligent cache invalidation: after any successful write operation, the entire Redis cache is automatically flushed, guaranteeing that subsequent queries always retrieve the most up-to-date data.

### Multi-Database Connectivity 🔄
- The project is database-agnostic and can be easily configured to connect to different SQL databases like PostgreSQL, MySQL, or SQLite.
- The connection is managed through a simple `config.yaml` file, allowing for easy switching without any code changes.

### High-Performance Caching with Redis ⚡
- Uses a high-speed Redis cache to store the results of previously asked questions.
- Dramatically improves the user experience for common queries by making the application more responsive.
- Reduces redundant calls to the LLM API.

### Professional UI with Speech-to-Text 🎤
- Sleek, modern chat interface with a professional navy blue theme.
- Includes a robust speech-to-text feature, allowing users to speak their queries directly into the application using the browser's native Web Speech API.

---

## 🛠️ Tech Stack

| Category           | Technology                            |
|--------------------|------------------------------------|
| Backend            | FastAPI, Uvicorn                   |
| Frontend           | Streamlit                         |
| AI & Orchestration | LangChain (LCEL for structured chains) |
| Language Model     | Groq API (with Llama3)             |
| Database Connectivity | SQLAlchemy (PostgreSQL, MySQL, SQLite) |
| Vector Database (RAG) | Pinecone                         |
| Caching            | Redis                             |
| Dependencies       | `requirements.txt`                  |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Docker Desktop (for running Redis)
- Access to a SQL database (or use the default SQLite)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd AskQL



2. Setup and Installation
Create a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate    # On Windows



Install Dependencies
pip install -r requirements.txt

Configure Environment Variables
Create a file named .env in the root directory.
Sign up for free accounts at Groq and Pinecone.
Add your keys and set an admin password:

GROQ_API_KEY="YOUR_GROQ_API_KEY"
PINECONE_API_KEY="YOUR_PINECONE_API_KEY"
ADMIN_PASSWORD="your_secure_password"


Configure the Database
Open backend/config.yaml.

To use the default SQLite database, no changes are needed.

To connect to your own PostgreSQL or MySQL database, update the relevant profile with your credentials and change active_database to match the profile name (e.g., postgres_example).

Initialize the Database and Pinecone Index
If using the default SQLite setup, run the database initialization script:

python backend/data/init_db.py
hen, run the schema indexing script to populate your Pinecone vector database.
You only need to do this once, or whenever your database schema changes:
python scripts/index_schema.py


▶️ How to Run the Application
You will need three separate terminals:

Terminal 1: Start the Redis Server
Make sure Docker Desktop is running.
Run this command to start the Redis container:


docker run --name my-redis -p 6379:6379 -d redis
(If it’s already running, you can use docker start my-redis)

Terminal 2: Start the Backend Server
Activate the virtual environment and navigate to the backend directory:



cd backend
uvicorn main:app --reload
Terminal 3: Start the Frontend Application
Open a new terminal, activate the virtual environment, then navigate to the frontend directory and run:

bash
Copy
Edit
cd frontend
streamlit run streamlit_app.py
Your browser should automatically open the application.
