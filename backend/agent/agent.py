# # # # # # backend/agent/agent.py

# # # # # from langchain_openai import ChatOpenAI
# # # # # from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# # # # # from langchain_core.prompts import ChatPromptTemplate
# # # # # from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# # # # # from langchain_core.output_parsers import StrOutputParser
# # # # # from sqlalchemy import text
# # # # # from sentence_transformers import SentenceTransformer
# # # # # from pinecone import Pinecone
# # # # # import re

# # # # # from backend.database.connection import db
# # # # # from backend.core.config import settings

# # # # # # --- ADVANCED RAG WITH PINECONE SETUP ---
# # # # # PINECONE_API_KEY = settings['api_keys']['pinecone']
# # # # # PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
# # # # # EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# # # # # # Initialize components for the RAG retriever
# # # # # pc = Pinecone(api_key=PINECONE_API_KEY)
# # # # # index = pc.Index(PINECONE_INDEX_NAME)
# # # # # embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# # # # # def get_relevant_schema_from_pinecone(query: str):
# # # # #     """
# # # # #     Embeds the user's query and retrieves the most relevant schema chunks
# # # # #     from Pinecone. This is the core of our advanced RAG.
# # # # #     """
# # # # #     print(f"\n--- Retrieving relevant schema for query: '{query}' ---")
# # # # #     query_embedding = embedding_model.encode(query).tolist()
# # # # #     results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
# # # # #     relevant_schema = "\n".join([match['metadata']['text'] for match in results['matches']])
# # # # #     print(f"--- Retrieved Schema Context ---\n{relevant_schema}\n---------------------------------")
# # # # #     return relevant_schema

# # # # # # --- HELPER FUNCTIONS ---
# # # # # def _create_llm():
# # # # #     """Helper function to initialize the Language Model."""
# # # # #     return ChatOpenAI(
# # # # #         model_name="llama3-70b-8192",
# # # # #         temperature=0,
# # # # #         api_key=settings['api_keys']['groq'],
# # # # #         base_url="https://api.groq.com/openai/v1"
# # # # #     )

# # # # # def _create_final_answer_chain(llm):
# # # # #     """Helper function to create the final answer formatting chain."""
# # # # #     final_answer_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

# # # # #         **Formatting Rules:**
# # # # #         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

# # # # #         **Table Display Rule:**
# # # # #         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
# # # # #         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

# # # # #         **Error and Invalid Query Handling:**
# # # # #         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
# # # # #         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

# # # # #         Original Question: {question}
# # # # #         SQL Result: {sql_result}
        
# # # # #         Final Answer:
# # # # #         """
# # # # #     )
# # # # #     return final_answer_prompt | llm | StrOutputParser()

# # # # # def _sql_sanitizer(response: str):
# # # # #     """
# # # # #     A robust guardrail to extract a clean SQL query from the LLM's output,
# # # # #     even if it includes conversational text or markdown.
# # # # #     """
# # # # #     # Find the content within a SQL markdown block if it exists
# # # # #     sql_match = re.search(r"```sql\n(.*?)\n```", response, re.DOTALL)
# # # # #     if sql_match:
# # # # #         return sql_match.group(1).strip()
# # # # #     # Otherwise, assume the response might be the query itself and clean it
# # # # #     return response.strip()

# # # # # # --- READ-ONLY CHAIN (NOW WITH PINECONE RAG AND FEW-SHOT PROMPTING) ---
# # # # # def get_read_only_chain():
# # # # #     llm = _create_llm()
    
# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are a master SQL architect. Given a user question and a database schema, your sole purpose is to generate a syntactically correct SQL query.

# # # # #         **RULES:**
# # # # #         1.  You are in a read-only environment. Only SELECT and WITH statements are allowed.
# # # # #         2.  Use only the tables and columns provided in the schema context.
# # # # #         3.  If the question is irrelevant, respond with the single word "INVALID".
# # # # #         4.  Your output MUST be ONLY the SQL query or the word "INVALID".

# # # # #         ---
# # # # #         **ADVANCED SQL EXAMPLES:**

# # # # #         **Example 1: Subquery for Comparison Against an Average**
# # # # #         User Question: "List employees whose salary is above the average salary of their department."
# # # # #         SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

# # # # #         **Example 2: GROUP BY with HAVING for Filtering Aggregates**
# # # # #         User Question: "Show each department and how many employees are in it, sorted by the highest count first."
# # # # #         SQL Query: `SELECT d.department_name, COUNT(e.employee_id) AS num_employees FROM departments d JOIN employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY num_employees DESC;`
# # # # #         ---

# # # # #         **YOUR TASK:**

# # # # #         Question: {question}
# # # # #         Schema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # # #     def execute_read_only_query(query: str):
# # # # #         if not query or query.strip().upper() == "INVALID":
# # # # #             return "INVALID_QUERY"
        
# # # # #         query_upper = query.strip().upper()
# # # # #         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
# # # # #         if any(keyword in query_upper for keyword in blocked_keywords):
# # # # #             return "Error: Data modification commands are not allowed in Read-Only mode."

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 result = connection.execute(text(query))
# # # # #                 return [dict(row) for row in result.mappings()]
# # # # #         except Exception as e:
# # # # #             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         RunnablePassthrough.assign(
# # # # #             schema=RunnableLambda(lambda x: get_relevant_schema_from_pinecone(x["input"])), 
# # # # #             question=lambda x: x["input"]
# # # # #         )
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"])))
# # # # #         | final_answer_chain
# # # # #     )
# # # # #     return full_chain

# # # # # # --- READ-WRITE CHAIN (UNCHANGED) ---
# # # # # def get_read_write_chain():
# # # # #     llm = _create_llm()

# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert SQL writer. Given a user command and a database schema, generate a SQL query to fulfill the request.
# # # # #         This can include SELECT, UPDATE, INSERT, or DELETE.
# # # # #         If the command is irrelevant, respond with "INVALID".
# # # # #         Only output the SQL query or "INVALID".
# # # # #         Command: {question}\nSchema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # # #     def execute_full_access_query(query: str):
# # # # #         if not query or query.strip().upper() == "INVALID":
# # # # #             return {"result": "INVALID_QUERY", "is_write": False}
        
# # # # #         is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE'))

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 if is_write_operation:
# # # # #                     with connection.begin() as transaction:
# # # # #                         connection.execute(text(query))
# # # # #                         transaction.commit()
# # # # #                     return {"result": "The command was executed successfully.", "is_write": True}
# # # # #                 else:
# # # # #                     result = connection.execute(text(query))
# # # # #                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
# # # # #         except Exception as e:
# # # # #             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
# # # # #         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
# # # # #         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
# # # # #     )
# # # # #     return full_chain

# # # # # # Create instances of both chains
# # # # # read_only_chain = get_read_only_chain()
# # # # # read_write_chain = get_read_write_chain()



