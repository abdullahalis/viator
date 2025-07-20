from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from tools import get_tools
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from langgraph.graph import MessagesState, START

load_dotenv()

llm = init_chat_model("gpt-4o-mini",model_provider="openai")
class AskHuman(BaseModel):
    """Ask the human a question"""

    question: str

tools = get_tools()
tool_node = ToolNode(tools)
# tools.append(AskHuman)
print(tools)

llm_with_tools = llm.bind(tools)

# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return END
    # If tool call is asking Human, we return that node
    # You could also add logic here to let some system know that there's something that requires Human input
    # For example, send a slack message, etc
    elif last_message.tool_calls[0]["name"] == "AskHuman":
        return "ask_human"
    # Otherwise if there is, we continue
    else:
        return "action"


# Define the function that calls the model
def call_model(state):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# We define a fake node to ask the human
def ask_human(state):
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    ask = AskHuman.model_validate(state["messages"][-1].tool_calls[0]["args"])
    location = interrupt(ask.question)
    tool_message = [{"tool_call_id": tool_call_id, "type": "tool", "content": location}]
    return {"messages": tool_message}

# Build the graph

from langgraph.graph import END, StateGraph

# Define a new graph
workflow = StateGraph(MessagesState)

# Define the three nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.add_node("ask_human", ask_human)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    path_map=["ask_human", "action", END],
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# After we get back the human response, we go back to the agent
workflow.add_edge("ask_human", "agent")

# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "2"}}
for event in app.stream(
    {
        "messages": [
            (
                "user",
                "Ask the user what their destination is then help them book a flight",
            )
        ]
    },
    config,
    stream_mode="values",
):
    if "messages" in event:
        event["messages"][-1].pretty_print()
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

# graph_builder.add_edge(START, "classifier")
# graph_builder.add_edge("classifier", "router")

# graph_builder.add_conditional_edges(
#     "router",
#     lambda state: state.get("next"),
#     {"itinerary": "itinerary", "suggestions": "suggestions", "calendar": "calendar"}
# )

# graph_builder.add_edge("itinerary", END)
# graph_builder.add_edge("suggestions", END)
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
