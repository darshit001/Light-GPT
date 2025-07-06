import streamlit as st
import asyncio
import os
import time
from datetime import datetime
from langchain.memory import ConversationBufferMemory

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from outh.login import get_authorization_url, get_access_token, get_user_info

from src.utils.cookie_manager import SessionCookieManager
cookie_manager = SessionCookieManager()

from src.database.db import (
    init_database,
    create_chat_session,
    get_chat_sessions,
    get_chat_interactions,
    delete_chat_session,
    save_chat_interaction,
    get_latest_session
)
from src.utils.formatting import format_tool_response
from src.utils.pdf_export import export_chat_to_pdf
from src.mcp.client import run_query, force_deep_research, generate_image_with_prompt, query_pdf

from src.utils.ui_utils import (
    display_message,
    display_message_streaming,
    format_timestamp,
    extract_image_path,
    get_session_preview,
    load_css,
    get_user_display_name
)
from src.utils.session_utils import (
    load_chat_history,
    init_session_state,
    load_user_from_cookies,
    clear_session,
    get_user_email,
    load_most_recent_session
)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(
    filename='../src/logs/mcp_interactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
  
SERVER_URL = os.getenv("SERVER_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")

init_session_state()

# Load user from cookies
load_user_from_cookies(cookie_manager)

# If user is logged in but no session is set, try to load their latest session
if st.session_state["user"] and not st.session_state.session_id:
    user_email = get_user_email()
    if user_email:
        load_most_recent_session(user_email, get_latest_session)

def main():
    cookie_manager.init_cookies()
    
    code = st.query_params.get("code")
    if code and st.session_state["user"] is None:
        st.write("🔄 Logging in...")
        token_data = asyncio.run(get_access_token(code))
        access_token = token_data["access_token"]
        user_info = asyncio.run(get_user_info(access_token))
        st.session_state["user"] = user_info
        
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.memory = ConversationBufferMemory(return_messages=True)
        st.session_state.image_paths = []
               # Save user to cookies
        cookie_manager.save_user_session(user_info)
        
        # Try to load the user's most recent session
        user_email = get_user_email()
        if user_email:
            load_most_recent_session(user_email, get_latest_session)
        
        st.query_params.clear()
        st.rerun()
        
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles", "styles.css")
    if not load_css(css_path):
        st.error(f"CSS file not found at: {css_path}")
    
    init_database()
    
    st.title("MCP Assistant")
    # Load chat history if we have an active session
    if st.session_state.session_id:
        load_chat_history(st.session_state.session_id, get_chat_interactions, cookie_manager)
    
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            is_user = message['role'] == 'user'
            if not is_user and "Tool used: generate_image" in message['content'] and i > 0:
                image_index = sum(1 for m in st.session_state.messages[:i] 
                                if m['role'] == 'assistant' and "Tool used: generate_image" in m['content'])
                if image_index < len(st.session_state.image_paths):
                    display_message(message['content'], is_user, st.session_state.image_paths[image_index])
                    
                else:
                    display_message(message['content'], is_user)
            else:
                display_message(message['content'], is_user)
    
    server_url = SERVER_URL
    with st.sidebar:
        st.header("User Authentication")
        if st.session_state["user"]:
            username = get_user_display_name()
            st.markdown(f"<h4 style='text-align: left;'>Welcome, {username}!</h4>", unsafe_allow_html=True)
            if st.button("🚪 Logout"):
                cookie_manager.clear_user_session()
                clear_session()
                st.rerun()
        else:
            if st.button("🔐 Login with Google"):
                auth_url = asyncio.run(get_authorization_url())
                st.markdown(
                    f"""<meta http-equiv="refresh" content="0; url={auth_url}" />""",
                    unsafe_allow_html=True
                )
        
        st.header("Chat Sessions")       
        if st.button("➕ New Chat"):
            if st.session_state["user"]:
                user_email = get_user_email()
                try:
                    st.session_state.session_id = create_chat_session(user_email)
                    # Reset chat state
                    st.session_state.messages = []
                    st.session_state.memory = ConversationBufferMemory(return_messages=True)
                    st.session_state.image_paths = []
                    
                    # Update cookie with new session ID
                    cookie_manager.save_user_session(st.session_state["user"], st.session_state.session_id)
                    
                    st.success("Created new chat session!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating new chat: {str(e)}")
            else:
                st.warning("Please log in first to create a new chat")
        
        st.divider()
        st.subheader("Chat History")
        chat_sessions = []
        
        if st.session_state["user"]:
            user_email = get_user_email()
            chat_sessions = get_chat_sessions(user_email)
        else:
            st.warning("Please log in to view your chat history.")
        
        if 'delete_session_id' not in st.session_state:
            st.session_state.delete_session_id = None
            
        if st.session_state.delete_session_id:
            session_to_delete = st.session_state.delete_session_id
            if delete_chat_session(session_to_delete):
                st.success(f"Chat deleted successfully!")
                st.session_state.delete_session_id = None
                st.rerun()
            else:
                st.error("Failed to delete chat. Please try again.")
                st.session_state.delete_session_id = None
        
        with st.container():
            for session_id, created_at in chat_sessions:
                formatted_time = format_timestamp(created_at)
                preview = get_session_preview(session_id, get_chat_interactions)
                is_active = session_id == st.session_state.session_id
                
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        if is_active:
                            active_chat_label = f"<div class='active-chat-container'><span class='current-chat-indicator'></span><strong>{preview}</strong><br><small>{formatted_time}</small> <span style='background-color: #1e3f34; color: #10a37f; padding: 2px 6px; border-radius: 10px; font-size: 10px;'>ACTIVE</span></div>"
                            st.markdown(active_chat_label, unsafe_allow_html=True)
                        else:
                            session_button_label = f"{preview}\n{formatted_time}"
                            if st.button(session_button_label, key=f"session_{session_id}", use_container_width=True):
                                load_chat_history(session_id, get_chat_interactions, cookie_manager)
                                st.rerun()
                    with col2:
                        if is_active:
                            st.markdown("<div style='height: 38px; display: flex; align-items: center;'>", unsafe_allow_html=True)
                            if st.button("🗑️", key=f"delete_active_{session_id}", help="Delete this chat"):
                                if st.session_state["user"]:
                                    user_email = get_user_email()
                                    new_session_id = create_chat_session(user_email)
                                else:
                                    new_session_id = None
                                    
                                if new_session_id:
                                    st.session_state.session_id = new_session_id
                                    st.session_state.messages = []
                                    st.session_state.memory = ConversationBufferMemory(return_messages=True)
                                    st.session_state.image_paths = []
                                    st.session_state.delete_session_id = session_id
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            if st.button("🗑️", key=f"delete_{session_id}", help="Delete this chat"):
                                st.session_state.delete_session_id = session_id
                                st.rerun()
        
        st.divider()
        st.header("Tool Controls")
        
        # Set streaming as always enabled with a default speed
        st.session_state.enable_streaming = True
        st.session_state.typing_speed = 0.01
        
        selected_tool = st.radio(
            "Select Tool",
            options=["General Chat", "Deep Research", "Image Generation", "PDF QA"],
            help="Choose the tool you want to use"
        ) 

        if selected_tool == "Deep Research":
            research_depth = st.slider(
                "Research Depth",min_value=1,
                max_value=15,
                value=5,
                help="Higher depth provides more comprehensive results but takes longer" 
            )
            
        if selected_tool == "PDF QA":
            st.subheader("Upload PDF")
            uploaded_pdf = st.file_uploader("Choose a PDF file", type=["pdf"], accept_multiple_files=False)
            if uploaded_pdf is not None:
                static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
                uploaded_dir = os.path.join(static_dir, "uploaded_pdfs")
                os.makedirs(uploaded_dir, exist_ok=True)
                pdf_path = os.path.join(uploaded_dir, uploaded_pdf.name)
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_pdf.read())
                st.session_state.pdf_path = pdf_path
                st.success("PDF uploaded successfully!")
            else:
                st.session_state.pdf_path = None
                st.warning("No PDF uploaded. Please upload a PDF to use the PDF QA tool.")
        
        if st.button(" Export Chat as PDF"):
            if st.session_state.messages:
                for message in st.session_state.messages:
                    if "timestamp" not in message:
                        message["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pdf_content = export_chat_to_pdf(st.session_state.messages)
                st.download_button(
                    label="Download Chat History",
                    data=pdf_content,
                    file_name="chat_history.pdf",
                    mime="application/pdf",
                )
            else:
                st.warning("No chat history to export.")
    if prompt := st.chat_input("Type your message here..."):
        if not st.session_state["user"]:
            st.error("Please login to send messages")
            return
            
        if not st.session_state.session_id:
            user_email = get_user_email()
            st.session_state.session_id = create_chat_session(user_email)
            
            cookie_manager.save_user_session(st.session_state["user"], st.session_state.session_id)
            
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        user_question = prompt
        with chat_container:
            display_message(prompt, is_user=True)
        with st.spinner("Processing your query..."):
            if selected_tool == "Deep Research":
                result, tool_used = asyncio.run(force_deep_research(prompt, research_depth))
            elif selected_tool == "Image Generation":
                result, tool_used = asyncio.run(generate_image_with_prompt(prompt))
            elif selected_tool == "PDF QA" and st.session_state.pdf_path:
                result, tool_used = asyncio.run(query_pdf(prompt, st.session_state.pdf_path))
            else:
                result, tool_used = asyncio.run(run_query(server_url, prompt, st.session_state.pdf_path))
            
            formatted_result = result if tool_used in ["deep_research", "generate_code"] else format_tool_response(prompt, result, st.session_state.memory)

            if tool_used == "generate_image":
                image_path = extract_image_path(result)
                if image_path and os.path.exists(image_path):
                    st.session_state.image_paths.append(image_path)
            
            assistant_message = f"Tool used: {tool_used}\n\n{formatted_result}"
            st.session_state.messages.append({'role': 'assistant', 'content': assistant_message})
            
            save_chat_interaction(st.session_state.session_id, user_question, formatted_result, tool_used)
            st.session_state.memory.chat_memory.add_user_message(prompt)
            st.session_state.memory.chat_memory.add_ai_message(formatted_result)
            
            with chat_container:
                # Always use streaming display for assistant responses
                if tool_used == "generate_image" and image_path and os.path.exists(image_path):
                    display_message_streaming(assistant_message, is_user=False, image_path=image_path, 
                                           typing_speed=st.session_state.typing_speed)
                else:
                    display_message_streaming(assistant_message, is_user=False, 
                                           typing_speed=st.session_state.typing_speed)

if __name__ == "__main__":
    main()
