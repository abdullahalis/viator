from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessageChunk, AIMessage
from agent.test import get_agent
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
import openai
import json

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def stream_from_openai(agent, q):
    response = agent.stream(q)
    for chunk in response:
        yield chunk.content

import logging

# Create a custom logger
metadata_logger = logging.getLogger("metadata_logger")
metadata_logger.setLevel(logging.DEBUG)

# Create file handler for metadata logs
metadata_handler = logging.FileHandler("metadata.log")
metadata_handler.setLevel(logging.DEBUG)

# Optional: Formatter for clarity
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
metadata_handler.setFormatter(formatter)

# Add handler to logger (only once)
if not metadata_logger.hasHandlers():
    metadata_logger.addHandler(metadata_handler)


@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("input")
    input_message = HumanMessage(content=user_input)
    # Set up the streaming LLM and inject it into your agent
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
    last_tool = ""
    agent, config = get_agent()
    
    # Define an async generator to stream tokens
    async def event_stream():
        nonlocal last_tool
        for chunk, metadata in agent.stream(
            {"messages": [("user", user_input)]},
            config=config,
            stream_mode="messages",
        ):
            metadata_logger.debug(f"chunk: {chunk}")
            metadata_logger.debug(f"Metadata: {metadata}")

            if hasattr(chunk, "tool_calls"):
                for tool_call in chunk.tool_calls:
                    tool_name = tool_call.get("name")
                    if tool_name and tool_name != last_tool:
                        print("new tool", tool_name)
                        yield f"{json.dumps({'type': 'tool', 'tool_name': tool_name})}[END]"
                        last_tool = tool_name
        #    if "tags" in metadata and metadata["tags"] != "structured":
            if ("structured" not in metadata.get("tags", []) and (isinstance(chunk, AIMessageChunk) or isinstance(chunk, AIMessage))):                
                content = chunk.content
                
                if content:
                    # Check if content is a JSON string
                    try:
                        content_json = json.loads(content)
                        yield f"{json.dumps(content_json)}[END]"
                    except (TypeError, ValueError):
                        yield f"{json.dumps({"type": "stream", "content": content})}[END]"
            
                    

    return StreamingResponse(event_stream(), media_type="text/event-stream")