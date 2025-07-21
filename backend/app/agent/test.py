from dotenv import load_dotenv
from typing import Literal, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
import json
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from agent.tools import get_tools  # Your custom tool loader

load_dotenv()

# 1. Load model and tools
llm = init_chat_model("gpt-4o-mini", model_provider="openai")
structured_llm = ChatOpenAI(model="gpt-4o").with_structured_output(method="json_mode")
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)

# 2. Track last tool in state
class CustomState(MessagesState):
    last_tool_used: Optional[str] = None

# 3. Define tool node wrapper to also save last_tool_used
def tool_node_with_tracking(state: CustomState) -> dict:
    tool_node = ToolNode(tools)
    new_state = tool_node.invoke(state)

    messages = new_state["messages"]
    last_tool_call = next(
        (m for m in messages[::-1] if isinstance(m, ToolMessage)), None
    )
    print("last call", last_tool_call)
    if last_tool_call:
        new_state["last_tool_used"] = last_tool_call.name

    return new_state

# 4. Define LLM call
def call_model(state: CustomState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 5. Determine where to go after LLM
def route_after_llm(state: CustomState) -> Literal["tools", END]:
    print(state)
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

# 6. Route after tools based on last_tool_used
def route_after_tools(state: CustomState) -> Literal["summarize", "LLM"]:
    print("staet tool used", state.get("last_tool_used"))
    if state.get("last_tool_used") == "search_flights":
        return "summarize"
    return "LLM"

# 7. Summarization logic
def summarize_flights(state: CustomState):
    print("summarizing...")
    # Get tool output
    message = state["messages"][-1]
    if not isinstance(message, ToolMessage) and message.name == "search_flights":
        raise ValueError("No search_flights result found")
    
    flight_list = json.loads(message.content)
    prompt = f"""
        You are an expert travel agent. The user just searched for flights and got the following options:

        {message.content}

        Pick the top 3 flights that balance good price, reasonable departure/arrival times, and total travel time. 

        Return a JSON object with:
        - "flights": an array of the indexes of the top 3 flights,
        - "message": a short paragraph summarizing your picks to the user in a friendly tone.
        """

    response = structured_llm.invoke(prompt)
    flights_data = []
    for index in response['flights']:
        flights_data.append(flight_list[index])

    response['flights'] = flights_data

    # Convert to message
    return {"messages": state["messages"] + [AIMessage(
                content=json.dumps({
            "message": response["message"],
            "flights": response["flights"]
        })
    )]}

# 8. Build the graph
workflow = StateGraph(CustomState)

workflow.add_node("LLM", call_model)
workflow.add_node("tools", tool_node_with_tracking)
workflow.add_node("summarize", summarize_flights)
workflow.set_entry_point("LLM")

workflow.add_conditional_edges("LLM", route_after_llm, {
    "tools": "tools",
    END: END,
})

workflow.add_conditional_edges("tools", route_after_tools, {
    "summarize": "summarize",
    "LLM": "LLM",
})

workflow.add_edge("summarize", END)
agent = workflow.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "1"}}

def get_agent():
    return (agent, config)
# # Example run
# for chunk in agent.stream(
#     {"messages": [("user", "Show me flights from ORD to MIA round trip on August 7, 2025 for one week")]},
#     stream_mode="values",
# ):
#     if "messages" in chunk:
#         chunk["messages"][-1].pretty_print()

# from dotenv import load_dotenv
# from typing import Annotated, Literal
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages
# from langchain.chat_models import init_chat_model
# from pydantic import BaseModel, Field
# from typing_extensions import TypedDict
# from tools import get_tools
# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
# from langgraph.types import Command, interrupt
# from langgraph.graph import MessagesState, START

# load_dotenv()

# llm = init_chat_model("gpt-4o-mini",model_provider="openai")

# tools = get_tools()  # Returns list of Tool instances
# llm_with_tools = llm.bind_tools(tools)
# # Map tool names to individual nodes
# tool_node = ToolNode(tools)

# def call_model(state: MessagesState):
#     messages = state["messages"]
#     response = llm_with_tools.invoke(messages)
#     return {"messages": [response]}

# def call_tools(state: MessagesState) -> Literal["tools", END]:
#     messages = state["messages"]
#     last_message = messages[-1]
#     print("last message", last_message)
#     if last_message.tool_calls:
#         return "tools"
#     return END

# # initialize the workflow from StateGraph
# workflow = StateGraph(MessagesState)

# # add a node named LLM, with call_model function. This node uses an LLM to make decisions based on the input given
# workflow.add_node("LLM", call_model)

# # Our workflow starts with the LLM node
# workflow.add_edge(START, "LLM")

# # Add a tools node
# workflow.add_node("tools", tool_node)

