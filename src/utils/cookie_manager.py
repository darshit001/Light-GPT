from streamlit_cookies_manager import CookieManager
import streamlit as st
import json
import warnings
warnings.filterwarnings("ignore")

class SessionCookieManager:
    def __init__(self):
        # Initialize cookie manager
        self.cookies = CookieManager()
        
    def init_cookies(self):
        """Initialize the cookie manager"""
        if not self.cookies.ready():
            st.warning("Cookie manager not ready yet. Please wait...")
            st.stop()
        return self.cookies
    
    def save_user_session(self, user_data, session_id=None):
        """Save user session data to cookies"""
        cookies = self.init_cookies()
        
        # Prepare session data
        session_data = {
            "user": user_data,
            "session_id": session_id
        }
        
        # Save to cookies
        cookies["user_session"] = json.dumps(session_data)
        cookies.save()
    
    def load_user_session(self):
        """Load user session data from cookies"""
        cookies = self.init_cookies()
        
        if "user_session" in cookies:
            try:
                session_data = json.loads(cookies["user_session"])
                return session_data.get("user"), session_data.get("session_id")
            except json.JSONDecodeError:
                return None, None
        
        return None, None
    
    def clear_user_session(self):
        """Clear user session data from cookies"""
        cookies = self.init_cookies()
        
        if "user_session" in cookies:
            del cookies["user_session"]
            cookies.save()
