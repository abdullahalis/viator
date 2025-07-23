from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, AIMessage
from agent.agent import get_agent
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import logging

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Endpoint for agent calls
@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("input")
    last_tool = ""
    agent, config = get_agent()
    
    # Define an async generator to stream tokens
    async def event_stream():
        nonlocal last_tool

        # Stream agent output by token
        for chunk, metadata in agent.stream(
            {"messages": [("user", user_input)]},
            config=config,
            stream_mode="messages",
        ):
            metadata_logger.debug(f"chunk: {chunk}")
            metadata_logger.debug(f"Metadata: {metadata}")

            # Send tool calls to frontend
            if hasattr(chunk, "tool_calls"):
                for tool_call in chunk.tool_calls:
                    tool_name = tool_call.get("name")
                    if tool_name and tool_name != last_tool:
                        print("new tool", tool_name)
                        try:
                            yield f"{json.dumps({'type': 'tool', 'tool_name': tool_name})}[END]"
                            await asyncio.sleep(0)
                        except asyncio.CancelledError:
                            print(f"Client disconnected while yielding")
                            return 
                        last_tool = tool_name

            # Make sure output being streamed is only AI Messages from main LLM
            if ("structured" not in metadata.get("tags", []) and (isinstance(chunk, AIMessageChunk) or isinstance(chunk, AIMessage))):                
                content = chunk.content
                send_data = ""
                if content:
                    # Check if content is a JSON string
                    try:
                        parsed = json.loads(content)
                        # If it's a dict with a "type" key, treat it as structured JSON
                        if isinstance(parsed, dict) and "type" in parsed:
                            send_data = f"{json.dumps(parsed)}[END]"
                        else:
                            # Otherwise it's normal streaming data that could technically count as JSON (like the number 4)
                            send_data = f"{json.dumps({'type': 'stream', 'content': content})}[END]"
                    except (TypeError, ValueError):
                        # If it can't be parsed to json than it's normal streaming tokens
                        send_data = f"{json.dumps({'type': 'stream', 'content': content})}[END]"
                    
                    # Avoid socket errors
                    try:
                        yield send_data
                        await asyncio.sleep(0)
                    except asyncio.CancelledError:
                        print(f"Client disconnected while yielding")
                        return 
                    
    return StreamingResponse(event_stream(), media_type="text/event-stream")