# # Add a conditional edge from LLM to call_tools function. It can go tools node or end depending on the output of the LLM. 
# workflow.add_conditional_edges("LLM", call_tools)

# # tools node sends the information back to the LLM
# workflow.add_edge("tools", "LLM")

# agent = workflow.compile()

# for chunk in agent.stream(
#     {"messages": [("user", "Search the internet for news today")]},
#     stream_mode="values",):
#     chunk["messages"][-1].pretty_print()





# class MessageClassifier(BaseModel):
#     message_type: Literal["suggestions", "itinerary", "calendar"] = Field(
#         ...,
#         description="Classify if the message requires giving suggestions, creating an itinerary, or adding an itinerary to Google Calendar."
#     )

# class State(TypedDict):
#     messages: Annotated[list, add_messages]
#     message_type: str | None
#     location: str | None
#     dates: str | None
#     itinerary: str | None

# def classify_message(state: State):
#     last_message = state["messages"][-1]
#     classifier_llm = llm.with_structured_output(MessageClassifier)

#     result = classifier_llm.invoke([
#         {
#             "role": "system",
#             "content": """Classify the user message as either:
#             - 'suggestions': if it asks for suggestions for events to go to, things to do, or places to eat
#             - 'itinerary': if it asks to create an itinerary
#             - 'calendar': if it asks to add events to the Google Calendar
#             """
#         },
#         {"role": "user", "content": last_message.content}
#     ])
#     return {"message_type": result.message_type}

# def router(state: State):
#     message_type = state.get("message_type", "suggestions")

#     if message_type == "suggestions":
#         return {"next": "suggestions"}
#     if message_type == "itinerary":
#         return {"next": "itinerary"}

#     return {"next": "calendar"}

# def suggestions_agent(state: State):
#     print("Suggestion agent")
#     last_message = state["messages"][-1]

#     messages = [
#         {"role": "system",
#          "content": """You are a helpful travel agent. Give suggestions of things to do based on the user's destination."""
#          },
#         {
#             "role": "user",
#             "content": last_message.content
#         }
#     ]
#     reply = llm.invoke(messages)
#     return {"messages": [{"role": "assistant", "content": reply.content}]}

# def itinerary_agent(state: State):
#     print("itini agent")
#     last_message = state["messages"][-1]

#     messages = [
#         {"role": "system",
#          "content": """You are a helpful itinerary maker. Create an in-depth itinerary of events, things to do, and places to eat broken down by day and hour."""
#          },
#         {
#             "role": "user",
#             "content": last_message.content
#         }
#     ]
#     reply = llm.invoke(messages)
#     return {"messages": [{"role": "assistant", "content": reply.content}]}

# def calendar_agent(state: State):
#     print("calendar agent")
#     last_message = state["messages"][-1]

#     messages = [
#         {"role": "system",
#          "content": """You are a helpful Google Calendar assistant. Add the events of the itinerary broken down by day and hour to the Google Calendar."""
#          },
#         {
#             "role": "user",
#             "content": last_message.content
#         }
#     ]
#     reply = llm.invoke(messages)
#     return {"messages": [{"role": "assistant", "content": reply.content}]}

# graph_builder = StateGraph(State)

# graph_builder.add_node("classifier", classify_message)
# graph_builder.add_node("router", router)
# graph_builder.add_node("suggestions", suggestions_agent)
# graph_builder.add_node("itinerary", itinerary_agent)
# graph_builder.add_node("calendar", calendar_agent)
# @tool("test_tool")
# def test_tool():
#     """Test function"""
#     print("testing")

# test_node =ToolNode([test_tool])
# graph_builder.add_node("test", test_node)

# graph_builder.add_edge(START, "classifier")
# graph_builder.add_edge("classifier", "router")

# graph_builder.add_conditional_edges(
#     "router",
#     lambda state: state.get("next"),
#     {"itinerary": "itinerary", "suggestions": "suggestions", "calendar": "calendar"}
# )

# graph_builder.add_edge("itinerary", END)
# graph_builder.add_edge("suggestions", "test")
# graph_builder.add_edge("test", END)
# graph_builder.add_edge("calendar", END)

# graph = graph_builder.compile()

# def run_chatbot():
#     state = {"messages": [], "message_type": None}

#     while True:
#         user_input = input("Message: ")
#         if user_input == "exit":
#             print("Bye")
#             break

#         state["messages"] = state.get("messages", []) + [
#             {"role": "user", "content": user_input}
#         ]

#         state = graph.invoke(state)

#         if state.get("messages") and len(state["messages"]) > 0:
#             last_message = state["messages"][-1]
#             print(f"Assistant: {last_message.content}")

# run_chatbot()