# # # # # backend/agent/agent.py

# # # # # from langchain_openai import ChatOpenAI
# # # # # from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# # # # # from langchain_core.prompts import ChatPromptTemplate
# # # # # from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# # # # # from langchain_core.output_parsers import StrOutputParser
# # # # # from sqlalchemy import text
# # # # # from sentence_transformers import SentenceTransformer
# # # # # from pinecone import Pinecone
# # # # # import re

# # # # # from backend.database.connection import db
# # # # # from backend.core.config import settings

# # # # # # --- ADVANCED RAG WITH PINECONE SETUP ---
# # # # # PINECONE_API_KEY = settings['api_keys']['pinecone']
# # # # # PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
# # # # # EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# # # # # # Initialize components for the RAG retriever
# # # # # pc = Pinecone(api_key=PINECONE_API_KEY)
# # # # # index = pc.Index(PINECONE_INDEX_NAME)
# # # # # embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# # # # # def get_relevant_schema_from_pinecone(query: str):
# # # # #     """
# # # # #     Embeds the user's query and retrieves the most relevant schema chunks
# # # # #     from Pinecone.
# # # # #     """
# # # # #     print(f"\n--- Retrieving relevant schema for query: '{query}' ---")
# # # # #     query_embedding = embedding_model.encode(query).tolist()
# # # # #     results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
# # # # #     relevant_schema = "\n".join([match['metadata']['text'] for match in results['matches']])
# # # # #     print(f"--- Retrieved Schema Context ---\n{relevant_schema}\n---------------------------------")
# # # # #     return relevant_schema

# # # # # # --- HELPER FUNCTIONS ---
# # # # # def _create_llm():
# # # # #     """Helper function to initialize the Language Model."""
# # # # #     return ChatOpenAI(
# # # # #         model_name="llama3-70b-8192",
# # # # #         temperature=0,
# # # # #         api_key=settings['api_keys']['groq'],
# # # # #         base_url="https://api.groq.com/openai/v1"
# # # # #     )

# # # # # def _create_final_answer_chain(llm):
# # # # #     """Helper function to create the final answer formatting chain."""
# # # # #     final_answer_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

# # # # #         **Formatting Rules:**
# # # # #         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

# # # # #         **Table Display Rule:**
# # # # #         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
# # # # #         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

# # # # #         **Error and Invalid Query Handling:**
# # # # #         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
# # # # #         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

# # # # #         Original Question: {question}
# # # # #         SQL Result: {sql_result}
        
# # # # #         Final Answer:
# # # # #         """
# # # # #     )
# # # # #     return final_answer_prompt | llm | StrOutputParser()

# # # # # def _sql_sanitizer(response: str):
# # # # #     """
# # # # #     Robustly cleans and extracts the SQL query from the LLM output.
# # # # #     Removes triple backticks, 'sql' tags, quotes, and excess whitespace.
# # # # #     """
# # # # #     if not response:
# # # # #         return ""

# # # # #     # Extract from code block if exists
# # # # #     sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
# # # # #     if sql_match:
# # # # #         cleaned = sql_match.group(1)
# # # # #     else:
# # # # #         cleaned = response

# # # # #     # Remove stray backticks and SQL hints
# # # # #     cleaned = re.sub(r"```", "", cleaned)
# # # # #     cleaned = re.sub(r"(?i)^sql", "", cleaned).strip()

# # # # #     # Remove wrapping quotes if any
# # # # #     cleaned = cleaned.strip('"').strip("'").strip()

# # # # #     return cleaned

# # # # # # --- READ-ONLY CHAIN ---
# # # # # def get_read_only_chain():
# # # # #     llm = _create_llm()
    
# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are a master SQL architect. Given a user question and a database schema, your sole purpose is to generate a syntactically correct SQL query.

# # # # #         **RULES:**
# # # # #         1.  You are in a read-only environment. Only SELECT and WITH statements are allowed.
# # # # #         2.  Use only the tables and columns provided in the schema context.
# # # # #         3.  If the question is irrelevant, respond with the single word "INVALID".
# # # # #         4.  Your output MUST be ONLY the SQL query or the word "INVALID".

# # # # #         ---
# # # # #         **ADVANCED SQL EXAMPLES:**

# # # # #         **Example 1:**
# # # # #         User Question: "List employees whose salary is above the average salary of their department."
# # # # #         SQL Query: SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;

# # # # #         **Example 2:**
# # # # #         User Question: "Show each department and how many employees are in it, sorted by the highest count first."
# # # # #         SQL Query: SELECT d.department_name, COUNT(e.employee_id) AS num_employees FROM departments d JOIN employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY num_employees DESC;
# # # # #         ---

# # # # #         Question: {question}
# # # # #         Schema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # # #     def execute_read_only_query(query: str):
# # # # #         if not query or query.strip().upper() == "INVALID":
# # # # #             return "INVALID_QUERY"
        
# # # # #         query_upper = query.strip().upper()
# # # # #         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
# # # # #         if any(keyword in query_upper for keyword in blocked_keywords):
# # # # #             return "Error: Data modification commands are not allowed in Read-Only mode."

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 result = connection.execute(text(query))
# # # # #                 return [dict(row) for row in result.mappings()]
# # # # #         except Exception as e:
# # # # #             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         RunnablePassthrough.assign(
# # # # #             schema=RunnableLambda(lambda x: get_relevant_schema_from_pinecone(x["input"])), 
# # # # #             question=lambda x: x["input"]
# # # # #         )
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"])))
# # # # #         | final_answer_chain
# # # # #     )
# # # # #     return full_chain

# # # # # # --- READ-WRITE CHAIN ---
# # # # # def get_read_write_chain():
# # # # #     llm = _create_llm()

# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert SQL writer. Given a user command and a database schema, generate a SQL query to fulfill the request.
# # # # #         This can include SELECT, UPDATE, INSERT, or DELETE.
# # # # #         If the command is irrelevant, respond with "INVALID".
# # # # #         Only output the SQL query or "INVALID".
# # # # #         Command: {question}\nSchema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # # #     def execute_full_access_query(query: str):
# # # # #         if not query or query.strip().upper() == "INVALID":
# # # # #             return {"result": "INVALID_QUERY", "is_write": False}
        
# # # # #         is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE'))

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 if is_write_operation:
# # # # #                     with connection.begin() as transaction:
# # # # #                         connection.execute(text(query))
# # # # #                         transaction.commit()
# # # # #                     return {"result": "The command was executed successfully.", "is_write": True}
# # # # #                 else:
# # # # #                     result = connection.execute(text(query))
# # # # #                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
# # # # #         except Exception as e:
# # # # #             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
# # # # #         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
# # # # #         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
# # # # #     )
# # # # #     return full_chain

# # # # # # Create instances of both chains
# # # # # read_only_chain = get_read_only_chain()
# # # # # read_write_chain = get_read_write_chain()



