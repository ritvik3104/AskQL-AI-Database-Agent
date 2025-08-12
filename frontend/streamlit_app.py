# # # # frontend/streamlit_app.py

# # # import streamlit as st
# # # import requests

# # # # --- Page Configuration ---
# # # st.set_page_config(
# # #     page_title="Auto SQL GPT - Professional",
# # #     page_icon="🤖",
# # #     layout="centered" 
# # # )

# # # # --- Custom CSS for Navy Blue Professional UI ---
# # # st.markdown("""
# # # <style>
# # #     /* Main App Styling */
# # #     .stApp {
# # #         background-color: #0a192f; /* Navy Blue */
# # #         color: #ccd6f6;
# # #     }
    
# # #     /* Title Styling */
# # #     h1 {
# # #         color: #64ffda; /* A vibrant accent color */
# # #     }

# # #     /* Button Styling */
# # #     .stButton > button {
# # #         color: #64ffda;
# # #         border: 1px solid #64ffda;
# # #         background-color: transparent;
# # #         border-radius: 4px;
# # #         padding: 0.75em 1em;
# # #         width: 100%;
# # #     }
# # #     .stButton > button:hover {
# # #         background-color: rgba(100, 255, 218, 0.1);
# # #         color: #64ffda;
# # #         border-color: #64ffda;
# # #     }
    
# # #     /* Text Input Styling */
# # #     .stTextInput > div > div > input {
# # #         background-color: #1d2d44;
# # #         color: #ccd6f6;
# # #         border: 1px solid #2e3d54;
# # #     }

# # #     /* Chat Message Styling */
# # #     .stChatMessage {
# # #         background-color: #1d2d44;
# # #         border-radius: 8px;
# # #         padding: 1.2em;
# # #         border: 1px solid #2e3d54;
# # #     }

# # #     /* Markdown link styling */
# # #     .stMarkdown a {
# # #         color: #64ffda;
# # #     }
    
# # #     /* Sub-header text */
# # #     .stMarkdown p, .st-emotion-cache-1yycg8b p {
# # #         color: #8892b0;
# # #     }

# # #     /* Styling for Markdown Tables */
# # #     .stMarkdown table {
# # #         width: auto;
# # #         color: #ccd6f6;
# # #         background-color: #2e3d54;
# # #         border-collapse: collapse;
# # #     }
# # #     .stMarkdown th {
# # #         background-color: #4a607c;
# # #         color: #ffffff;
# # #         padding: 8px;
# # #         border: 1px solid #1d2d44;
# # #     }
# # #     .stMarkdown td {
# # #         padding: 8px;
# # #         border: 1px solid #1d2d44;
# # #     }

# # # </style>
# # # """, unsafe_allow_html=True)


# # # # --- API Configuration ---
# # # BACKEND_URL = "http://127.0.0.1:8000"

# # # # --- Session State Initialization ---
# # # if "role" not in st.session_state:
# # #     st.session_state.role = None
# # # if "messages" not in st.session_state:
# # #     st.session_state.messages = []
# # # if "authenticated" not in st.session_state:
# # #     st.session_state.authenticated = False
# # # if "db_name" not in st.session_state:
# # #     st.session_state.db_name = None

# # # # --- Main App Logic ---

# # # # 1. Role Selection Screen
# # # if st.session_state.role is None:
# # #     st.title("Welcome to Auto SQL GPT")
# # #     st.write("Please select your role to begin.")
    
# # #     col1, col2 = st.columns(2)
# # #     with col1:
# # #         if st.button("Read/View Only Access", use_container_width=True):
# # #             st.session_state.role = "read_only"
# # #             st.rerun()
# # #     with col2:
# # #         if st.button("Admin Access", use_container_width=True):
# # #             st.session_state.role = "admin"
# # #             st.rerun()

# # # # 2. Admin Password Screen
# # # elif st.session_state.role == "admin" and not st.session_state.authenticated:
# # #     st.title("Admin Authentication")
# # #     password = st.text_input("Please enter the admin password:", type="password")
    
