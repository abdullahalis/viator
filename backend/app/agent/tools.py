from langchain_core.tools import tool, Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI
from serpapi import GoogleSearch
from langchain_google_community import CalendarToolkit
import os
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import praw
from datetime import date
from typing import List, Optional

load_dotenv()

search_tool = Tool(
    name="Online-Search",
    func=GoogleSerperAPIWrapper().run,
    description="use to get suggestions for the user. Search for special events going on during the stay of the user. Search for reddit threads and pass the url to the get_reddit_comments tool. For example if a user asks for things to do in Cancun, search for 'things to do in Cancun reddit' and pass the url to the get_reddit_comments threads to get suggestions.",
)

calendar_tools = CalendarToolkit().get_tools()
print("tools", calendar_tools)
calendar_add = calendar_tools[0] 
print("tools", calendar_add)
# remove datetime tool causing errors
# calendar_tools.pop()
# #remove delete calendar event for safety
# calendar_tools.pop()

class FlightSearchParams(BaseModel):
    departure_id: str = Field(..., description="REQUIRED: The 3 letter ID of the departure airport. For example, 'JFK' for John F. Kennedy International Airport. You can specify multiple departure airports by separating them with a comma. For example, CDG,ORY for both Charles de Gaulle and Orly airports in Paris.")
    arrival_id: str = Field(..., description="REQUIRED: The 3 letter ID of the arrival airport. For example, 'JFK' for John F. Kennedy International Airport. You can specify multiple arrvial airports by separating them with a comma. For example, CDG,ORY for both Charles de Gaulle and Orly airports in Paris.")
    outbound_date: str = Field(..., description="REQUIRED: The date of the outbound flight in YYYY-MM-DD format.")
    return_date: str = Field(..., description="REQUIRED: The date of the return flight in YYYY-MM-DD format.")
    type: int = Field(1, description="OPTIONAL Parameter defines the type of flight. Available options: 1 - Round-trip (default), 2 - One-way")
    travel_class: int = Field(1, description="OPTIONAL Parameter defines the travel class. Available options: 1 - Economy (default), 2 - Premium economy, 3 - Business, 4 - First")
    adults: int = Field(1, description="OPTIONAL Number of adults traveling. Default is 1.")
    children: int = Field(0, description="OPTIONAL Number of children traveling. Default is 1.")
    infants_in_seat: int = Field(0, description="OPTIONAL Number of infants in seat. Default is 0.")
    infants_in_lap: int = Field(0, description="OPTIONAL Number of infants in lap. Default is 0.")
    bags: int = Field(0, description="OPTIONAL Number of bags. Default is 0. Parameter should not exceed the total number of passengers with carry-on bag allowance (adults, children and infants_in_seat). For example, if you have 2 adults, 1 child and 1 infant_in_seat, you can have a maximum of 4 bags.")
    sort_by: int = Field(1, description="OPTIONAL Parameter defines the sorting order of the results. Available options: 1 - Top flights (default), 2 - Price, 3 - Departure time, 4 - Arrival time, 5 - Duration, 6 - Emissions")
    stops: int = Field(0, description="OPTIONAL Number of stops during the flight. 0 - Any number of stops (default), 1 - Nonstop only, 2 - 1 stop or fewer, 3 - 2 stops or fewer")
    exclude_airlines: str = Field("", description="OPTIONAL Comma-separated list of airline codes to exclude from the results. For example, 'AA,DL' to exclude American Airlines and Delta Air Lines.")
    include_airlines: str = Field("", description="OPTIONAL Comma-separated list of airline codes to include in the results. For example, 'AA,DL' to include only American Airlines and Delta Air Lines.")
    max_price: int = Field(10000, description="OPTIONAL Maximum price for the flight. Default is 10000.")
    currency: str = Field("USD", description="OPTIONAL Currency code (e.g., USD). Default is USD.")
    hl: str = Field("en", description="OPTIONAL Language code (e.g., en for English). Default is en.")
 
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

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent="viator_agent"
)

class RedditCommentsParams(BaseModel):
    url: str = Field(..., description="URL of the Reddit page to get comments from. For example, https://www.reddit.com/r/TravelHacks/comments/12ppmqx/must_dos_in_cancun/")

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


# Set up LLM with structured JSON output
structured_llm = ChatOpenAI(
    model="gpt-4o",
    tags=["structured"]
).with_structured_output(method='json_mode')

# --- Input Schema ---
class ItineraryParams(BaseModel):
    location: str = Field(..., description="The destination city or region")
    start_date: str = Field(..., description="Start date of the trip in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date of the trip in YYYY-MM-DD format")
    interests: Optional[List[str]] = Field(default_factory=list, description="Optional list of travel interests (e.g. food, museums, hiking)")

# --- Tool Function ---
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
tools = [search_tool, search_flights, get_reddit_comments, generate_itinerary, calendar_add]

def get_tools():
    """
    Returns the list of tools available for the agent.
    """
    return tools