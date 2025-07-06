"""
UI Utility Functions for MCP Assistant

This module contains functions for UI-related utilities such as
displaying messages, formatting timestamps, and other UI helper functions.
"""

import streamlit as st
import os
import time
from datetime import datetime

def display_message(message, is_user=False, image_path=None):
    """
    Display a chat message in the Streamlit UI with proper formatting.
    
    Args:
        message (str): The message content to display
        is_user (bool): Whether the message is from the user (True) or assistant (False)
        image_path (str, optional): Path to an image to display with the message
    """
    avatar = "👤" if is_user else "🖥️"

    message_html = f"""
        <div class="stChatMessage" data-testid="stChatMessage-{'User' if is_user else 'Assistant'}">
            <div class="avatar">{avatar}</div>
            <div class="message-content">{message}</div>
        </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)

    if image_path and not is_user and os.path.exists(image_path):
        with st.container():
            st.image(image_path, caption="Generated Image", width=400)

        # Manage image storage - keep only the most recent 5 images
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        static_dir = os.path.join(project_root, "server")
        image_dir = os.path.join(static_dir, "image")
        if os.path.exists(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if len(image_files) > 5:
                # Sort by modification time and remove the oldest
                image_files.sort(key=lambda x: os.path.getmtime(os.path.join(image_dir, x)))
                for img_file in image_files[:-5]:  # Keep the 5 most recent
                    os.remove(os.path.join(image_dir, img_file))

def display_message_streaming(message, is_user=False, image_path=None, typing_speed=0.01):
    """
    Display a chat message in the Streamlit UI with streaming effect.
    
    Args:
        message (str): The message content to display
        is_user (bool): Whether the message is from the user (True) or assistant (False)
        image_path (str, optional): Path to an image to display with the message
        typing_speed (float): Delay between characters to simulate typing speed
    """
    avatar = "👤" if is_user else "🖥️"
    
    # For user messages, we don't need streaming
    if is_user:
        display_message(message, is_user, image_path)
        return
        
    # Extract "Tool used:" prefix to display immediately without streaming effect
    tool_prefix = ""
    message_content = message
    
    if "Tool used:" in message:
        lines = message.split("\n", 2)
        if len(lines) >= 2:
            tool_prefix = lines[0] + "\n\n"
            message_content = lines[2] if len(lines) > 2 else ""
    
    # Handle code blocks specially
    code_blocks = []
    text_chunks = []
    current_pos = 0
    in_code_block = False
    code_start = message_content.find("```", current_pos)
    
    while code_start != -1:
        # Add text before code block
        if code_start > current_pos:
            text_chunks.append(message_content[current_pos:code_start])
            
        # Find end of code block
        code_end = message_content.find("```", code_start + 3)
        if code_end == -1:  # No closing tag
            text_chunks.append(message_content[code_start:])
            break
        
        # Add complete code block
        code_blocks.append(message_content[code_start:code_end+3])
        current_pos = code_end + 3
        code_start = message_content.find("```", current_pos)
    
    # Add remaining text after last code block
    if current_pos < len(message_content):
        text_chunks.append(message_content[current_pos:])
    
    # If we found code blocks, we'll handle streaming differently
    has_code_blocks = len(code_blocks) > 0
    
    # Create the message container
    message_container = st.container()
    
    with message_container:
        # Create the HTML structure
        message_placeholder = st.empty()
        
        # Display tool prefix immediately
        if tool_prefix:
            full_message = tool_prefix
            streaming_html = f"""
                <div class="stChatMessage" data-testid="stChatMessage-Assistant">
                    <div class="avatar">{avatar}</div>
                    <div class="message-content">{full_message}</div>
                </div>
            """
            message_placeholder.markdown(streaming_html, unsafe_allow_html=True)
            time.sleep(0.5)  # Small pause after tool prefix
        else:
            full_message = ""
        
        if has_code_blocks:
            # Stream text chunks and code blocks alternately
            for i in range(max(len(text_chunks), len(code_blocks))):
                # Stream text chunk
                if i < len(text_chunks):
                    text = text_chunks[i]
                    for char in text:
                        full_message += char
                        streaming_html = f"""
                            <div class="stChatMessage" data-testid="stChatMessage-Assistant">
                                <div class="avatar">{avatar}</div>
                                <div class="message-content">{full_message}</div>
                            </div>
                        """
                        message_placeholder.markdown(streaming_html, unsafe_allow_html=True)
                        time.sleep(typing_speed)
                
                # Add complete code block at once, not character by character
                if i < len(code_blocks):
                    full_message += code_blocks[i]
                    streaming_html = f"""
                        <div class="stChatMessage" data-testid="stChatMessage-Assistant">
                            <div class="avatar">{avatar}</div>
                            <div class="message-content">{full_message}</div>
                        </div>
                    """
                    message_placeholder.markdown(streaming_html, unsafe_allow_html=True)
                    time.sleep(0.5)  # Slightly longer pause after code block
        else:                # Stream by paragraphs for better markdown rendering
                paragraphs = message_content.split('\n\n')
                current_msg = ""
                
                for i, paragraph in enumerate(paragraphs):
                    # For first paragraph or short paragraphs, stream character by character
                    if i == 0 or len(paragraph) < 80:
                        for char in paragraph:
                            current_msg += char
                            full_message = tool_prefix + current_msg
                            streaming_html = f"""
                                <div class="stChatMessage" data-testid="stChatMessage-Assistant">
                                    <div class="avatar">{avatar}</div>
                                    <div class="message-content">{full_message}</div>
                                </div>
                            """
                            message_placeholder.markdown(streaming_html, unsafe_allow_html=True)
                            time.sleep(typing_speed)
                    else:
                        # For longer paragraphs, stream word by word for better performance
                        words = paragraph.split(' ')
                        for word in words:
                            current_msg += word + ' '
                            full_message = tool_prefix + current_msg
                            streaming_html = f"""
                                <div class="stChatMessage" data-testid="stChatMessage-Assistant">
                                    <div class="avatar">{avatar}</div>
                                    <div class="message-content">{full_message}</div>
                                </div>
                            """
                            message_placeholder.markdown(streaming_html, unsafe_allow_html=True)
                            time.sleep(typing_speed * 5)  # Slightly longer pause between words
                    
                    # Add paragraph break
                    if i < len(paragraphs) - 1:
                        current_msg += '\n\n'
            
    # Display image if available
    if image_path and os.path.exists(image_path):
        with message_container:
            st.image(image_path, caption="Generated Image", width=400)

        # Same image management as in display_message
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        static_dir = os.path.join(project_root, "server")
        image_dir = os.path.join(static_dir, "image")
        if os.path.exists(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if len(image_files) > 5:
                # Sort by modification time and remove the oldest
                image_files.sort(key=lambda x: os.path.getmtime(os.path.join(image_dir, x)))
                for img_file in image_files[:-5]:  # Keep the 5 most recent
                    os.remove(os.path.join(image_dir, img_file))

def format_timestamp(timestamp):
    """
    Format a timestamp into a readable date string.
    
    Args:
        timestamp: Either a datetime object or a string in ISO format
        
    Returns:
        str: A formatted date string (e.g., "Jun 25, 2025, 10:30 AM")
    """
    if isinstance(timestamp, str):
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return timestamp
    else:
        dt = timestamp
    return dt.strftime("%b %d, %Y, %I:%M %p")

def extract_image_path(result_text):
    """
    Extract the image path from a result text containing "Saved as:" marker.
    
    Args:
        result_text (str): The text containing an image path
        
    Returns:
        str or None: The extracted path or None if not found
    """
    if "Saved as:" in result_text:
        return result_text.split("Saved as:")[1].strip()
    return None

def get_session_preview(session_id, get_chat_interactions_func):
    """
    Get a preview of the first message in a chat session.
    
    Args:
        session_id (str): The ID of the chat session
        get_chat_interactions_func (callable): Function to get chat interactions
        
    Returns:
        str: A preview of the first chat message or "Empty chat" if none
    """
    interactions = get_chat_interactions_func(session_id)
    if interactions:
        first_question = interactions[0][0]
        return first_question[:37] + "..." if len(first_question) > 40 else first_question
    return "Empty chat"

def load_css(css_path):
    """
    Load and apply CSS styling from a file.
    
    Args:
        css_path (str): Path to the CSS file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        return True
    return False

def get_user_display_name():
    """
    Get the display name for the current user from session state.
    
    Returns:
        str: User's display name, email, or string representation
    """
    
    if not st.session_state.get("user"):
        return "Guest"
        
    if isinstance(st.session_state["user"], dict):
        if 'name' in st.session_state["user"]:
            return st.session_state["user"]["name"]
        elif 'email' in st.session_state["user"]:
            return st.session_state["user"]["email"]
    
    return str(st.session_state["user"])