# # #     if st.button("Login"):
# # #         try:
# # #             response = requests.post(f"{BACKEND_URL}/authenticate", json={"password": password})
# # #             if response.status_code == 200:
# # #                 st.session_state.authenticated = True
# # #                 st.rerun()
# # #             else:
# # #                 st.error("Incorrect password. Please try again.")
# # #         except requests.RequestException as e:
# # #             st.error(f"Could not connect to the backend: {e}")
    
# # #     if st.button("← Go Back"):
# # #         st.session_state.role = None
# # #         st.rerun()

# # # # 3. Main Chat Interface
# # # else:
# # #     # Fetch the database name once
# # #     if st.session_state.db_name is None:
# # #         try:
# # #             response = requests.get(f"{BACKEND_URL}/db-info")
# # #             if response.status_code == 200:
# # #                 st.session_state.db_name = response.json().get("active_database", "Unknown")
# # #             else:
# # #                 st.session_state.db_name = "Error"
# # #         except requests.RequestException:
# # #             st.session_state.db_name = "Unavailable"

# # #     st.title("🤖 Auto SQL GPT - Professional Edition")
# # #     role_display = "Admin" if st.session_state.role == "admin" else "Read-Only"
# # #     st.markdown(f"**Mode:** {role_display} | **Connected to:** {st.session_state.db_name}")

# # #     # Display chat history
# # #     for message in st.session_state.messages:
# # #         with st.chat_message(message["role"]):
# # #             st.markdown(message["content"], unsafe_allow_html=True)

# # #     # Chat input
# # #     if prompt := st.chat_input("e.g., How many people are in London?"):
# # #         st.session_state.messages.append({"role": "user", "content": prompt})
# # #         with st.chat_message("user"):
# # #             st.markdown(prompt)

# # #         with st.chat_message("assistant"):
# # #             with st.spinner("Thinking..."):
# # #                 try:
# # #                     payload = {
# # #                         "query": prompt,
# # #                         "role": st.session_state.role,
# # #                         "chat_history": [
# # #                             {"type": msg["role"], "content": msg["content"]}
# # #                             for msg in st.session_state.messages[:-1]
# # #                         ]
# # #                     }
# # #                     response = requests.post(f"{BACKEND_URL}/query", json=payload)
# # #                     response.raise_for_status()
# # #                     data = response.json()
# # #                     answer = data.get("answer", "Sorry, something went wrong.")
# # #                     st.markdown(answer, unsafe_allow_html=True)
# # #                     st.session_state.messages.append({"role": "assistant", "content": answer})
# # #                 except requests.RequestException as e:
# # #                     error_message = f"Failed to connect to the backend: {e}"
# # #                     st.error(error_message)
# # #                     st.session_state.messages.append({"role": "assistant", "content": error_message})

# # #     if st.button("End Session and Change Role"):
# # #         # Clear session state to go back to the role selection screen
# # #         for key in list(st.session_state.keys()):
# # #             del st.session_state[key]
# # #         st.rerun()



# # import streamlit as st
# # import requests

# # # --- Page Configuration ---
# # st.set_page_config(
# #     page_title="AskQL",
# #     page_icon="💬",
# #     layout="centered"
# # )

# # # --- Custom CSS ---
# # st.markdown("""
# # <style>
# #     /* Gradient background */
# #     .stApp {
# #         background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #0f2027 100%);
# #         color: #ccd6f6;
# #         font-family: 'Segoe UI', sans-serif;
# #     }
    
# #     /* Title Styling */
# #     h1 {
# #         color: #64ffda; 
# #         text-align: center;
# #         padding-top: 10px;
# #     }

