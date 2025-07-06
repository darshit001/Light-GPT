import psycopg2
import logging
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "darshit")
DB_PORT = os.getenv("DB_PORT", "5432")  

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'mcp_interactions.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection error: {str(e)}")
        return None

def init_database():
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if user_id column exists in chat_sessions table
            cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='chat_sessions' AND column_name='user_id'
            """)
            
            user_id_exists = cur.fetchone() is not None
            
            if not user_id_exists:
                # First create the table if it doesn't exist
                cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Then add user_id column if the table already existed but without this column
                cur.execute("""
                ALTER TABLE chat_sessions 
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)
                """)
            else:
                # Table exists and has user_id column
                cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_interactions (
                interaction_id SERIAL PRIMARY KEY,
                session_id VARCHAR(36) REFERENCES chat_sessions(session_id),
                user_question TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                tool_used VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cur.execute("""
            DROP TABLE IF EXISTS chat_messages CASCADE
            """)
            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Database initialization error: {str(e)}")
        return False
    finally:
        conn.close()

def save_chat_interaction(session_id, user_question, assistant_response=None, tool_used=None):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        response_text = assistant_response or "Processing..."
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_interactions (session_id, user_question, assistant_response, tool_used)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, user_question, response_text, tool_used)
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Error saving interaction: {str(e)}")
        return False
    finally:
        conn.close()

def create_chat_session(user_email):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_sessions (session_id, user_id) VALUES (%s, %s)",
                (session_id, user_email)
            )
            conn.commit()
            return session_id
    except psycopg2.Error as e:
        logging.error(f"Error creating chat session: {str(e)}")
        return None
    finally:
        conn.close()

def get_chat_sessions(user_email):
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT session_id, created_at 
                FROM chat_sessions 
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_email,)
            )
            return cur.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Error retrieving chat sessions: {str(e)}")
        return []
    finally:
        conn.close()

def get_chat_interactions(session_id):
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_question, assistant_response, tool_used, created_at 
                FROM chat_interactions 
                WHERE session_id = %s 
                ORDER BY created_at
                """,
                (session_id,)
            )
            return cur.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Error retrieving chat interactions: {str(e)}")
        return []
    finally:
        conn.close()

def delete_chat_session(session_id):
    conn = get_db_connection()
    if conn is None:
        logging.error("Failed to get database connection for deleting chat session.")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chat_interactions WHERE session_id = %s",
                (session_id,)
            )
            logging.info(f"Deleted interactions for session {session_id}")
            
            cur.execute(
                "DELETE FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )
            logging.info(f"Deleted session {session_id}")
            
            conn.commit()
            return True
    except psycopg2.Error as e:
        logging.error(f"Error deleting chat session: {str(e)}")
        conn.rollback()
        return False
    except Exception as e:
        logging.error(f"Unexpected error deleting chat session: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_latest_session(user_email):
    """
    Get the most recent chat session for a user
    
    Args:
        user_email (str): The user's email address
        
    Returns:
        str: The session ID of the most recent chat, or None if no sessions exist
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
            
        with conn.cursor() as cur:
            # Get the most recent session for this user
            cur.execute(
                "SELECT session_id FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_email,)
            )
            
            result = cur.fetchone()
            return result[0] if result else None
            
    except Exception as e:
        logging.error(f"Database error in get_latest_session: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()