# # # # # backend/agent/agent.py

# # # # # from langchain_openai import ChatOpenAI
# # # # # from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# # # # # from langchain_core.prompts import ChatPromptTemplate
# # # # # from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# # # # # from langchain_core.output_parsers import StrOutputParser
# # # # # from sqlalchemy import text

# # # # # from backend.database.connection import db
# # # # # from backend.core.config import settings

# # # # # def _create_llm():
# # # # #     """Helper function to initialize the Language Model."""
# # # # #     return ChatOpenAI(
# # # # #         model_name="llama3-70b-8192",
# # # # #         temperature=0,
# # # # #         api_key=settings['api_keys']['groq'],
# # # # #         base_url="https://api.groq.com/openai/v1"
# # # # #     )

# # # # # def _create_final_answer_chain(llm):
# # # # #     """Helper function to create the final answer formatting chain."""
# # # # #     final_answer_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

# # # # #         **Formatting Rules:**
# # # # #         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

# # # # #         **Table Display Rule:**
# # # # #         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
# # # # #         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

# # # # #         **Error and Invalid Query Handling:**
# # # # #         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
# # # # #         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

# # # # #         Original Question: {question}
# # # # #         SQL Result: {sql_result}
        
# # # # #         Final Answer:
# # # # #         """
# # # # #     )
# # # # #     return final_answer_prompt | llm | StrOutputParser()

# # # # # def get_read_only_chain():
# # # # #     """
# # # # #     Creates and returns a structured LangChain chain that can ONLY execute
# # # # #     read operations (SELECT statements) on the database.
# # # # #     """
# # # # #     llm = _create_llm()
    
# # # # #     # --- GOD-LEVEL FEW-SHOT PROMPT FOR COMPLEX READ QUERIES ---
# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are a master SQL architect. Given a user question and a database schema, generate a syntactically correct SQL query to answer the question.

# # # # #         **RULES:**
# # # # #         1.  You are in a read-only environment. Only non-destructive queries are allowed.
# # # # #         2.  When filtering string values, use case-insensitive comparisons (e.g., `LOWER()` or `ILIKE`).
# # # # #         3.  Think step-by-step. If a question requires multiple steps (e.g., finding an average then comparing to it), use subqueries or Common Table Expressions (CTEs).
# # # # #         4.  If the user's question is irrelevant to the schema, respond with the single word "INVALID".
# # # # #         5.  Only output the SQL query or the word "INVALID".

# # # # #         ---
# # # # #         **ADVANCED SQL EXAMPLES (FEW-SHOT LEARNING):**

# # # # #         **Example 1: Multi-Table JOIN**
# # # # #         User Question: "What is the department name for the employee named Alice Johnson?"
# # # # #         SQL Query: `SELECT T2.department_name FROM employees AS T1 INNER JOIN departments AS T2 ON T1.department_id = T2.department_id WHERE T1.first_name = 'Alice' AND T1.last_name = 'Johnson'`

# # # # #         **Example 2: Subquery for Comparison Against an Average**
# # # # #         User Question: "List employees whose salary is above the average salary of their department."
# # # # #         SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

# # # # #         **Example 3: GROUP BY with HAVING for Filtering Aggregates**
# # # # #         User Question: "Show the departments that have more than 2 employees."
# # # # #         SQL Query: `SELECT d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name HAVING COUNT(e.employee_id) > 2;`
        
# # # # #         **Example 4: Window Function for Ranking**
# # # # #         User Question: "Who are the top 2 highest-paid employees in each department?"
# # # # #         SQL Query: `WITH RankedSalaries AS (SELECT first_name, last_name, salary, department_id, ROW_NUMBER() OVER(PARTITION BY department_id ORDER BY salary DESC) as rank FROM employees) SELECT rs.first_name, rs.last_name, rs.salary, d.department_name FROM RankedSalaries rs JOIN departments d ON rs.department_id = d.department_id WHERE rs.rank <= 2;`
# # # # #         ---

# # # # #         **YOUR TASK:**

# # # # #         Question: {question}
# # # # #         Schema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm.bind(stop=["```"]) | StrOutputParser()

# # # # #     def execute_read_only_query(query: str):
# # # # #         if query.strip().upper() == "INVALID":
# # # # #             return "INVALID_QUERY"
        
# # # # #         query_upper = query.strip().upper()
# # # # #         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
        
# # # # #         if any(keyword in query_upper for keyword in blocked_keywords):
# # # # #             return "Error: Data modification commands like UPDATE, DELETE, etc., are not allowed in Read-Only mode."

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 result = connection.execute(text(query))
# # # # #                 return [dict(row) for row in result.mappings()]
# # # # #         except Exception as e:
# # # # #             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         # --- FIX: Revert to using the full schema for reliability ---
# # # # #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"])))
# # # # #         | final_answer_chain
# # # # #     )
# # # # #     return full_chain

# # # # # def get_read_write_chain():
# # # # #     """
# # # # #     Creates and returns a structured LangChain chain that can execute both
# # # # #     read and write operations on the database for admin users.
# # # # #     """
# # # # #     llm = _create_llm()

# # # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # # #         """You are an expert SQL writer. Given a user command and a database schema, generate a syntactically correct SQL query to fulfill the user's request.
        
# # # # #         This can include SELECT, UPDATE, INSERT, DELETE, and ALTER statements.

# # # # #         If the command is irrelevant to the schema, respond with the single word "INVALID".
        
# # # # #         Only output the SQL query or the word "INVALID".

# # # # #         Command: {question}
# # # # #         Schema: {schema}
# # # # #         """
# # # # #     )
# # # # #     sql_query_chain = sql_generation_prompt | llm.bind(stop=["```"]) | StrOutputParser()

# # # # #     def execute_full_access_query(query: str):
# # # # #         if query.strip().upper() == "INVALID":
# # # # #             return {"result": "INVALID_QUERY", "is_write": False}
        
# # # # #         query_upper = query.strip().upper()
# # # # #         # --- FIX: Add DDL commands to the write operation check ---
# # # # #         is_write_operation = query_upper.startswith(('UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE'))

# # # # #         try:
# # # # #             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
# # # # #             with db._engine.connect() as connection:
# # # # #                 if is_write_operation:
# # # # #                     with connection.begin() as transaction:
# # # # #                         connection.execute(text(query))
# # # # #                         transaction.commit()
# # # # #                     return {"result": "The command was executed successfully.", "is_write": True}
# # # # #                 else:
# # # # #                     result = connection.execute(text(query))
# # # # #                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
# # # # #         except Exception as e:
# # # # #             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

# # # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # # #     full_chain = (
# # # # #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# # # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # # #         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
# # # # #         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
# # # # #         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
# # # # #     )
# # # # #     return full_chain