# #     /* Button Styling */
# #     .stButton > button {
# #         color: #64ffda;
# #         border: 1px solid #64ffda;
# #         background-color: rgba(0,0,0,0.2);
# #         border-radius: 6px;
# #         padding: 0.75em 1em;
# #         width: 100%;
# #         font-weight: bold;
# #     }
# #     .stButton > button:hover {
# #         background-color: rgba(100, 255, 218, 0.15);
# #         color: #64ffda;
# #         border-color: #64ffda;
# #     }
    
# #     /* Text Input Styling */
# #     .stTextInput > div > div > input {
# #         background-color: rgba(29, 45, 68, 0.8);
# #         color: #ccd6f6;
# #         border: 1px solid #2e3d54;
# #     }

# #     /* Chat Message Styling */
# #     .stChatMessage {
# #         background-color: rgba(29, 45, 68, 0.85);
# #         border-radius: 8px;
# #         padding: 1.2em;
# #         border: 1px solid #2e3d54;
# #     }

# #     /* Markdown link styling */
# #     .stMarkdown a {
# #         color: #64ffda;
# #     }
    
# #     /* Sub-header text */
# #     .stMarkdown p, .st-emotion-cache-1yycg8b p {
# #         color: #b0bec5;
# #     }

# #     /* Table styling */
# #     .stMarkdown table {
# #         width: auto;
# #         color: #ccd6f6;
# #         background-color: rgba(46, 61, 84, 0.8);
# #         border-collapse: collapse;
# #     }
# #     .stMarkdown th {
# #         background-color: rgba(74, 96, 124, 0.9);
# #         color: #ffffff;
# #         padding: 8px;
# #         border: 1px solid #1d2d44;
# #     }
# #     .stMarkdown td {
# #         padding: 8px;
# #         border: 1px solid #1d2d44;
# #     }

# #     /* End Session button positioning */
# #     div[data-testid="stButton"] > button.end-session-btn {
# #         position: fixed;
# #         bottom: 15px;
# #         left: 15px;
# #         background-color: #222 !important;
# #         color: #64ffda !important;
# #         border: 1px solid #64ffda !important;
# #         border-radius: 6px !important;
# #         font-weight: bold !important;
# #         z-index: 999 !important;
# #     }
# #     div[data-testid="stButton"] > button.end-session-btn:hover {
# #         background-color: #64ffda !important;
# #         color: black !important;
# #     }
# # </style>
# # """, unsafe_allow_html=True)

# # # --- API Configuration ---
# # BACKEND_URL = "http://127.0.0.1:8000"

# # # --- Session State Initialization ---
# # if "role" not in st.session_state:
# #     st.session_state.role = None
# # if "messages" not in st.session_state:
# #     st.session_state.messages = []
# # if "authenticated" not in st.session_state:
# #     st.session_state.authenticated = False
# # if "db_name" not in st.session_state:
# #     st.session_state.db_name = None

# # # --- Main App Logic ---

# # # 1. Role Selection Screen
# # if st.session_state.role is None:
# #     st.title("💬 Welcome to AskQL")
# #     st.markdown("""
# #         <p style='
# #             text-align: center;
# #             color: #ffeb3b;
# #             font-size: 18px;
# #             font-weight: bold;
# #             margin-top: -10px;
# #         '>
# #             Select your role to get started.
# #         </p>
# #     """, unsafe_allow_html=True)
    
# #     col1, col2 = st.columns(2)
# #     with col1:
# #         if st.button("Read/View Only Access", use_container_width=True):
# #             st.session_state.role = "read_only"
# #             st.rerun()
# #     with col2:
# #         if st.button("Admin Access", use_container_width=True):
# #             st.session_state.role = "admin"
# #             st.rerun()

# # # 2. Admin Password Screen
# # elif st.session_state.role == "admin" and not st.session_state.authenticated:
# #     st.title("🔑 Admin Authentication")
# #     password = st.text_input("Please enter the admin password:", type="password")
    
# #     if st.button("Login"):
# #         try:
# #             response = requests.post(f"{BACKEND_URL}/authenticate", json={"password": password})
# #             if response.status_code == 200:
# #                 st.session_state.authenticated = True
# #                 st.rerun()
# #             else:
# #                 st.error("Incorrect password. Please try again.")
# #         except requests.RequestException as e:
# #             st.error(f"Could not connect to the backend: {e}")
    
