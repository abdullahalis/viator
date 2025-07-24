from dotenv import load_dotenv
from typing import Literal, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
import json
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated, Literal
from langgraph.graph.message import add_messages
from datetime import datetime
from agent.tools import get_tools

load_dotenv()

# Load model and tools
llm = init_chat_model("gpt-4o-mini", model_provider="openai", tags=["main"])
structured_llm = ChatOpenAI(model="gpt-4o", tags=["structured"], disable_streaming=True).with_structured_output(method="json_mode")
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)

current_date = datetime.now().strftime("%B %d, %Y")
# system_message = f"""You are a friendly and intelligent travel planning assistant. Your role is to help users plan their trips — from choosing destinations to finding activities — and to build clear, community-informed itineraries that can be added directly to their Google Calendar. Make sure to use the itinerary tool if the user asks for an itinerary.

# Tailor your responses to the stage of the conversation:

# - At the start, offer to help find a travel destination. If the user is unsure where to go, ask engaging questions about their interests, preferred travel style, and desired experiences. Suggest potential destinations based on their answers.
# - After a destination is chosen, offer to help find flights or accommodations. Ask only for the necessary details (like travel dates, departure location, or budget) to use the tools provided.
# - Once travel logistics are handled, offer suggestions for things to do — especially special events, must-see attractions, and highly recommended local food spots. Use Reddit and other community sources to enrich these suggestions.
# - After finding things to do, suggest creating a detailed itinerary. When making an itinerary, always use the reddit tool to search reddit for personal recommendations. Then call the itinerary tool. Do not list out a full itinerary as a message. tell the user a couple things you plan on adding. the itinerary tool will handle the full display of events.
# - Once the itinerary is ready, offer to add it to their Google Calendar. Do not add to the calendar without explicit permission. Do **not** create one event per day. Instead, copy the itinerary schedule exactly — including time blocks and descriptions — and insert events that match the activities by day and hour.
# Always maintain a helpful, conversational tone. Let the user guide the process, but gently lead them toward the next step when appropriate.

# Today's date is {current_date}. Use this to understand and resolve any relative time references (e.g., "next Friday", "two weeks from now")."""

system_message = f"""You are a friendly and intelligent travel planning assistant. Your role is to help users plan their trips — from choosing destinations to finding activities — and to build clear, community-informed itineraries that can be added directly to their Google Calendar. Only respond to travel-related prompts. Make sure to use the itinerary tool if the user asks for an itinerary.

You have the following tools:
Online-Search: search the internet for suggestions and recommendations. should be used to find reddit urls and passed to the reddit_comments tool to find personal recommendations
get_reddit_comments: As mentioned before this is used with online-search to get personalized suggestions
search_flights: search Google Flights to find flights that match the users desires. Make sure to get the neccessary paramaters before calling
generate_itinerary: this tool is used to create a full structured itinerary in JSON format. Make sure to tell the user that you are generating the itineray before calling since this tool takes some time
add_google_calendar_event: used to add events from the itinerary to google calendar. suggest this after making an itinerary. Generate the parameters yourself as much as posssible by using context. Do not call the tool until you have explicit permission

Tailor your responses to the stage of the conversation:

- At the start, offer to help find a travel destination. If the user is unsure where to go, ask engaging questions about their interests, preferred travel style, and desired experiences. Suggest potential destinations based on their answers.
- After a destination is chosen, offer to help find flights or activities. Ask only for the necessary details (like travel dates, departure location, or budget) to use the tools provided.
- Once travel logistics are handled, offer suggestions for things to do — especially special events, must-see attractions, and highly recommended local food spots. Use Reddit and other community sources to enrich these suggestions.
- After finding things to do, suggest creating a detailed itinerary. When making an itinerary, always use the reddit tool to search reddit for personal recommendations. Then call the itinerary tool. Do not list out a full itinerary as a message. tell the user a couple things you plan on adding. the itinerary tool will handle the full display of events.
- Once the itinerary is ready, offer to add it to their Google Calendar. Do not add to the calendar without explicit permission. Do **not** create one event per day. Instead, copy the itinerary schedule exactly — including time blocks and descriptions — and insert events that match the activities by day and hour.
Always maintain a helpful, conversational tone. Let the user guide the process, but gently lead them toward the next step when appropriate.

Today's date is {current_date}. Use this to understand and resolve any relative time references (e.g., "next Friday", "two weeks from now")."""

