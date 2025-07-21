from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent.test import get_agent
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
import openai
import json

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def stream_from_openai(agent, q):
    response = agent.stream(q)
    for chunk in response:
        yield chunk.content

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("input")
    input_message = HumanMessage(content=user_input)
    # Set up the streaming LLM and inject it into your agent
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
    agent, config = get_agent()

    # Define an async generator to stream tokens
    async def event_stream():
        for chunk in agent.stream(
            {"messages": [("user", user_input)]},
            config=config,
            stream_mode="values",
        ):
            # Extract the last assistant message content chunk
            if "messages" in chunk:
                last_msg = chunk["messages"][-1]
                # Yield JSON-encoded chunk as SSE data
                yield f"data: {json.dumps({'content': last_msg.content})}\n\n"
                

        # Signal end of stream
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")