# # # # # # Create instances of both chains
# # # # # read_only_chain = get_read_only_chain()
# # # # # read_write_chain = get_read_write_chain()


# # # # # backend/agent/agent.py

# # # # from langchain_openai import ChatOpenAI
# # # # from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# # # # from langchain_core.prompts import ChatPromptTemplate
# # # # from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# # # # from langchain_core.output_parsers import StrOutputParser
# # # # from sqlalchemy import text
# # # # from sentence_transformers import SentenceTransformer
# # # # from pinecone import Pinecone
# # # # import re

# # # # from backend.database.connection import db
# # # # from backend.core.config import settings

# # # # # --- ADVANCED RAG WITH PINECONE SETUP ---
# # # # PINECONE_API_KEY = settings['api_keys']['pinecone']
# # # # PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
# # # # EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# # # # # Initialize components for the RAG retriever
# # # # pc = Pinecone(api_key=PINECONE_API_KEY)
# # # # index = pc.Index(PINECONE_INDEX_NAME)
# # # # embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# # # # def get_relevant_schema_from_pinecone(query: str):
# # # #     """
# # # #     Embeds the user's query and retrieves the most relevant schema chunks
# # # #     from Pinecone. This is the core of our advanced RAG.
# # # #     """
# # # #     print(f"\n--- Retrieving relevant schema for query: '{query}' ---")
# # # #     query_embedding = embedding_model.encode(query).tolist()
# # # #     results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
# # # #     relevant_schema = "\n".join([match['metadata']['text'] for match in results['matches']])
# # # #     print(f"--- Retrieved Schema Context ---\n{relevant_schema}\n---------------------------------")
# # # #     return relevant_schema

# # # # # --- HELPER FUNCTIONS ---
# # # # def _create_llm():
# # # #     """Helper function to initialize the Language Model."""
# # # #     return ChatOpenAI(
# # # #         model_name="llama3-70b-8192",
# # # #         temperature=0,
# # # #         api_key=settings['api_keys']['groq'],
# # # #         base_url="https://api.groq.com/openai/v1"
# # # #     )

# # # # def _create_final_answer_chain(llm):
# # # #     """Helper function to create the final answer formatting chain."""
# # # #     final_answer_prompt = ChatPromptTemplate.from_template(
# # # #         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

# # # #         **Formatting Rules:**
# # # #         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

# # # #         **Table Display Rule:**
# # # #         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
# # # #         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

# # # #         **Error and Invalid Query Handling:**
# # # #         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
# # # #         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

# # # #         Original Question: {question}
# # # #         SQL Result: {sql_result}
        
# # # #         Final Answer:
# # # #         """
# # # #     )
# # # #     return final_answer_prompt | llm | StrOutputParser()

# # # # def _sql_sanitizer(response: str):
# # # #     """
# # # #     A final, super-robust guardrail to clean and extract a single SQL query
# # # #     from the LLM's potentially messy output.
# # # #     """
# # # #     if not response:
# # # #         return ""
    
# # # #     # 1. Extract from markdown block if it exists (handles ```sql ... ``` and ``` ... ```)
# # # #     sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
# # # #     if sql_match:
# # # #         cleaned = sql_match.group(1)
# # # #     else:
# # # #         cleaned = response

# # # #     # 2. Remove potential conversational prefixes like "Here is the query:"
# # # #     # We find the first SQL keyword and take everything from that point onwards.
# # # #     sql_keywords = ['SELECT', 'WITH', 'UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE']
# # # #     start_pos = -1
# # # #     cleaned_upper = cleaned.upper()
# # # #     for keyword in sql_keywords:
# # # #         pos = cleaned_upper.find(keyword)
# # # #         if pos != -1:
# # # #             # Check if this is the earliest keyword found
# # # #             if start_pos == -1 or pos < start_pos:
# # # #                 start_pos = pos
    
# # # #     if start_pos != -1:
# # # #         cleaned = cleaned[start_pos:]
    
# # # #     # 3. Remove wrapping quotes (single, double, or triple) and trailing semicolons
# # # #     cleaned = cleaned.strip().rstrip(';').strip()
# # # #     if (cleaned.startswith('"') and cleaned.endswith('"')) or \
# # # #        (cleaned.startswith("'") and cleaned.endswith("'")):
# # # #         cleaned = cleaned[1:-1]
# # # #     if (cleaned.startswith('"""') and cleaned.endswith('"""')):
# # # #         cleaned = cleaned[3:-3]
        
# # # #     return cleaned.strip()

# # # # # --- READ-ONLY CHAIN (NOW WITH PINECONE RAG AND FEW-SHOT PROMPTING) ---
# # # # def get_read_only_chain():
# # # #     llm = _create_llm()
    
# # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # #         """You are a master SQL architect. Given a user question and a database schema, your sole purpose is to generate a syntactically correct SQL query.

# # # #         **RULES:**
# # # #         1.  You are in a read-only environment. Only SELECT and WITH statements are allowed.
# # # #         2.  Use only the tables and columns provided in the schema context.
# # # #         3.  If the question is irrelevant, respond with the single word "INVALID".
# # # #         4.  Your output MUST be ONLY the SQL query or the word "INVALID".

# # # #         ---
# # # #         **ADVANCED SQL EXAMPLES:**

# # # #         **Example 1: Subquery for Comparison Against an Average**
# # # #         User Question: "List employees whose salary is above the average salary of their department."
# # # #         SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

# # # #         **Example 2: GROUP BY with HAVING for Filtering Aggregates**
# # # #         User Question: "Show each department and how many employees are in it, sorted by the highest count first."
# # # #         SQL Query: `SELECT d.department_name, COUNT(e.employee_id) AS num_employees FROM departments d JOIN employees e ON d.department_id = e.department_id GROUP BY d.department_name ORDER BY num_employees DESC;`
# # # #         ---

# # # #         **YOUR TASK:**

# # # #         Question: {question}
# # # #         Schema: {schema}
# # # #         """
# # # #     )
# # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # #     def execute_read_only_query(query: str):
# # # #         if not query or query.strip().upper() == "INVALID":
# # # #             return "INVALID_QUERY"
        
# # # #         query_upper = query.strip().upper()
# # # #         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
# # # #         if any(keyword in query_upper for keyword in blocked_keywords):
# # # #             return "Error: Data modification commands are not allowed in Read-Only mode."

# # # #         try:
# # # #             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
# # # #             with db._engine.connect() as connection:
# # # #                 result = connection.execute(text(query))
# # # #                 return [dict(row) for row in result.mappings()]
# # # #         except Exception as e:
# # # #             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

# # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # #     full_chain = (
# # # #         RunnablePassthrough.assign(
# # # #             schema=RunnableLambda(lambda x: get_relevant_schema_from_pinecone(x["input"])), 
# # # #             question=lambda x: x["input"]
# # # #         )
# # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # #         | RunnablePassthrough.assign(sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"])))
# # # #         | final_answer_chain
# # # #     )
# # # #     return full_chain

