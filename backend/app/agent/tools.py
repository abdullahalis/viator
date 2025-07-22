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
# remove datetime tool causing errors
calendar_tools.pop()
#remove delete calendar event 
calendar_tools.pop()

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

    return [{'flights': [{'departure_airport': {'name': "Chicago O'Hare International Airport", 'id': 'ORD', 'time': '2025-07-25 08:25'}, 'arrival_airport': {'name': 'Miami International Airport', 'id': 'MIA', 'time': '2025-07-25 12:35'}, 'duration': 190, 'airplane': 'Boeing 737', 'airline': 'American', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/AA.png', 'travel_class': 'Economy', 'flight_number': 'AA 1250', 'legroom': '30 in', 'extensions': ['Average legroom (30 in)', 'Wi-Fi for a fee', 'In-seat power & USB outlets', 'Stream media to your device', 'Carbon emissions estimate: 154 kg']}], 'total_duration': 190, 'carbon_emissions': {'this_flight': 154000, 'typical_for_this_route': 158000, 'difference_percent': -3}, 'price': 563, 'type': 'Round trip', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/AA.png', 'extensions': ['Checked baggage for a fee', 'Bag and fare conditions depend on the return flight'], 'departure_token': 'WyJDalJJY2pCd2N6VkhVVU41U1ZWQlNFZEZjM2RDUnkwdExTMHRMUzB0TFhscGFXUXhNRUZCUVVGQlIyZ3Rablp6U0dZd2JtdEJFZ1pCUVRFeU5UQWFDd2pzdHdNUUFob0RWVk5FT0J4dzdMY0QiLFtbIk9SRCIsIjIwMjUtMDctMjUiLCJNSUEiLG51bGwsIkFBIiwiMTI1MCJdXV0='}, {'flights': [{'departure_airport': {'name': "Chicago O'Hare International Airport", 'id': 'ORD', 'time': '2025-07-25 11:15'}, 'arrival_airport': {'name': 'Raleigh-Durham International Airport', 'id': 'RDU', 'time': '2025-07-25 14:25'}, 'duration': 130, 'airplane': 'Airbus A320neo', 'airline': 'Frontier', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/F9.png', 'travel_class': 'Economy', 'flight_number': 'F9 3352', 'legroom': '28 in', 'extensions': ['Below average legroom (28 in)', 'Carbon emissions estimate: 86 kg'], 'often_delayed_by_over_30_min': True}, {'departure_airport': {'name': 'Raleigh-Durham International Airport', 'id': 'RDU', 'time': '2025-07-25 15:17'}, 'arrival_airport': {'name': 'Miami International Airport', 'id': 'MIA', 'time': '2025-07-25 17:32'}, 'duration': 135, 'airplane': 'Airbus A320neo', 'airline': 'Frontier', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/F9.png', 'travel_class': 'Economy', 'flight_number': 'F9 3321', 'legroom': '28 in', 'extensions': ['Below average legroom (28 in)', 'Carbon emissions estimate: 92 kg'], 'often_delayed_by_over_30_min': True}], 'layovers': [{'duration': 52, 'name': 'Raleigh-Durham International Airport', 'id': 'RDU'}], 'total_duration': 317, 'carbon_emissions': {'this_flight': 179000, 'typical_for_this_route': 158000, 'difference_percent': 13}, 'price': 297, 'type': 'Round trip', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/F9.png', 'extensions': ['Checked baggage for a fee', 'Bag and fare conditions depend on the return flight'], 'departure_token': 'WyJDalJJY2pCd2N6VkhVVU41U1ZWQlNFZEZjM2RDUnkwdExTMHRMUzB0TFhscGFXUXhNRUZCUVVGQlIyZ3Rablp6U0dZd2JtdEJFZzFHT1RNek5USjhSamt6TXpJeEdnc0loT2dCRUFJYUExVlRSRGdjY0lUb0FRPT0iLFtbIk9SRCIsIjIwMjUtMDctMjUiLCJSRFUiLG51bGwsIkY5IiwiMzM1MiJdLFsiUkRVIiwiMjAyNS0wNy0yNSIsIk1JQSIsbnVsbCwiRjkiLCIzMzIxIl1dXQ=='}, {'flights': [{'departure_airport': {'name': "Chicago O'Hare International Airport", 'id': 'ORD', 'time': '2025-07-25 08:09'}, 'arrival_airport': {'name': 'Miami International Airport', 'id': 'MIA', 'time': '2025-07-25 12:23'}, 'duration': 194, 'airplane': 'Airbus A321 (Sharklets)', 'airline': 'Spirit', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/NK.png', 'travel_class': 'Economy', 'flight_number': 'NK 1101', 'legroom': '28 in', 'extensions': ['Below average legroom (28 in)', 'Wi-Fi for a fee', 'Carbon emissions estimate: 163 kg']}], 'total_duration': 194, 'carbon_emissions': {'this_flight': 164000, 'typical_for_this_route': 158000, 'difference_percent': 4}, 'price': 488, 'type': 'Round trip', 'airline_logo': 'https://www.gstatic.com/flights/airline_logos/70px/NK.png', 'extensions': ['Checked baggage for a fee', 'Bag and fare conditions depend on the return flight'], 'departure_token': 'WyJDalJJY2pCd2N6VkhVVU41U1ZWQlNFZEZjM2RDUnkwdExTMHRMUzB0TFhscGFXUXhNRUZCUVVGQlIyZ3Rablp6U0dZd2JtdEJFZ1pPU3pFeE1ERWFDd2llL1FJUUFob0RWVk5FT0J4d252MEMiLFtbIk9SRCIsIjIwMjUtMDctMjUiLCJNSUEiLG51bGwsIk5LIiwiMTEwMSJdXV0='}]

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


# 1. Define the output schema
class Activity(BaseModel):
    time: str
    title: str
    description: str

class DayPlan(BaseModel):
    date: str
    activities: List[Activity]

class Itinerary(BaseModel):
    location: str
    days: List[DayPlan]
    
# 3. Set up the LLM with structured JSON output
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
    # print("prompt", prompt)
    # Call the model
    # result =  structured_llm.invoke(prompt)
    # print("result in tools", result)
    result = {"location": "Los Angeles", "days": [{"date": "2025-07-25", "activities": [{"time": "10:00", "title": "Santa Monica Pier", "description": "Visit the iconic Santa Monica Pier and explore the various seafood eateries offering fresh catches."}, {"time": "13:00", "title": "Lunch at The Lobster", "description": "Dine at The Lobster, known for its exquisite seafood cuisine with stunning ocean views."}, {"time": "16:00", "title": "Explore Venice Beach", "description": "Stroll along Venice Beach, enjoying the lively atmosphere and various oceanfront food stalls."}]}, {"date": "2025-07-26", "activities": [{"time": "08:00", "title": "Hike at Runyon Canyon", "description": "Embark on an early morning hike at Runyon Canyon offering spectacular views of Los Angeles."}, {"time": "12:00", "title": "Seafood Lunch at Son of a Gun", "description": "Enjoy a seafood-focused menu at Son of a Gun, known for its adventurous dishes."}, {"time": "15:00", "title": "Hollywood Walk of Fame", "description": "Visit the Hollywood Walk of Fame and explore nearby attractions."}]}, {"date": "2025-07-27", "activities": [{"time": "09:00", "title": "Griffith Park and Observatory", "description": "Hike the trails in Griffith Park, then visit the Observatory for more city views."}, {"time": "13:00", "title": "Lunch at Water Grill", "description": "Indulge in a seafood lunch at Water Grill, renowned for its quality and variety."}, {"time": "17:00", "title": "Explore Downtown LA", "description": "Explore the cultural sites and culinary scene of downtown Los Angeles."}]}, {"date": "2025-07-28", "activities": [{"time": "07:00", "title": "Early Morning Hike in Malibu", "description": "Take a scenic hike in the Malibu hills for breathtaking coastal views."}, {"time": "12:00", "title": "Lunch at Nobu Malibu", "description": "Experience high-end seafood dining with ocean views at Nobu Malibu."}, {"time": "15:00", "title": "Malibu Pier", "description": "Relax and enjoy the views and seafood offerings on the Malibu Pier."}]}, {"date": "2025-07-29", "activities": [{"time": "10:00", "title": "Hike to the Hollywood Sign", "description": "Join a guided hike to get up close to the famous Hollywood Sign."}, {"time": "13:00", "title": "Lunch at Blue Plate Oysterette", "description": "Savor the seafood dishes at Blue Plate Oysterette known for its fresh oysters."}, {"time": "16:00", "title": "Visit The Grove", "description": "Shop and dine at The Grove open-air shopping complex."}]}, {"date": "2025-07-30", "activities": [{"time": "08:30", "title": "Hike at Topanga State Park", "description": "Explore the extensive trails and scenery of Topanga State Park."}, {"time": "12:30", "title": "Lunch at Enterprise Fish Co.", "description": "Enjoy a relaxing seafood meal at Enterprise Fish Co. in Santa Monica."}, {"time": "15:00", "title": "Abbot Kinney Boulevard", "description": "Explore the trendy shops and dining spots on Abbot Kinney Boulevard."}]}, {"date": "2025-07-31", "activities": [{"time": "09:00", "title": "Hike at Escondido Falls", "description": "Take a hike to the scenic waterfall in Escondido Canyon in Malibu."}, {"time": "13:00", "title": "Lunch at The Reel Inn", "description": "A casual seafood dining experience at The Reel Inn in Malibu, favored by locals."}, {"time": "16:00", "title": "Relax at Zuma Beach", "description": "Unwind on Zuma Beach, one of Malibu's largest and most popular beaches."}]}, {"date": "2025-08-01", "activities": [{"time": "08:00", "title": "Griffith Observatory Sunrise Hike", "description": "Early morning hike to catch the sunrise at Griffith Observatory."}, {"time": "11:00", "title": "Brunch at Catch LA", "description": "End your trip with a delightful brunch featuring seafood specialties at Catch LA."}, {"time": "14:00", "title": "Explore The Getty Center", "description": "Visit The Getty Center to enjoy art exhibits and stunning views of the city."}]}]}
    return result

tools = [search_tool, search_flights, search_hotels, get_reddit_comments, generate_itinerary] + calendar_tools
def get_tools():
    """
    Returns the list of tools available for the agent.
    """
    return tools

# print(get_reddit_suggestions("https://www.reddit.com/r/TravelHacks/comments/12ppmqx/must_dos_in_cancun/"))