from groq import Groq
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")

import logging
logging.basicConfig(
    filename='../logs/mcp_interactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def llm_client(message: str, memory: ConversationBufferMemory):
    memory_messages = memory.chat_memory.messages
    message_history = [{"role": "system", "content": "You are an intelligent assistant. You will execute tasks as prompted"}]
    
    for msg in memory_messages:
        if isinstance(msg, HumanMessage):
            message_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            message_history.append({"role": "assistant", "content": msg.content})
    
    message_history.append({"role": "user", "content": message})
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=message_history,
        max_tokens=1000,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def format_tool_response(query: str, raw_response: str, memory: ConversationBufferMemory):
    prompt = (
        "You are an assistant tasked with reformatting a tool's response to make it clear, concise, and well-structured. "
        "Ensure the response directly answers the user's question, uses proper grammar, and is formatted in a professional manner. "
        "Avoid adding unnecessary details or altering the factual content unless it improves clarity. "
        " For code blocks, maintain the exact backtick formatting from the original response (```language ... code ... ```)\n"
        " Do not add backticks around text that is not meant to be code\n" 
        "When image generation tool is used , do not include the image URl in the response"
        "If the raw response is empty or irrelevant, provide a polite fallback message. "
        f"User's Question: {query}\n"
        f"Raw Tool Response: {raw_response}\n"
        "Reformatted Response:"
    )
    return llm_client(prompt, memory)