# # # # # --- READ-WRITE CHAIN (UNCHANGED) ---
# # # # def get_read_write_chain():
# # # #     llm = _create_llm()

# # # #     sql_generation_prompt = ChatPromptTemplate.from_template(
# # # #         """You are an expert SQL writer. Given a user command and a database schema, generate a SQL query to fulfill the request.
# # # #         This can include SELECT, UPDATE, INSERT, or DELETE.
# # # #         If the command is irrelevant, respond with "INVALID".
# # # #         Only output the SQL query or "INVALID".
# # # #         Command: {question}\nSchema: {schema}
# # # #         """
# # # #     )
# # # #     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

# # # #     def execute_full_access_query(query: str):
# # # #         if not query or query.strip().upper() == "INVALID":
# # # #             return {"result": "INVALID_QUERY", "is_write": False}
        
# # # #         is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE'))

# # # #         try:
# # # #             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
# # # #             with db._engine.connect() as connection:
# # # #                 if is_write_operation:
# # # #                     with connection.begin() as transaction:
# # # #                         connection.execute(text(query))
# # # #                         transaction.commit()
# # # #                     return {"result": "The command was executed successfully.", "is_write": True}
# # # #                 else:
# # # #                     result = connection.execute(text(query))
# # # #                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
# # # #         except Exception as e:
# # # #             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

# # # #     final_answer_chain = _create_final_answer_chain(llm)

# # # #     full_chain = (
# # # #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# # # #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# # # #         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
# # # #         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
# # # #         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
# # # #     )
# # # #     return full_chain

# # # # # Create instances of both chains
# # # # read_only_chain = get_read_only_chain()
# # # # read_write_chain = get_read_write_chain()



# # # # backend/agent/agent.py

# # from langchain_openai import ChatOpenAI
# # from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# # from langchain_core.prompts import ChatPromptTemplate
# # from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# # from langchain_core.output_parsers import StrOutputParser
# # from sqlalchemy import text
# # from sentence_transformers import SentenceTransformer
# # from pinecone import Pinecone
# # import re

# # from backend.database.connection import db
# # from backend.core.config import settings

# # # --- ADVANCED RAG WITH PINECONE SETUP ---
# # PINECONE_API_KEY = settings['api_keys']['pinecone']
# # PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
# # EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# # # Initialize components for the RAG retriever
# # pc = Pinecone(api_key=PINECONE_API_KEY)
# # index = pc.Index(PINECONE_INDEX_NAME)
# # embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# # def get_hybrid_schema_context(query: str):
# #     """
# #     The definitive fix: A hybrid retriever that combines a full table list
# #     with intelligently retrieved, relevant column details from Pinecone.
# #     """
# #     print(f"\n--- Retrieving hybrid schema for query: '{query}' ---")
    
# #     # 1. Always get the list of all table names
# #     all_table_names = db.get_table_names()
# #     table_list_context = f"All available tables in the database: {', '.join(all_table_names)}"
    
# #     # 2. Use Pinecone to find the most relevant columns for the query
# #     query_embedding = embedding_model.encode(query).tolist()
# #     results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
# #     pinecone_context = "\n".join([match['metadata']['text'] for match in results['matches']])
    
# #     # 3. Combine both contexts
# #     hybrid_context = f"{table_list_context}\n\nHere are the most relevant table and column details for your query:\n{pinecone_context}"
# #     print(f"--- Retrieved Hybrid Schema Context ---\n{hybrid_context}\n---------------------------------")
# #     return hybrid_context

# # # --- HELPER FUNCTIONS ---
# # def _create_llm():
# #     """Helper function to initialize the Language Model."""
# #     return ChatOpenAI(
# #         model_name="llama3-70b-8192",
# #         temperature=0,
# #         api_key=settings['api_keys']['groq'],
# #         base_url="https://api.groq.com/openai/v1"
# #     )

# # def _create_final_answer_chain(llm):
# #     """Helper function to create the final answer formatting chain."""
# #     final_answer_prompt = ChatPromptTemplate.from_template(
# #         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

# #         **Formatting Rules:**
# #         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

# #         **Table Display Rule:**
# #         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
# #         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

# #         **Error and Invalid Query Handling:**
# #         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
# #         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

# #         Original Question: {question}
# #         SQL Result: {sql_result}
        
# #         Final Answer:
# #         """
# #     )
# #     return final_answer_prompt | llm | StrOutputParser()

# # # --- GOD-LEVEL PROMPT TEMPLATE (Used by both chains) ---
# # GOD_LEVEL_PROMPT_TEMPLATE = """You are a master SQL architect. Given a user question and a database schema, generate a syntactically correct SQL query to answer the question.

# # **RULES:**
# # 1.  Use only the tables and columns provided in the schema context.
# # 2.  When filtering string values, use case-insensitive comparisons (e.g., `LOWER()` or `ILIKE`).
# # 3.  Think step-by-step. If a question requires multiple steps (e.g., finding an average then comparing to it), use subqueries or Common Table Expressions (CTEs).
# # 4.  If the user's question is irrelevant to the schema, respond with the single word "INVALID".
# # 5.  Your output MUST be ONLY the SQL query or the word "INVALID".

# # ---
# # **ADVANCED SQL EXAMPLES (FEW-SHOT LEARNING):**

# # **Example 1: Using IN for Subqueries that may return multiple rows**
# # User Question: "Show me employees in the Finance department."
# # SQL Query: `SELECT * FROM employees WHERE department_id IN (SELECT department_id FROM departments WHERE department_name ILIKE '%Finance%');`

# # **Example 2: Subquery for Comparison Against an Average**
# # User Question: "List employees whose salary is above the average salary of their department."
# # SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

# # **Example 3: GROUP BY with HAVING for Filtering Aggregates**
# # User Question: "Show the departments that have more than 2 employees."
# # SQL Query: `SELECT d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name HAVING COUNT(e.employee_id) > 2;`
# # ---

# # **YOUR TASK:**

# # Question: {question}
# # Schema: {schema}
# # """

# # # --- READ-ONLY CHAIN (NOW WITH HYBRID RAG) ---
# # def get_read_only_chain():
# #     llm = _create_llm()
    
# #     sql_generation_prompt = ChatPromptTemplate.from_template(
# #         GOD_LEVEL_PROMPT_TEMPLATE.replace(
# #             "Only SELECT and WITH statements are allowed.",
# #             "You are in a read-only environment. Only SELECT and WITH statements are allowed."
# #         )
# #     )
# #     sql_query_chain = sql_generation_prompt | llm.bind(stop=["```"]) | StrOutputParser()

# #     def execute_read_only_query(query: str):
# #         if not query or query.strip().upper() == "INVALID":
# #             return "INVALID_QUERY"
        
