from langchain_core.tools import tool, Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
import praw
from typing import List
from googleapiclient.discovery import build

from google_functions import google_authenticate, build_event_data, extract_event_links
from agent.schemas import *

load_dotenv()

# Initialize LLM and services needed to run tools
service = build('calendar', 'v3', credentials=google_authenticate())

structured_llm = ChatOpenAI(
    model="gpt-4o",
    tags=["structured"]
).with_structured_output(method='json_mode')

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent="viator_agent"
)

# TOOLS
search_tool = Tool(
    name="online_search",
    func=GoogleSerperAPIWrapper().run,
    description="use to get suggestions for the user. Search for special events going on during the stay of the user. Search for reddit threads and pass the url to the get_reddit_comments tool. For example if a user asks for things to do in Cancun, search for 'things to do in Cancun reddit' and pass the url to the get_reddit_comments threads to get suggestions.",
)

@tool("add_google_calendar_event", args_schema=Events)
def add_google_calendar_event(events: Events):
    """
    Tool for adding events to google calendar. Returns list of the title of event added and the link to open it. Make sure links are opened in a new tab when clicked.
    """
    try:
        batch = service.new_batch_http_request()
        for event in events:
            event_data = build_event_data(event)
            print("event", event_data)
            batch.add(service.events().insert(calendarId="primary", body=event_data))
        
        batch.execute()
        links = extract_event_links(batch._responses)
        if links:
            return links
        
        return "Error occured when creating events"

    except Exception as e:
        print(f"Error occured: {e}")
        return f"Error occured: {e}"    
 
@tool("search_flights", args_schema=FlightSearchParams)
def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    type: int = 1,
    travel_class: int = 1,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_in_lap: int = 0,
    bags: int = 0,
    sort_by: int = 1,
    stops: int = 0,
    exclude_airlines: str = "",
    include_airlines: str = "",
    max_price: int = 10000,
    currency: str = "USD",
    hl: str = "en"
) -> str:
    """
Searches for flights using Google Flights.

Use this tool only if the user has specified or you can infer:
- A departure location
- An outbound (departure) date

If it's a round trip, a return date must also be provided. Other parameters like destination, budget, and number of stops are optional and can be inferred or asked for in conversation.

Returns:
    A JSON object containing available flight options. Use this data to present multiple choices to the user but use conversational language, highlighting relevant factors like price, number of stops, airlines, and duration.
    Do not return the JSON to the user.
"""
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "type": type,
        "travel_class": travel_class,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_in_lap": infants_in_lap,
        "bags": bags,
        "sort_by": sort_by,
        "stops": stops,
        "max_price": max_price,
        "currency": currency,
        "hl": hl,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }

    # Optional parameters
    if arrival_id:
        params["arrival_id"] = arrival_id
    if exclude_airlines:
        params["exclude_airlines"] = exclude_airlines
    if include_airlines:
        params["include_airlines"] = include_airlines


    # Call Google Flight API
    search = GoogleSearch(params)
    results = search.get_dict()

    if results["best_flights"]:
        return results["best_flights"]
    return results["other_flights"]

@tool("get_reddit_comments", args_schema=RedditCommentsParams)
def get_reddit_comments(url):
    """
    Get top 10 reddit comments from a URL to get personal recommenations and suggestions from the community.
    """
    submission = reddit.submission(url=url)
    submission.comments.replace_more(limit=0)  # flatten comment tree

    top_comments = []
    for comment in submission.comments[:10]:
        top_comments.append(comment.body)

    return top_comments

@tool("generate_itinerary", args_schema=ItineraryParams)
def generate_itinerary(location: str, start_date: str, end_date: str, interests: List[str] = ["food", "sightseeing", "local experiences"]): 
    """
    Creates a structured day-by-day itinerary in JSON format for a given location, date range, and optional interests.
    Suitable for frontend display or exporting to a calendar.
    """
    interest_text = ", ".join(interests)

    prompt = (
        f"Plan a multi-day trip to {location} from {start_date} to {end_date}. "
        f"Tailor it to the following interests: {interest_text}. "
        f"""Return only structured JSON in this format: 
        class Activity(BaseModel):
            time: str
            title: str
            description: str

        class DayPlan(BaseModel):
            date: str
            activities: List[Activity]

        class Itinerary(BaseModel):
            location: str
            days: List[DayPlan]"""
    )
    result =  structured_llm.invoke(prompt)
    return result

# All tools
tools = [search_tool, search_flights, get_reddit_comments, generate_itinerary, add_google_calendar_event]

def get_tools():
    """
    Returns the list of tools available for the agent.
    """
    return tools