# #     if st.button("← Go Back"):
# #         st.session_state.role = None
# #         st.rerun()

# # # 3. Main Chat Interface
# # else:
# #     # Fetch the database name once
# #     if st.session_state.db_name is None:
# #         try:
# #             response = requests.get(f"{BACKEND_URL}/db-info")
# #             if response.status_code == 200:
# #                 st.session_state.db_name = response.json().get("active_database", "Unknown")
# #             else:
# #                 st.session_state.db_name = "Error"
# #         except requests.RequestException:
# #             st.session_state.db_name = "Unavailable"

# #     st.title("💬 AskQL ")
# #     role_display = "Admin" if st.session_state.role == "admin" else "Read-Only"

# #     # Floating bottom-right status badge
# #     st.markdown(f"""
# #         <div style='
# #             position: fixed;
# #             bottom: 10px;
# #             right: 15px;
# #             background-color: rgba(0,0,0,0.4);
# #             padding: 6px 12px;
# #             border-radius: 6px;
# #             font-size: 14px;
# #             color: #64ffda;
# #             z-index: 999;
# #         '>
# #             <b>Mode:</b> {role_display} &nbsp;|&nbsp; <b>Connected to:</b> {st.session_state.db_name}
# #         </div>
# #     """, unsafe_allow_html=True)

# #     # Display chat history
# #     for message in st.session_state.messages:
# #         with st.chat_message(message["role"]):
# #             st.markdown(message["content"], unsafe_allow_html=True)

# #     # Chat input
# #     if prompt := st.chat_input("Ask your database..."):
# #         st.session_state.messages.append({"role": "user", "content": prompt})
# #         with st.chat_message("user"):
# #             st.markdown(prompt)

# #         with st.chat_message("assistant"):
# #             with st.spinner("Thinking..."):
# #                 try:
# #                     payload = {
# #                         "query": prompt,
# #                         "role": st.session_state.role,
# #                         "chat_history": [
# #                             {"type": msg["role"], "content": msg["content"]}
# #                             for msg in st.session_state.messages[:-1]
# #                         ]
# #                     }
# #                     response = requests.post(f"{BACKEND_URL}/query", json=payload)
# #                     response.raise_for_status()
# #                     data = response.json()
# #                     answer = data.get("answer", "Sorry, something went wrong.")
# #                     st.markdown(answer, unsafe_allow_html=True)
# #                     st.session_state.messages.append({"role": "assistant", "content": answer})
# #                 except requests.RequestException as e:
# #                     error_message = f"Failed to connect to the backend: {e}"
# #                     st.error(error_message)
# #                     st.session_state.messages.append({"role": "assistant", "content": error_message})

# #     # Bottom-left "End Session" button (only in active mode)
# #     if st.session_state.role == "read_only" or (st.session_state.role == "admin" and st.session_state.authenticated):
# #         if st.button("End Session and Change Role", key="end_session", help="Click to logout/change role"):
# #             for key in list(st.session_state.keys()):
# #                 del st.session_state[key]
# #             st.rerun()
# #         st.markdown("""
# #     <style>
# #     /* Center role selection */
# #     .center-container {
# #         display: flex;
# #         justify-content: center;
# #         align-items: center;
# #         height: 80vh;
# #         flex-direction: column;
# #         text-align: center;
# #         color: #64ffda;
# #     }
# #     /* Move End Session button to bottom-left */
# #     .stButton > button.end-session-btn {
# #         position: fixed;
# #         bottom: 15px;
# #         left: 15px;
# #         background-color: #222 !important;
# #         color: #64ffda !important;
# #         border: 1px solid #64ffda !important;
# #         border-radius: 6px !important;
# #         font-weight: bold !important;
# #         padding: 0.5rem 1rem;
# #         z-index: 999 !important;
# #     }
# #     .stButton > button.end-session-btn:hover {
# #         background-color: #64ffda !important;
# #         color: black !important;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)




