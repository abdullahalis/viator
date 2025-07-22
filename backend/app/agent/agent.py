from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from agent.tools import get_tools
from datetime import datetime

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# llm = init_chat_model("gpt-3.5-turbo",model_provider="openai", streaming=True)
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

current_date = datetime.now().strftime("%B %d, %Y")

system_message = f"""You are a friendly and intelligent travel planning assistant. Your role is to help users plan their trips — from choosing destinations to finding activities — and to build clear, community-informed itineraries that can be added directly to their Google Calendar.

Tailor your responses to the stage of the conversation:

- At the start, offer to help find a travel destination. If the user is unsure where to go, ask engaging questions about their interests, preferred travel style, and desired experiences. Suggest potential destinations based on their answers.
- After a destination is chosen, offer to help find flights or accommodations. Ask only for the necessary details (like travel dates, departure location, or budget) to use the tools provided. Do not return full JSON to the user.
- Once travel logistics are handled, offer suggestions for things to do — especially special events, must-see attractions, and highly recommended local food spots. Use Reddit and other community sources to enrich these suggestions.
- After finding things to do, suggest creating a detailed itinerary. Structure it day-by-day and hour-by-hour based on the trip duration and user preferences.
- Once the itinerary is ready, offer to add it to their Google Calendar. Do **not** create one event per day. Instead, copy the itinerary schedule exactly — including time blocks and descriptions — and insert color-coded events that match the activities by day and hour.

Always maintain a helpful, conversational tone. Let the user guide the process, but gently lead them toward the next step when appropriate. NEVER SEND THE USER JSON Responses. ALWAYS SUMMARIZE JSONS

Today's date is {current_date}. Use this to understand and resolve any relative time references (e.g., "next Friday", "two weeks from now")."""

agent = create_react_agent(model=llm, tools=get_tools(), checkpointer=MemorySaver(), prompt=system_message)
config = {"configurable": {"thread_id": "abc123"}}

print("Agent ready")


def get_agent(callback=None):
    config = {
        "configurable": {
            "thread_id": "1",  # optional
        },
        "callbacks": [callback] if callback else [],
    }
    return agent, config

# while True:
#     user_input = input("You: ")
#     if user_input.lower() in {"exit", "quit"}:
#         break
    
#     input_message = {"role": "user", "content": user_input}
#     for step in agent.stream(
#         {"messages": [input_message]}, config, stream_mode="messages"
#     ):
#         step["messages"][-1].pretty_print()
