"""
Session Management Utilities for MCP Assistant

This module contains functions for session management, chat history loading,
and other session-related utilities.
"""

import streamlit as st
import os
from langchain.memory import ConversationBufferMemory
from src.utils.ui_utils import extract_image_path

def get_user_email():
    """
    Get the current user's email from session state, handling different data formats.
    
    Returns:
        str: User email or string representation of user data
    """
    if not st.session_state.get("user"):
        return None
        
    if isinstance(st.session_state["user"], dict) and 'email' in st.session_state["user"]:
        return st.session_state["user"]["email"]
    else:
        return str(st.session_state["user"])

def load_chat_history(session_id, get_chat_interactions, cookie_manager):
    """
    Load chat history from database for a specific session.
    
    Args:
        session_id (str): The ID of the chat session to load
        get_chat_interactions (callable): Function to get chat interactions from DB
        cookie_manager: Cookie manager instance for saving session data
        
    Returns:
        None: Updates session state directly
    """
    # Reset session state
    st.session_state.messages = []
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
    st.session_state.image_paths = []
    
    # Load interactions from database
    interactions = get_chat_interactions(session_id)
    for user_question, assistant_response, tool_used, timestamp in interactions:
        # Add to session state
        st.session_state.messages.append({'role': 'user', 'content': user_question})
        st.session_state.messages.append({'role': 'assistant', 'content': assistant_response})
        
        # Add to memory for context
        st.session_state.memory.chat_memory.add_user_message(user_question)
        st.session_state.memory.chat_memory.add_ai_message(assistant_response)
        
        # Handle images if present
        if tool_used == "generate_image":
            image_path = extract_image_path(assistant_response)
            if image_path and os.path.exists(image_path):
                st.session_state.image_paths.append(image_path)
    
    # Update session ID
    st.session_state.session_id = session_id
    
    # Update cookies with new session_id
    if st.session_state.get("user"):
        cookie_manager.save_user_session(st.session_state["user"], session_id)

def init_session_state():
    """
    Initialize Streamlit session state variables if they don't exist.
    """
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'tools' not in st.session_state:
        st.session_state.tools = []
    if 'tool_used' not in st.session_state:
        st.session_state.tool_used = None
    if 'image_paths' not in st.session_state:
        st.session_state.image_paths = []
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(return_messages=True)
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'delete_session_id' not in st.session_state:
        st.session_state.delete_session_id = None
    # Streaming settings
    if 'typing_speed' not in st.session_state:
        st.session_state.typing_speed = 0.01  # Default typing speed
    if 'enable_streaming' not in st.session_state:
        st.session_state.enable_streaming = True  # Enable streaming by default

def load_user_from_cookies(cookie_manager):
    """
    Load user data from cookies if available.
    
    Args:
        cookie_manager: Cookie manager instance for loading session data
        
    Returns:
        bool: True if user was loaded, False otherwise
    """
    if st.session_state["user"] is None:
        try:
            user_data, session_id = cookie_manager.load_user_session()
            if user_data:
                # Verify this session belongs to the current user if session_id exists
                if session_id:
                    from src.database.db import get_db_connection
                    import logging
                    conn = get_db_connection()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "SELECT user_id FROM chat_sessions WHERE session_id = %s",
                                    (session_id,)
                                )
                                result = cur.fetchone()
                                if result and result[0] == user_data["email"]:
                                    st.session_state.session_id = session_id
                        except Exception as e:
                            logging.error(f"Error verifying session: {str(e)}")
                        finally:
                            conn.close()
                
                # Set the user in session state
                st.session_state["user"] = user_data
                return True
        except Exception as e:
            import logging
            logging.error(f"Error loading user session from cookies: {str(e)}")
    
    return False

def clear_session():
    """Clear all user session data and memory."""
    st.session_state["user"] = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
    st.session_state.image_paths = []


def load_most_recent_session(user_email, get_latest_session_func):
    """
    Load the most recent chat session for a user from the database
    
    Args:
        user_email (str): The user's email
        get_latest_session_func (callable): Function to get latest session ID
        
    Returns:
        bool: True if a session was loaded, False otherwise
    """
    if not user_email:
        return False
        
    # Get latest session ID from database
    session_id = get_latest_session_func(user_email)
    
    if not session_id:
        return False
        
    # Set session state
    st.session_state.session_id = session_id
    return True