# import streamlit as st
# import requests
# import re

# # --- Page Configuration ---
# st.set_page_config(
#     page_title="AskQL",
#     page_icon="💬",
#     layout="centered"
# )

# # --- Custom CSS ---
# st.markdown("""
# <style>
#     /* Gradient background */
#     .stApp {
#         background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #0f2027 100%);
#         color: #ccd6f6;
#         font-family: 'Segoe UI', sans-serif;
#     }
    
#     /* Title Styling */
#     h1 {
#         color: #64ffda; 
#         text-align: center;
#         padding-top: 10px;
#     }

#     /* Button Styling */
#     .stButton > button {
#         color: #64ffda;
#         border: 1px solid #64ffda;
#         background-color: rgba(0,0,0,0.2);
#         border-radius: 6px;
#         padding: 0.75em 1em;
#         width: 100%;
#         font-weight: bold;
#     }
#     .stButton > button:hover {
#         background-color: rgba(100, 255, 218, 0.15);
#         color: #64ffda;
#         border-color: #64ffda;
#     }
    
#     /* Text Input Styling */
#     .stTextInput > div > div > input {
#         background-color: rgba(29, 45, 68, 0.8);
#         color: #ccd6f6;
#         border: 1px solid #2e3d54;
#     }

#     /* Chat Message Styling */
#     .stChatMessage {
#         background-color: rgba(29, 45, 68, 0.85);
#         border-radius: 8px;
#         padding: 1.2em;
#         border: 1px solid #2e3d54;
#     }

#     /* Markdown link styling */
#     .stMarkdown a {
#         color: #64ffda;
#     }
    
#     /* Sub-header text */
#     .stMarkdown p, .st-emotion-cache-1yycg8b p {
#         color: #b0bec5;
#     }

#     /* Scrollable table container */
#     .table-wrapper {
#         overflow-x: auto;
#         -webkit-overflow-scrolling: touch;
#         max-width: 100%;
#         border-radius: 8px;
#         border: 1px solid #2e3d54;
#         margin: 10px 0;
#     }

#     /* Make ALL table containers scrollable */
#     .stChatMessage div[data-testid="stMarkdownContainer"],
#     .stMarkdown,
#     .element-container {
#         overflow-x: auto !important;
#         -webkit-overflow-scrolling: touch !important;
#     }

#     /* Table styling - both for wrapper and direct markdown tables */
#     .table-wrapper table,
#     .stMarkdown table,
#     .stChatMessage table {
#         color: #ccd6f6;
#         background-color: rgba(46, 61, 84, 0.8);
#         border-collapse: collapse;
#         width: 100%;
#         min-width: 700px !important; /* ensures scroll when narrow container */
#     }
    
#     .table-wrapper th,
#     .stMarkdown th,
#     .stChatMessage th {
#         background-color: rgba(74, 96, 124, 0.9);
#         color: #ffffff;
#         padding: 12px 8px;
#         border: 1px solid #1d2d44;
#         white-space: nowrap;
#         font-weight: bold;
#     }
    
#     .table-wrapper td,
#     .stMarkdown td,
#     .stChatMessage td {
#         padding: 10px 8px;
#         border: 1px solid #1d2d44;
#         white-space: nowrap;
#     }

#     /* Force horizontal scroll on any container with tables */
#     div:has(table) {
#         overflow-x: auto !important;
#         -webkit-overflow-scrolling: touch !important;
#     }

#     /* End Session button positioning */
#     .stButton > button.end-session-btn {
#         position: fixed;
#         bottom: 15px;
#         left: 15px;
#         background-color: #222 !important;
#         color: #64ffda !important;
#         border: 1px solid #64ffda !important;
#         border-radius: 6px !important;
#         font-weight: bold !important;
#     }
#     .stButton > button.end-session-btn:hover {
#         background-color: #64ffda !important;
#         color: black !important;
#     }
# </style>
# """, unsafe_allow_html=True)

