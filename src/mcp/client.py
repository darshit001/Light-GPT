import asyncio
import json
import logging
import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")

logging.basicConfig(
    filename='logs/mcp_interactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_prompt_to_identify_tool_and_arguments(query, tools, pdf_path=None):
    tools_description = "\n".join([f"- {tool.name}, {tool.description}, {tool.inputSchema} " for tool in tools])
    pdf_instruction = f"\nIf a PDF is uploaded (path: {pdf_path}), use the pdf_qa tool for questions related to the PDF content." if pdf_path else ""
    return (
        """You are a helpful assistant with access to these tools. Your task is to choose the most appropriate tool based on the user's question.

IMPORTANT GUIDELINES:
1. For general questions, learning paths, explanations, or discussions, use the general_qa tool
2. For specific code implementation requests, use the generate_code tool
3. For mathematical calculations, use the math_solver tool
4. For web searches, use the tavily_search tool
5. For casual conversation, use the chat_with_assistant tool
6. For creating prompts, use the generate_prompt tool
7. For generating images, use the generate_image tool
8. For questions about a PDF's content, use the pdf_qa tool"""
        f"{pdf_instruction}\n"
        f"Available tools:\n{tools_description}\n"
        f"User's Question: {query}\n"
        "Choose the most appropriate tool based on the guidelines above.\n"
        "If no tool is needed, reply directly.\n\n"
        "IMPORTANT: When you need to use a tool, you must ONLY respond with "
        "the exact JSON object format below, nothing else:\n"
        "Keep the values in str "
        "{\n"
        '    "tool": "tool-name",\n'
        '    "arguments": {\n'
        '        "argument-name": "value"\n'
        "    }\n"
        "}\n\n"
    )

def llm_client(message: str):
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": "You are an intelligent assistant. You will execute tasks as prompted"},
                  {"role": "user", "content": message}],
        max_tokens=250,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

async def run_query(server_url: str, query: str, pdf_path=None):
    logging.info(f"User Query: {query}")
    try:
        async with sse_client(server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools = await session.list_tools()
                
                prompt = get_prompt_to_identify_tool_and_arguments(query, tools.tools, pdf_path)
                llm_response = llm_client(prompt)
                logging.info(f"LLM response received: {llm_response}")
                
                tool_call = json.loads(llm_response)
                
                result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])
                
                if not result.content:
                    return "No results found. Please try a different query.", tool_call["tool"]
                
                response_text = result.content[0].text if result.content else "No content available"
                logging.info(f"Response from main tool : {response_text}\n")
                
                return response_text, tool_call["tool"]
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        return f"An error occurred. Please try again. Error: {str(e)}", None

async def force_deep_research(query, research_depth):
    async with sse_client(os.getenv("SERVER_URL")) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            result = await session.call_tool(
                "deep_research",
                arguments={"query": query, "depth": str(research_depth)}
            )
            return result.content[0].text, "deep_research"

async def generate_image_with_prompt(query):
    async with sse_client(os.getenv("SERVER_URL")) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            result = await session.call_tool(
                "generate_image",
                arguments={"prompt": query}
            )
            return result.content[0].text, "generate_image"

async def query_pdf(query, pdf_path):
    async with sse_client(os.getenv("SERVER_URL")) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            result = await session.call_tool(
                "pdf_qa",
                arguments={"query": query, "pdf_path": pdf_path}
            )
            return result.content[0].text, "pdf_qa"