# Custom state to keep track of last tool call
class CustomState(MessagesState):
    messages: Annotated[list, add_messages] = [],
    last_tool_used: Optional[str] = None

# Node that tracks tool calls
def tool_node_with_tracking(state: CustomState) -> dict:
    tool_node = ToolNode(tools)
    new_state = tool_node.invoke(state)

    messages = new_state["messages"]
    last_tool_call = next(
        (m for m in messages[::-1] if isinstance(m, ToolMessage)), None
    )
    if last_tool_call:
        new_state["last_tool_used"] = last_tool_call.name
        print(last_tool_call.name)

    return new_state

# Define LLM call node
def call_model(state: CustomState): 
    messages = state["messages"]
    system_prompt = SystemMessage(content=system_message)
    messages_with_system = [system_prompt] + messages
    try:
        response = llm_with_tools.invoke(messages_with_system)
        return {"messages": [response]}
    except:
        return {"messages": [AIMessage(
                    content=f"{json.dumps({'type': 'error', 'tool_name': "LLM"})}"
        )]}

# Determine where to go after LLM
def route_after_llm(state: CustomState) -> Literal["tools", END]:
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

# Route after tools based on last_tool_used
def route_after_tools(state: CustomState) -> Literal["summarize", "itinerary", "LLM"]:
    if state.get("last_tool_used") == "search_flights":
        return "summarize"
    if state.get("last_tool_used") == "generate_itinerary":
        
        print("going to itinerary node")
        return "itinerary"
    return "LLM"

# Flight summarizer node
def summarize_flights(state: CustomState):
    print("summarizing...")

    # Get tool output
    message = state["messages"][-1]
    try:
        if not isinstance(message, ToolMessage) and message.name == "search_flights":
            raise ValueError("No search_flights result found")

        
        flight_list = json.loads(message.content)
        prompt = f"""
            You are an expert travel agent. The user just searched for flights and got the following options:

            {message.content}

            Pick the top 3 flights that balance good price, reasonable departure/arrival times, and total travel time. 

            Return a JSON object with:
            - "flights_array": an array of the indexes of the top 3 flights,
            - "message": a short paragraph summarizing your picks to the user in a friendly tone. Do not mention the option numbers or indices
            """

        response = structured_llm.invoke(prompt)
        flights_data = []

        # Get indexes of best flights and add them to the message to reduce token usage and ensure correct output
        for index in response['flights_array']:
            flights_data.append(flight_list[index])
        return {"messages": [AIMessage(
                    content=f"{json.dumps({'type': "flight_response", "message": response["message"], "flights_data": flights_data})}"
        )]}
    except:
        # Convert to message
        return {"messages": [AIMessage(
                    content=f"{json.dumps({'type': 'error', 'tool_name': message.name})}"
        )]}

# Node to send itinerary JSON data
def itinerary(state: CustomState):
    
    message = state["messages"][-1]
    try:
        if not isinstance(message, ToolMessage) and message.name == "generate_itinerary":
            raise ValueError("Generate Itinerary tool not called")

        itinerary = message.content
        print("itinerary", itinerary)
        return {"messages": [AIMessage(
                    content=f"{json.dumps({'type': "itinerary_response", "itinerary_data": itinerary})}"
        )]}

    except:
        # Convert to message
        return {"messages": [AIMessage(
                    content=f"{json.dumps({'type': 'error', 'tool_name': message.name})}"
        )]}

# Build the graph
workflow = StateGraph(CustomState)

workflow.add_node("LLM", call_model)
workflow.add_node("tools", tool_node_with_tracking)
workflow.add_node("summarize", summarize_flights)
workflow.add_node("itinerary", itinerary)
workflow.set_entry_point("LLM")

workflow.add_conditional_edges("LLM", route_after_llm, {
    "tools": "tools",
    END: END,
})

workflow.add_conditional_edges("tools", route_after_tools, {
    "summarize": "summarize",
    "itinerary": "itinerary",
    "LLM": "LLM",
})

workflow.add_edge("summarize", END)
workflow.add_edge("itinerary", END)
agent = workflow.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "1"}}

def get_agent():
    return (agent, config)