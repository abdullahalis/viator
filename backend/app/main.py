from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent import get_agent

load_dotenv()
app = FastAPI()

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_input = body.get("input")
    
    input_message = {"role": "user", "content": user_input}

    agent, config = get_agent()
    async def event_stream():
        for step in agent.stream(
            {"messages": [input_message]}, config, stream_mode="values"
        ):
            # Extract the most recent assistant message
            msg = step["messages"][-1].content
            yield msg + "\n"

    return StreamingResponse(event_stream(), media_type="text/plain")