# # --- API Configuration ---
# BACKEND_URL = "http://127.0.0.1:8000"

# # --- Session State Initialization ---
# if "role" not in st.session_state:
#     st.session_state.role = None
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False
# if "db_name" not in st.session_state:
#     st.session_state.db_name = None

# # --- Main App Logic ---
# # 1. Role Selection Screen
# if st.session_state.role is None:
#     st.title("💬 Welcome to AskQL")
#     st.markdown("""
#         <p style='
#             text-align: center;
#             color: #ffeb3b;
#             font-size: 18px;
#             font-weight: bold;
#             margin-top: -10px;
#         '>
#             Select your role to get started.
#         </p>
#     """, unsafe_allow_html=True)
    
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("Read/View Only Access", use_container_width=True):
#             st.session_state.role = "read_only"
#             st.rerun()
#     with col2:
#         if st.button("Admin Access", use_container_width=True):
#             st.session_state.role = "admin"
#             st.rerun()

# # 2. Admin Password Screen
# elif st.session_state.role == "admin" and not st.session_state.authenticated:
#     st.title("🔑 Admin Authentication")
#     password = st.text_input("Please enter the admin password:", type="password")
    
#     if st.button("Login"):
#         try:
#             response = requests.post(f"{BACKEND_URL}/authenticate", json={"password": password})
#             if response.status_code == 200:
#                 st.session_state.authenticated = True
#                 st.rerun()
#             else:
#                 st.error("Incorrect password. Please try again.")
#         except requests.RequestException as e:
#             st.error(f"Could not connect to the backend: {e}")
    
#     if st.button("← Go Back"):
#         st.session_state.role = None
#         st.rerun()

# # 3. Main Chat Interface
# else:
#     if st.session_state.db_name is None:
#         try:
#             response = requests.get(f"{BACKEND_URL}/db-info")
#             if response.status_code == 200:
#                 st.session_state.db_name = response.json().get("active_database", "Unknown")
#             else:
#                 st.session_state.db_name = "Error"
#         except requests.RequestException:
#             st.session_state.db_name = "Unavailable"

#     st.title("💬 AskQL ")
#     role_display = "Admin" if st.session_state.role == "admin" else "Read-Only"

#     st.markdown(f"""
#         <div style='
#             position: fixed;
#             bottom: 10px;
#             right: 15px;
#             background-color: rgba(0,0,0,0.4);
#             padding: 6px 12px;
#             border-radius: 6px;
#             font-size: 14px;
#             color: #64ffda;
#             z-index: 999;
#         '>
#             <b>Mode:</b> {role_display} &nbsp;|&nbsp; <b>Connected to:</b> {st.session_state.db_name}
#         </div>
#     """, unsafe_allow_html=True)

#     # --- Updated Chat History Display ---
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             if message["role"] == "assistant":
#                 content = message["content"]

#                 # Detect Markdown table in message
#                 table_match = re.search(r"(\|.+\|(?:\n\|[-:]+)+\n(?:\|.*\|.*\n?)+)", content)
#                 if table_match:
#                     table_md = table_match.group(1)
#                     text_md = content.replace(table_md, "").strip()

#                     if text_md:
#                         st.markdown(text_md, unsafe_allow_html=True)

#                     # Scrollable table with enhanced wrapper
#                     st.markdown(
#                         f"""
#                         <div class="table-wrapper">
#                             {table_md}
#                         </div>
#                         """,
#                         unsafe_allow_html=True
#                     )
#                 else:
#                     # For content without tables, still apply scrollable styling
#                     st.markdown(f'<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">{content}</div>', 
#                               unsafe_allow_html=True)
#             else:
#                 st.markdown(message["content"], unsafe_allow_html=True)

