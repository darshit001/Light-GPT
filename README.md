# Chat Assistant

A powerful AI assistant application built using Streamlit and the Model Context Protocol (MCP), offering multiple AI tools including general QA, deep research, image generation, and PDF document analysis.

## Project Overview

Chat Assistant is a versatile conversational AI interface that integrates several advanced AI capabilities:

- **General Chat**: Engage in conversational interactions with an AI assistant
- **Deep Research**: Perform comprehensive research on any topic with multiple sources
- **Image Generation**: Create images from text descriptions
- **PDF QA**: Ask questions about the content of uploaded PDF documents

The application uses Streamlit for the frontend UI, with a Python backend that communicates with various AI services via the Model Context Protocol (MCP).

## Project Structure

```
Dev-MCP/
│
├── src/                    # Main application source code
│   ├── database/           # Database handling and persistence
│   ├── mcp/                # Model Context Protocol client implementation
│   ├── styles/             # CSS and styling files
│   ├── utils/              # Utility functions
│   └── main.py             # Main Streamlit application
│
├── server/                 # MCP Server implementation
│   └── mcp_server_sse.py   # Server-Sent Events based MCP server
│
└── requirements.txt        # Project dependencies
```

## Installation

1. Clone the repository 

```bash
git clone https://gitlab.wappnet.us/dhruv.wappnet/general-chat-agent.git
cd Dev-MCP
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root directory with the following environment variables:

```
# Required API keys
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Server configuration
SERVER_URL=http://localhost:8000/sse
MODEL_NAME=llama3-70b-8192

# PostgreSQL configuration
DB_HOST=your_hostname
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

### Required API Keys:

- **GROQ_API_KEY**: API key for the Groq language model API (https://groq.com)
- **TAVILY_API_KEY**: API key for the Tavily search API (https://tavily.com)
- **FIRECRAWL_API_KEY**: API key for the Firecrawl research API

## Running the Application

### Step 1: Start the MCP Server

Open a terminal window and run:

```bash
cd Dev-MCP
python server/mcp_server_sse.py
```

This will start the MCP server on `localhost:8000`.

### Step 2: Start the Streamlit Application

Open a new terminal window and run:

```bash
cd Dev-MCP
streamlit run src/main.py
```

## Features

### Tools
- **Default**: Standard question-answering using the Groq LLM
- **Deep Research**: In-depth research on topics with multiple source references
- **Image Generation**: Create images from text descriptions
- **PDF QA**: Upload PDFs and ask questions about their content