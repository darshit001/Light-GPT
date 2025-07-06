# 🧠 LightGPT - Groq LLM Chat Assistant with Custom Tooling

**LightGPT** is an intelligent, extensible chat assistant powered by Groq's LLM and custom tools, built with Streamlit and Starlette. It enables contextual, task-aware responses across multiple domains, including code generation, research, PDF Q&A, image creation, and web search — all through an interactive multi-session chat UI.

## ✨ Features

- ⚙️ **Integrated Groq's LLM** with tool invocation via a custom MCP (Modular Command Processor) server using Server-Sent Events (SSE).
- 🧠 **Tool-Enhanced Intelligence**:
  - `generate_code`: Write code in multiple languages with explanations.
  - `deep_research`: Firecrawl-powered multi-source research.
  - `pdf_qa`: Ask questions about uploaded PDFs using LlamaIndex.
  - `tavily_search`: Summarized real-time web results.
  - `generate_image`: AI image generation via Pollinations.
- � **Google OAuth Authentication** with secure login system and user session management.
- 👤 **User Account System** with persistent user profiles and personalized chat histories.
- �💬 **Multi-session Chat Memory** with PostgreSQL-backed persistence and LangChain memory support.
- 📄 **Export Conversations** to PDF format.
- 🖼️ **File Uploads & Image Previews** integrated into the chat.
- 🧱 **Modern UI/UX** with dynamic chat, customizable input controls, and session management.
- � **Secure Session Management** with cookie-based authentication and session persistence.

## 📁 Project Structure

```
├── src/                   # Source code directory
│   ├── main.py      # Streamlit app entrypoint
│   ├── database/          # Database connectivity and operations
│   │   └── db.py          # PostgreSQL database integration
│   ├── mcp/               # MCP client implementation
│   │   └── client.py      # Client for MCP server interaction
│   ├── styles/            # UI styling
│   │   └── styles.css     # Custom CSS for the app
│   └── utils/             # Utility functions
│       ├── cookie_manager.py    # Cookie-based session management
│       ├── file_utils.py        # File handling utilities
│       ├── formatting.py        # Response formatting utilities
│       ├── pdf_export.py        # PDF export functionality
│       ├── session_utils.py     # Session management utilities
│       └── ui_utils.py          # UI helper functions
├── server/                # Server components
│   └── mcp_server_sse.py  # Custom MCP tool server (Starlette + SSE)
├── outh/                  # Authentication system
│   └── login.py           # Google OAuth integration
├── .env                   # Environment variables
└── requirements.txt       # Project dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- API Keys:
  - `GROQ_API_KEY`
  - `TAVILY_API_KEY`
  - `FIRECRAWL_API_KEY`

### Installation

```bash
git clone https://github.com/yourusername/lightgpt.git
cd lightgpt
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Server Configuration
SERVER_URL=http://localhost:8000/sse
MCP_PORT=8000

# Database Configuration
DB_HOST=localhost
DB_NAME=chatbot_db
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_PORT=5432

# Google OAuth Configuration
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:8501
```

### Run the MCP Server

```bash
python server/mcp_server_sse.py
```

### Run the Streamlit Frontend

```bash
streamlit run main.py
```

## 🔐 Authentication System

The app uses Google OAuth for secure user authentication:

- **User Login**: Secure authentication through Google's OAuth 2.0 system
- **Session Management**: Cookie-based session storage for persistent login
- **User Profiles**: Each user gets their own personalized chat history and sessions
- **Secure Data**: Chat sessions are linked to user accounts in the database

### Google OAuth Setup

1. Create a Google Cloud project at [Google Developer Console](https://console.developers.google.com/)
2. Configure OAuth consent screen
3. Create OAuth credentials (Client ID and Client Secret)
4. Add your redirect URI (usually http://localhost:8501 for local Streamlit)
5. Add the credentials to your `.env` file:

```env
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:8501
```

## 💾 Session Management

LightGPT offers sophisticated session management:

- **Multiple Chat Sessions**: Create and manage multiple conversations per user
- **Session Persistence**: Sessions are stored in PostgreSQL and recalled on login
- **Chat History**: Full conversation history is preserved between sessions
- **Session Switching**: Easily switch between different chat contexts

## 🧠 Tools Overview

Each tool is registered with the MCP server and auto-discovered in the frontend:
- **`generate_code`**: Converts natural language into runnable code with explanations.
- **`deep_research`**: Crawls and summarizes web sources deeply.
- **`pdf_qa`**: Answers based on PDF content using vector index.
- **`generate_image`**: Creates images from prompts.
- **`general_qa`, `chat_with_assistant`, `math_solver`, `generate_prompt`**, etc.

## 🧪 Example Use Cases

- Ask: *"Create a Python script to scrape weather data."*
- Upload a PDF and ask: *"Summarize chapter 3."*
- Prompt: *"Generate an image of a futuristic city at night."*

## 📦 Dependencies

- **Web Framework**: Streamlit, Starlette, Uvicorn
- **Authentication**: httpx_oauth, streamlit-cookies-manager
- **AI & LLM**: Groq SDK, LangChain, LlamaIndex
- **Data Services**: Firecrawl, Tavily
- **Database**: PostgreSQL, psycopg2
- **Documents**: ReportLab (PDF generation)
- **Utilities**: dotenv, requests, nest-asyncio
- **MCP Framework**: mcp (Modular Command Processor)