# #         query_upper = query.strip().upper()
# #         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
# #         if any(keyword in query_upper for keyword in blocked_keywords):
# #             return "Error: Data modification commands are not allowed in Read-Only mode."

# #         try:
# #             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
# #             with db._engine.connect() as connection:
# #                 result = connection.execute(text(query))
# #                 return [dict(row) for row in result.mappings()]
# #         except Exception as e:
# #             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

# #     final_answer_chain = _create_final_answer_chain(llm)

# #     full_chain = (
# #         RunnablePassthrough.assign(
# #             schema=RunnableLambda(lambda x: get_hybrid_schema_context(x["input"])), 
# #             question=lambda x: x["input"]
# #         )
# #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# #         | RunnablePassthrough.assign(sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"])))
# #         | final_answer_chain
# #     )
# #     return full_chain

# # # --- READ-WRITE CHAIN (NOW WITH GOD-LEVEL PROMPT) ---
# # def get_read_write_chain():
# #     llm = _create_llm()

# #     # Admin mode now also uses the god-level prompt for read queries, but can also generate write queries.
# #     admin_sql_generation_prompt = ChatPromptTemplate.from_template(
# #         GOD_LEVEL_PROMPT_TEMPLATE.replace(
# #             "Only SELECT and WITH statements are allowed.",
# #             "SELECT, UPDATE, INSERT, DELETE, and ALTER statements are allowed."
# #         )
# #     )
# #     sql_query_chain = admin_sql_generation_prompt | llm.bind(stop=["```"]) | StrOutputParser()

# #     def execute_full_access_query(query: str):
# #         if not query or query.strip().upper() == "INVALID":
# #             return {"result": "INVALID_QUERY", "is_write": False}
        
# #         is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE'))

# #         try:
# #             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
# #             with db._engine.connect() as connection:
# #                 if is_write_operation:
# #                     with connection.begin() as transaction:
# #                         connection.execute(text(query))
# #                         transaction.commit()
# #                     return {"result": "The command was executed successfully.", "is_write": True}
# #                 else:
# #                     result = connection.execute(text(query))
# #                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
# #         except Exception as e:
# #             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

# #     final_answer_chain = _create_final_answer_chain(llm)

# #     full_chain = (
# #         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
# #         | RunnablePassthrough.assign(sql_query=sql_query_chain)
# #         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
# #         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
# #         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
# #     )
# #     return full_chain

# # # Create instances of both chains
# # read_only_chain = get_read_only_chain()
# # read_write_chain = get_read_write_chain()


# # backend/agent/agent.py

# from langchain_openai import ChatOpenAI
# from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# from langchain_core.output_parsers import StrOutputParser
# from sqlalchemy import text
# from sentence_transformers import SentenceTransformer
# from pinecone import Pinecone
# import re

# from backend.database.connection import db
# from backend.core.config import settings

# # --- ADVANCED RAG WITH PINECONE SETUP ---
# PINECONE_API_KEY = settings['api_keys']['pinecone']
# PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
# EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# # Initialize components for the RAG retriever
# pc = Pinecone(api_key=PINECONE_API_KEY)
# index = pc.Index(PINECONE_INDEX_NAME)
# embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# def get_hybrid_schema_context(query: str):
#     """
#     A hybrid retriever that combines a full table list
#     with intelligently retrieved, relevant column details from Pinecone.
#     """
#     print(f"\n--- Retrieving hybrid schema for query: '{query}' ---")
    
#     all_table_names = db.get_table_names()
#     table_list_context = f"All available tables in the database: {', '.join(all_table_names)}"
    
#     query_embedding = embedding_model.encode(query).tolist()
#     results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
#     pinecone_context = "\n".join([match['metadata']['text'] for match in results['matches']])
    
#     hybrid_context = f"{table_list_context}\n\nHere are the most relevant table and column details for your query:\n{pinecone_context}"
#     print(f"--- Retrieved Hybrid Schema Context ---\n{hybrid_context}\n---------------------------------")
#     return hybrid_context

# # --- HELPER FUNCTIONS ---
# def _create_llm():
#     """Helper function to initialize the Language Model."""
#     return ChatOpenAI(
#         model_name="llama3-70b-8192",
#         temperature=0,
#         api_key=settings['api_keys']['groq'],
#         base_url="https://api.groq.com/openai/v1"
#     )

# def _create_final_answer_chain(llm):
#     """Helper function to create the final answer formatting chain."""
#     final_answer_prompt = ChatPromptTemplate.from_template(
#         """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL() query.

#         **Formatting Rules:**
#         - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

#         **Table Display Rule:**
#         - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
#         - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

#         **Error and Invalid Query Handling:**
#         - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
#         - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

#         Original Question: {question}
#         SQL Result: {sql_result}
        
#         Final Answer:
#         """
#     )
#     return final_answer_prompt | llm | StrOutputParser()

# def _sql_sanitizer(response: str):
#     """
#     A final, super-robust guardrail to clean and extract a single SQL query
#     from the LLM's potentially messy output.
#     """
#     if not response:
#         return ""
    
#     # 1. Extract from markdown block if it exists (handles ```sql ... ``` and ``` ... ```)
#     sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
#     if sql_match:
#         cleaned = sql_match.group(1)
#     else:
#         cleaned = response

#     # 2. Remove potential conversational prefixes like "Here is the query:"
#     # We find the first SQL keyword and take everything from that point onwards.
#     sql_keywords = ['SELECT', 'WITH', 'UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE']
#     start_pos = -1
#     cleaned_upper = cleaned.upper()
#     for keyword in sql_keywords:
#         pos = cleaned_upper.find(keyword)
#         if pos != -1:
#             # Check if this is the earliest keyword found
#             if start_pos == -1 or pos < start_pos:
#                 start_pos = pos
    
#     if start_pos != -1:
#         cleaned = cleaned[start_pos:]
    
#     # 3. Remove wrapping quotes (single, double, or triple) and trailing semicolons
#     cleaned = cleaned.strip().rstrip(';').strip()
#     if (cleaned.startswith('"') and cleaned.endswith('"')) or \
#        (cleaned.startswith("'") and cleaned.endswith("'")):
#         cleaned = cleaned[1:-1]
#     if (cleaned.startswith('"""') and cleaned.endswith('"""')):
#         cleaned = cleaned[3:-3]
        
#     return cleaned.strip()

# # --- GOD-LEVEL PROMPT TEMPLATE (Used by both chains) ---
# GOD_LEVEL_PROMPT_TEMPLATE = """You are a master SQL architect. Given a user question and a database schema, generate a syntactically correct SQL query to answer the question.