#     # Chat input
#     if prompt := st.chat_input("Ask your database..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 try:
#                     payload = {
#                         "query": prompt,
#                         "role": st.session_state.role,
#                         "chat_history": [
#                             {"type": msg["role"], "content": msg["content"]}
#                             for msg in st.session_state.messages[:-1]
#                         ]
#                     }
#                     response = requests.post(f"{BACKEND_URL}/query", json=payload)
#                     response.raise_for_status()
#                     data = response.json()
#                     answer = data.get("answer", "Sorry, something went wrong.")
                    
#                     # Check if answer contains table and wrap accordingly
#                     table_match = re.search(r"(\|.+\|(?:\n\|[-:]+)+\n(?:\|.*\|.*\n?)+)", answer)
#                     if table_match:
#                         table_md = table_match.group(1)
#                         text_md = answer.replace(table_md, "").strip()

#                         if text_md:
#                             st.markdown(text_md, unsafe_allow_html=True)

#                         # Display table with horizontal scroll
#                         st.markdown(
#                             f"""
#                             <div class="table-wrapper">
#                                 {table_md}
#                             </div>
#                             """,
#                             unsafe_allow_html=True
#                         )
#                     else:
#                         st.markdown(answer, unsafe_allow_html=True)
                    
#                     st.session_state.messages.append({"role": "assistant", "content": answer})
#                 except requests.RequestException as e:
#                     error_message = f"Failed to connect to the backend: {e}"
#                     st.error(error_message)
#                     st.session_state.messages.append({"role": "assistant", "content": error_message})

#     # End Session button
#     if st.session_state.role == "read_only" or (st.session_state.role == "admin" and st.session_state.authenticated):
#         if st.button("End Session and Change Role", key="end_session", help="Click to logout/change role"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()




