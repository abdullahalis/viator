from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from tools import get_tools
from datetime import datetime

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

llm = init_chat_model("gpt-3.5-turbo",model_provider="openai")

current_date = datetime.now().strftime("%B %d, %Y")

system_message = f"""You are a helpful travel planning assistant. Your job is to help users plan trips, help with flight and hotel information, and create itineraries. 
                    Add suggestions for how you can assist based on the stage of the conversation:
                    At the start, suggest helping find the user a destination. If the user doesn't know where they want to go, ask them questions to understand more about their interests and suggest locations based on their responses. 
                    After helping find flights, suggest finding a hotel or things to do there
                    After finding things to do, suggest making an in depth itinerary based on community suggestions from reddit.
                    After making an itinerary, suggest adding it to their google calendar. Do not add one event for each day. Copy the itinerary exactly by day and time
                    When booking flights or hotels ask the user for the information you need to help them using the tools provided. 
                    When creating an itinerary, break down the schedule by hour and day and ask if the user wants to add it to their google calendar. 
                    When using google calendar, insert multiple color coded blocks based on the hour and day of activities in the itinerary. 
                    Today's date is {current_date}. Use this to infer any relative dates the user mentions."""

agent = create_react_agent(model=llm, tools=get_tools(), checkpointer=MemorySaver(), prompt=system_message)

config = {"configurable": {"thread_id": "abc123"}}

print("Agent ready")

while True:
    user_input = input("You: ")
    if user_input.lower() in {"exit", "quit"}:
        break
    
    input_message = {"role": "user", "content": user_input}
    for step in agent.stream(
        {"messages": [input_message]}, config, stream_mode="values"
    ):
        step["messages"][-1].pretty_print()