# **RULES:**
# 1.  Use only the tables and columns provided in the schema context.
# 2.  When filtering string values, use case-insensitive comparisons (e.g., `LOWER()` or `ILIKE`).
# 3.  Think step-by-step. If a question requires multiple steps (e.g., finding an average then comparing to it), use subqueries or Common Table Expressions (CTEs).
# 4.  If the user's question is irrelevant to the schema, respond with the single word "INVALID".
# 5.  Your output MUST be ONLY the SQL query or the word "INVALID".

# ---
# **ADVANCED SQL EXAMPLES (FEW-SHOT LEARNING):**

# **Example 1: Using IN for Subqueries that may return multiple rows**
# User Question: "Show me employees in the Finance department."
# SQL Query: `SELECT * FROM employees WHERE department_id IN (SELECT department_id FROM departments WHERE department_name ILIKE '%Finance%');`

# **Example 2: Subquery for Comparison Against an Average**
# User Question: "List employees whose salary is above the average salary of their department."
# SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

# **Example 3: GROUP BY with HAVING for Filtering Aggregates**
# User Question: "Show the departments that have more than 2 employees."
# SQL Query: `SELECT d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name HAVING COUNT(e.employee_id) > 2;`
# ---

# **YOUR TASK:**

# Question: {question}
# Schema: {schema}
# """

# # --- READ-ONLY CHAIN (NOW WITH HYBRID RAG) ---
# def get_read_only_chain():
#     llm = _create_llm()
    
#     sql_generation_prompt = ChatPromptTemplate.from_template(
#         GOD_LEVEL_PROMPT_TEMPLATE.replace(
#             "Only SELECT and WITH statements are allowed.",
#             "You are in a read-only environment. Only SELECT and WITH statements are allowed."
#         )
#     )
#     sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

#     def execute_read_only_query(query: str):
#         if not query or query.strip().upper() == "INVALID":
#             return "INVALID_QUERY"
        
#         query_upper = query.strip().upper()
#         blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
#         if any(keyword in query_upper for keyword in blocked_keywords):
#             return "Error: Data modification commands are not allowed in Read-Only mode."

#         try:
#             print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
#             with db._engine.connect() as connection:
#                 result = connection.execute(text(query))
#                 return [dict(row) for row in result.mappings()]
#         except Exception as e:
#             return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

#     final_answer_chain = _create_final_answer_chain(llm)

#     full_chain = (
#         RunnablePassthrough.assign(
#             schema=RunnableLambda(lambda x: get_hybrid_schema_context(x["input"])),
#             question=lambda x: x["input"]
#         )
#         | RunnablePassthrough.assign(
#             sql_query=sql_query_chain
#         )
#         | RunnablePassthrough.assign(
#             sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"]))
#         )
#         | final_answer_chain
#     )
#     return full_chain

# # --- READ-WRITE CHAIN (NOW WITH GOD-LEVEL PROMPT) ---
# def get_read_write_chain():
#     llm = _create_llm()

#     admin_sql_generation_prompt = ChatPromptTemplate.from_template(
#         GOD_LEVEL_PROMPT_TEMPLATE.replace(
#             "Only SELECT and WITH statements are allowed.",
#             "SELECT, UPDATE, INSERT, DELETE, and ALTER statements are allowed."
#         )
#     )
#     sql_query_chain = admin_sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

#     def execute_full_access_query(query: str):
#         if not query or query.strip().upper() == "INVALID":
#             return {"result": "INVALID_QUERY", "is_write": False}
        
#         is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE'))

#         try:
#             print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
#             with db._engine.connect() as connection:
#                 if is_write_operation:
#                     with connection.begin() as transaction:
#                         connection.execute(text(query))
#                         transaction.commit()
#                     return {"result": "The command was executed successfully.", "is_write": True}
#                 else:
#                     result = connection.execute(text(query))
#                     return {"result": [dict(row) for row in result.mappings()], "is_write": False}
#         except Exception as e:
#             return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

#     final_answer_chain = _create_final_answer_chain(llm)

#     full_chain = (
#         RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
#         | RunnablePassthrough.assign(sql_query=sql_query_chain)
#         | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
#         | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
#         | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
#     )
#     return full_chain

# # Create instances of both chains
# read_only_chain = get_read_only_chain()
# read_write_chain = get_read_write_chain()


# backend/agent/agent.py

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import re

from backend.database.connection import db
from backend.core.config import settings

# --- ADVANCED RAG WITH PINECONE SETUP ---
PINECONE_API_KEY = settings['api_keys']['pinecone']
PINECONE_INDEX_NAME = "auto-sql-gpt-schema"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# Initialize components for the RAG retriever
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

def get_hybrid_schema_context(query: str):
    """
    A hybrid retriever that combines a full table list
    with intelligently retrieved, relevant column details from Pinecone.
    """
    print(f"\n--- Retrieving hybrid schema for query: '{query}' ---")
    
    all_table_names = db.get_table_names()
    table_list_context = f"All available tables in the database: {', '.join(all_table_names)}"
    
    query_embedding = embedding_model.encode(query).tolist()
    results = index.query(vector=query_embedding, top_k=7, include_metadata=True)
    pinecone_context = "\n".join([match['metadata']['text'] for match in results['matches']])
    
    hybrid_context = f"{table_list_context}\n\nHere are the most relevant table and column details for your query:\n{pinecone_context}"
    print(f"--- Retrieved Hybrid Schema Context ---\n{hybrid_context}\n---------------------------------")
    return hybrid_context

# --- HELPER FUNCTIONS ---
def _create_llm():
    """Helper function to initialize the Language Model."""
    return ChatOpenAI(
        model_name="llama3-70b-8192",
        temperature=0,
        api_key=settings['api_keys']['groq'],
        base_url="https://api.groq.com/openai/v1"
    )

def _create_final_answer_chain(llm):
    """Helper function to create the final answer formatting chain."""
    final_answer_prompt = ChatPromptTemplate.from_template(
        """You are an expert AI assistant. Your job is to provide a clear, readable, and informative natural language answer to the user's question based on the result of a SQL query.

        **Formatting Rules:**
        - Structure your answers clearly. Use bullet points or numbered lists if it improves readability.

        **Table Display Rule:**
        - If the user's original question contains verbs like "show", "list", "display", "what are", or "who are", and the SQL result is not an error, you MUST include a markdown-formatted table of the SQL results in your final answer, in addition to your natural language summary.
        - If the question is asking for a single value (e.g., "how many"), do NOT include a table.

        **Error and Invalid Query Handling:**
        - If the SQL Result is "INVALID_QUERY", you MUST respond with: "Sorry, that question seems irrelevant to the database."
        - If the SQL Result starts with "Error:", inform the user that there was a problem running the query and provide the details.

        Original Question: {question}
        SQL Result: {sql_result}
        
        Final Answer:
        """
    )
    return final_answer_prompt | llm | StrOutputParser()

