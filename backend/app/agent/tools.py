from langchain_core.tools import tool, Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from serpapi import GoogleSearch
from langchain_google_community import CalendarToolkit
import os
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import praw
load_dotenv()

search_tool = Tool(
    name="Online-Search",
    func=GoogleSerperAPIWrapper().run,
    description="use to get suggestions for the user. Search for special events going on during the stay of the user. Search for reddit threads and pass the url to the get_reddit_comments tool. For example if a user asks for things to do in Cancun, search for 'things to do in Cancun reddit' and pass the url to the get_reddit_comments threads to get suggestions.",
)

calendar_tools = CalendarToolkit().get_tools()
# remove datetime tool causing errors
calendar_tools.pop()
#remove delete calendar event 
calendar_tools.pop()

class FlightSearchParams(BaseModel):
    departure_id: str = Field(..., description="REQUIRED: The 3 letter ID of the departure airport. For example, 'JFK' for John F. Kennedy International Airport. You can specify multiple departure airports by separating them with a comma. For example, CDG,ORY for both Charles de Gaulle and Orly airports in Paris.")
    arrival_id: str = Field(..., description="REQUIRED: The 3 letter ID of the arrival airport. For example, 'JFK' for John F. Kennedy International Airport. You can specify multiple arrvial airports by separating them with a comma. For example, CDG,ORY for both Charles de Gaulle and Orly airports in Paris.")
    outbound_date: str = Field(..., description="REQUIRED: The date of the outbound flight in YYYY-MM-DD format.")
    return_date: str = Field(..., description="REQUIRED if flight is round trip, otherwise OPTIONAL: The date of the return flight in YYYY-MM-DD format.")
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
    return_date: str = "",
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
    A JSON object containing available flight options. Use this data to present multiple choices to the user, highlighting relevant factors like price, number of stops, airlines, and duration.
"""
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "outbound_date": outbound_date,
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
    if return_date:
        params["return_date"] = return_date
    if exclude_airlines:
        params["exclude_airlines"] = exclude_airlines
    if include_airlines:
        params["include_airlines"] = include_airlines


    # Call Google Flight API
    search = GoogleSearch(params)
    results = search.get_dict()

    return results

class HotelSearchParams(BaseModel):
    location: str = Field(..., description="REQUIRED: The location to search for hotels, e.g., 'Chicago'.")
    check_in_date: str = Field(..., description="REQUIRED: Check-in date in YYYY-MM-DD format.")
    check_out_date: str = Field(..., description="REQUIRED: Check-out date in YYYY-MM-DD format.")
    adults: int = Field(2, description="OPTIONAL: Number of adults. Default is 2.")
    children: int = Field(0, description="OPTIONAL: Number of children. Default is 0.")
    children_ages: Optional[str] = Field(None, description="OPTIONAL: Ages of children separated by commas (e.g., '5,8'). Must match number of children.")
    sort_by: Optional[int] = Field(13, description="OPTIONAL: Sorting order. Options: 3=Lowest price, 8=Highest rating, 13=Most reviewed. Default is 13.")
    min_price: Optional[int] = Field(0, description="OPTIONAL: Minimum price filter.")
    max_price: Optional[int] = Field(10000, description="OPTIONAL: Maximum price filter.")
    rating: Optional[int] = Field(7, description="OPTIONAL: Minimum hotel rating. Options: 7=3.5+, 8=4.0+, 9=4.5+.")
    property_types: Optional[str] = Field(None, description="OPTIONAL: Property type IDs, separated by commas.")
    amenities: Optional[str] = Field(None, description="OPTIONAL: Amenity IDs, separated by commas.")
    brands: Optional[str] = Field(None, description="OPTIONAL: Hotel brand IDs, separated by commas.")
    hotel_class: Optional[str] = Field(None, description="OPTIONAL: Hotel class IDs (2, 3, 4, 5), separated by commas.")
    free_cancellation: Optional[bool] = Field(None, description="OPTIONAL: Whether to only show hotels with free cancellation.")
    special_offers: Optional[bool] = Field(None, description="OPTIONAL: Whether to only show hotels with special offers.")
    eco_certified: Optional[bool] = Field(None, description="OPTIONAL: Whether to only show eco-certified hotels.")
    gl: Optional[str] = Field(None, description="OPTIONAL: Country code for localization (e.g., 'us', 'fr').")
    hl: Optional[str] = Field(None, description="OPTIONAL: Language code (e.g., 'en', 'es').")
    currency: Optional[str] = Field("USD", description="OPTIONAL: Currency for returned prices. Default is 'USD'.")

@tool("search_hotels", args_schema=HotelSearchParams)
def search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    children: int = 0,
    children_ages: Optional[str] = None,
    sort_by: Optional[int] = 13,
    min_price: Optional[int] = 0,
    max_price: Optional[int] = 10000,
    rating: Optional[int] = 7,
    property_types: Optional[str] = None,
    amenities: Optional[str] = None,
    brands: Optional[str] = None,
    hotel_class: Optional[str] = None,
    free_cancellation: Optional[bool] = None,
    special_offers: Optional[bool] = None,
    eco_certified: Optional[bool] = None,
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = "USD"
) -> dict:
    """
    Search for hotels using Google Hotels.
    """
    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "gl": gl,
        "hl": hl,
        "currency": currency,
        "adults": adults,
        "children": children,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }

    # Optional Parameters
    if children > 0 and children_ages:
        params["children_ages"] = children_ages
    if sort_by is not None:
        params["sort_by"] = sort_by
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if property_types:
        params["property_types"] = property_types
    if amenities:
        params["amenities"] = amenities
    if rating is not None:
        params["rating"] = rating
    if brands:
        params["brands"] = brands
    if hotel_class:
        params["hotel_class"] = hotel_class
    if free_cancellation:
        params["free_cancellation"] = "true"
    if special_offers:
        params["special_offers"] = "true"
    if eco_certified:
        params["eco_certified"] = "true"

    # Call Google Hotels API
    search = GoogleSearch(params)
    results = search.get_dict()
    return results

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
    Get top 10 reddit comments from a URL.
    """
    submission = reddit.submission(url=url)
    submission.comments.replace_more(limit=0)  # flatten comment tree

    top_comments = []
    for comment in submission.comments[:10]:
        top_comments.append(comment.body)

    return top_comments

# tools = [search_tool, search_flights, search_hotels, make_itinerary]
tools = [search_tool, search_flights, search_hotels, get_reddit_comments] + calendar_tools

def get_tools():
    """
    Returns the list of tools available for the agent.
    """
    return tools

# print(get_reddit_suggestions("https://www.reddit.com/r/TravelHacks/comments/12ppmqx/must_dos_in_cancun/"))