import streamlit as st
import requests
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="AskQL",
    page_icon="💬",
    layout="centered"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* App background */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #0f2027 100%);
        color: #ccd6f6;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Title Styling */
    h1 {
        color: #64ffda; 
        text-align: center;
        padding-top: 10px;
    }

    /* Button Styling */
    .stButton > button {
        color: #64ffda;
        border: 1px solid #64ffda;
        background-color: rgba(0,0,0,0.2);
        border-radius: 6px;
        padding: 0.75em 1em;
        width: 100%;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: rgba(100, 255, 218, 0.15);
        color: #64ffda;
        border-color: #64ffda;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background-color: rgba(29, 45, 68, 0.8);
        color: #ccd6f6;
        border: 1px solid #2e3d54;
    }

    /* Chat bubbles */
    .stChatMessage {
        background-color: rgba(29, 45, 68, 0.85);
        border-radius: 8px;
        padding: 1.2em;
        border: 1px solid #2e3d54;
    }

    /* Scrollable table container */
    .table-scroll-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        max-width: 100%;
        border-radius: 8px;
        border: 1px solid #2e3d54;
        margin: 10px 0;
        background-color: rgba(46, 61, 84, 0.4);
    }

    /* Table Styling */
    .table-scroll-wrapper table {
        color: #ccd6f6;
        background-color: rgba(46, 61, 84, 0.8);
        border-collapse: collapse;
        min-width: 700px;
        margin: 0;
    }
    .table-scroll-wrapper th {
        background-color: rgba(74, 96, 124, 0.95);
        color: #ffffff;
        padding: 12px 8px;
        border: 1px solid #1d2d44;
        white-space: nowrap;
        font-weight: bold;
        position: sticky;
        top: 0; /* Fixed header */
        z-index: 2;
    }
    .table-scroll-wrapper td {
        padding: 10px 8px;
        border: 1px solid #1d2d44;
        white-space: nowrap;
    }

    /* Striped rows */
    .table-scroll-wrapper tr:nth-child(even) {
        background-color: rgba(255, 255, 255, 0.05);
    }
    .table-scroll-wrapper tr:hover {
        background-color: rgba(255, 255, 255, 0.08);
    }

    /* End Session button */
    .stButton > button.end-session-btn {
        position: fixed;
        bottom: 15px;
        left: 15px;
        background-color: #222 !important;
        color: #64ffda !important;
        border: 1px solid #64ffda !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    .stButton > button.end-session-btn:hover {
        background-color: #64ffda !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# --- API Config ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- Markdown table to HTML converter ---
def markdown_table_to_html(md_table):
    lines = [line.strip() for line in md_table.strip().split('\n') if line.strip()]
    headers = [h.strip() for h in lines[0].strip('|').split('|')]
    html = '<table><thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead><tbody>'
    for row in lines[2:]:
        cells = [c.strip() for c in row.strip('|').split('|')]
        html += '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
    html += '</tbody></table>'
    return html

# --- Render helper for scrollable tables ---
def render_with_scrollable_table(message_text):
    table_match = re.search(r"(\|(?:[^\n]+\|)+\n\|(?:[-:\s]+\|)+\n(?:\|.*\|.*\n?)+)", message_text)
    if table_match:
        table_md = table_match.group(1)
        text_md = message_text.replace(table_md, "").strip()
        if text_md:
            st.markdown(text_md, unsafe_allow_html=True)
        table_html = markdown_table_to_html(table_md)
        st.markdown(f'<div class="table-scroll-wrapper">{table_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(message_text, unsafe_allow_html=True)

# --- Session state ---
if "role" not in st.session_state: st.session_state.role = None
if "messages" not in st.session_state: st.session_state.messages = []
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "db_name" not in st.session_state: st.session_state.db_name = None

# --- Main logic ---
if st.session_state.role is None:
    st.title("💬 Welcome to AskQL")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Read/View Only Access", use_container_width=True):
            st.session_state.role = "read_only"
            st.rerun()
    with col2:
        if st.button("Admin Access", use_container_width=True):
            st.session_state.role = "admin"
            st.rerun()

elif st.session_state.role == "admin" and not st.session_state.authenticated:
    st.title("🔑 Admin Authentication")
    password = st.text_input("Please enter the admin password:", type="password")
    if st.button("Login"):
        try:
            res = requests.post(f"{BACKEND_URL}/authenticate", json={"password": password})
            if res.status_code == 200:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        except requests.RequestException as e:
            st.error(f"Could not connect to backend: {e}")
    if st.button("← Go Back"):
        st.session_state.role = None
        st.rerun()

else:
    # DB info
    if st.session_state.db_name is None:
        try:
            res = requests.get(f"{BACKEND_URL}/db-info")
            st.session_state.db_name = res.json().get("active_database", "Unknown") if res.status_code == 200 else "Error"
        except requests.RequestException:
            st.session_state.db_name = "Unavailable"

    st.title("💬 AskQL")
    role_display = "Admin" if st.session_state.role == "admin" else "Read-Only"
    st.markdown(f"""
        <div style='position: fixed; bottom: 10px; right: 15px;
             background-color: rgba(0,0,0,0.4);
             padding: 6px 12px; border-radius: 6px;
             font-size: 14px; color: #64ffda; z-index: 999;'>
            <b>Mode:</b> {role_display} &nbsp;|&nbsp;
            <b>Connected to:</b> {st.session_state.db_name}
        </div>
    """, unsafe_allow_html=True)

    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_with_scrollable_table(message["content"])
            else:
                st.markdown(message["content"], unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask your database..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "query": prompt,
                        "role": st.session_state.role,
                        "chat_history": [
                            {"type": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.messages[:-1]
                        ]
                    }
                    res = requests.post(f"{BACKEND_URL}/query", json=payload)
                    res.raise_for_status()
                    answer = res.json().get("answer", "Sorry, something went wrong.")
                    render_with_scrollable_table(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except requests.RequestException as e:
                    err_msg = f"Failed to connect: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

    # End session button
    if st.session_state.role == "read_only" or (st.session_state.role == "admin" and st.session_state.authenticated):
        if st.button("End Session and Change Role", key="end_session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