def _sql_sanitizer(response: str):
    """
    A final, super-robust guardrail to clean and extract a single SQL query
    from the LLM's potentially messy output.
    """
    if not response:
        return ""
    
    # 1. Extract from markdown block if it exists (handles ```sql ... ``` and ``` ... ```)
    sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        cleaned = sql_match.group(1)
    else:
        cleaned = response

    # 2. Remove potential conversational prefixes like "Here is the query:"
    # We find the first SQL keyword and take everything from that point onwards.
    sql_keywords = ['SELECT', 'WITH', 'UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE']
    start_pos = -1
    cleaned_upper = cleaned.upper()
    for keyword in sql_keywords:
        pos = cleaned_upper.find(keyword)
        if pos != -1:
            # Check if this is the earliest keyword found
            if start_pos == -1 or pos < start_pos:
                start_pos = pos
    
    if start_pos != -1:
        cleaned = cleaned[start_pos:]
    
    # 3. Remove wrapping quotes (single, double, or triple) and trailing semicolons
    cleaned = cleaned.strip().rstrip(';').strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")) or \
       (cleaned.startswith('`') and cleaned.endswith('`')):
        cleaned = cleaned[1:-1]
    if (cleaned.startswith('"""') and cleaned.endswith('"""')):
        cleaned = cleaned[3:-3]
        
    return cleaned.strip()

# --- GOD-LEVEL PROMPT TEMPLATE (Used by both chains) ---
GOD_LEVEL_PROMPT_TEMPLATE = """You are a master SQL architect. Given a user question and a database schema, generate a syntactically correct SQL query to answer the question.

**RULES:**
1.  Use only the tables and columns provided in the schema context.
2.  When filtering string values, use case-insensitive comparisons (e.g., `LOWER()` or `ILIKE`).
3.  Think step-by-step. If a question requires multiple steps (e.g., finding an average then comparing to it), use subqueries or Common Table Expressions (CTEs).
4.  If the user's question is irrelevant to the schema, respond with the single word "INVALID".
5.  Your output MUST be ONLY the SQL query or the word "INVALID".

---
**ADVANCED SQL EXAMPLES (FEW-SHOT LEARNING):**

**Example 1: Using IN for Subqueries that may return multiple rows**
User Question: "Show me employees in the Finance department."
SQL Query: `SELECT * FROM employees WHERE department_id IN (SELECT department_id FROM departments WHERE department_name ILIKE '%Finance%');`

**Example 2: Subquery for Comparison Against an Average**
User Question: "List employees whose salary is above the average salary of their department."
SQL Query: `SELECT e.first_name, e.last_name, d.department_name, e.salary, avg_sal.department_avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN (SELECT department_id, AVG(salary) as department_avg_salary FROM employees GROUP BY department_id) avg_sal ON e.department_id = avg_sal.department_id WHERE e.salary > avg_sal.department_avg_salary ORDER BY e.salary DESC;`

**Example 3: GROUP BY with HAVING for Filtering Aggregates**
User Question: "Show the departments that have more than 2 employees."
SQL Query: `SELECT d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name HAVING COUNT(e.employee_id) > 2;`
---

**YOUR TASK:**

Question: {question}
Schema: {schema}
"""

# --- READ-ONLY CHAIN (NOW WITH HYBRID RAG) ---
def get_read_only_chain():
    llm = _create_llm()
    
    sql_generation_prompt = ChatPromptTemplate.from_template(
        GOD_LEVEL_PROMPT_TEMPLATE.replace(
            "Only SELECT and WITH statements are allowed.",
            "You are in a read-only environment. Only SELECT and WITH statements are allowed."
        )
    )
    sql_query_chain = sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

    def execute_read_only_query(query: str):
        if not query or query.strip().upper() == "INVALID":
            return "INVALID_QUERY"
        
        query_upper = query.strip().upper()
        blocked_keywords = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
        if any(keyword in query_upper for keyword in blocked_keywords):
            return "Error: Data modification commands are not allowed in Read-Only mode."

        try:
            print(f"\n--- EXECUTING READ-ONLY SQL QUERY ---\n{query}\n---------------------------\n")
            with db._engine.connect() as connection:
                result = connection.execute(text(query))
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            return f"Error: The following SQL query failed: `{query}`. Error details: {e}"

    final_answer_chain = _create_final_answer_chain(llm)

    full_chain = (
        RunnablePassthrough.assign(
            schema=RunnableLambda(lambda x: get_hybrid_schema_context(x["input"])),
            question=lambda x: x["input"]
        )
        | RunnablePassthrough.assign(
            sql_query=sql_query_chain
        )
        | RunnablePassthrough.assign(
            sql_result=RunnableLambda(lambda x: execute_read_only_query(x["sql_query"]))
        )
        | final_answer_chain
    )
    return full_chain

# --- READ-WRITE CHAIN (NOW WITH GOD-LEVEL PROMPT) ---
def get_read_write_chain():
    llm = _create_llm()

    admin_sql_generation_prompt = ChatPromptTemplate.from_template(
        GOD_LEVEL_PROMPT_TEMPLATE.replace(
            "Only SELECT and WITH statements are allowed.",
            "SELECT, UPDATE, INSERT, DELETE, and ALTER statements are allowed."
        )
    )
    sql_query_chain = admin_sql_generation_prompt | llm | StrOutputParser() | RunnableLambda(_sql_sanitizer)

    def execute_full_access_query(query: str):
        if not query or query.strip().upper() == "INVALID":
            return {"result": "INVALID_QUERY", "is_write": False}
        
        is_write_operation = query.strip().upper().startswith(('UPDATE', 'INSERT', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE'))

        try:
            print(f"\n--- EXECUTING ADMIN SQL QUERY ---\n{query}\n---------------------------\n")
            with db._engine.connect() as connection:
                if is_write_operation:
                    with connection.begin() as transaction:
                        connection.execute(text(query))
                        transaction.commit()
                    return {"result": "The command was executed successfully.", "is_write": True}
                else:
                    result = connection.execute(text(query))
                    return {"result": [dict(row) for row in result.mappings()], "is_write": False}
        except Exception as e:
            return {"result": f"Error: The following SQL query failed: `{query}`. Error details: {e}", "is_write": False}

    final_answer_chain = _create_final_answer_chain(llm)

    full_chain = (
        RunnablePassthrough.assign(schema=RunnableLambda(lambda x: db.get_table_info()), question=lambda x: x["input"])
        | RunnablePassthrough.assign(sql_query=sql_query_chain)
        | RunnablePassthrough.assign(execution_output=RunnableLambda(lambda x: execute_full_access_query(x["sql_query"])))
        | RunnablePassthrough.assign(sql_result=lambda x: x["execution_output"]["result"], is_write=lambda x: x["execution_output"]["is_write"])
        | {"answer": final_answer_chain, "is_write": RunnableLambda(lambda x: x["is_write"])}
    )
    return full_chain

# Create instances of both chains
read_only_chain = get_read_only_chain()
read_write_chain = get_read_write_chain()
