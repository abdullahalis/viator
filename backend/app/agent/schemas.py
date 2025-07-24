from typing import List, Optional
from pydantic import BaseModel, Field


class EventTime(BaseModel):
    dateTime: str = Field(..., description="time of event in FRC3339 format. Here is an example of Internet date/time format(1985-04-12T23:20:50.52Z)This represents 20 minutes and 50.52 seconds after the 23rd hour of April 12th, 1985 in UTC.")
    timeZone: str = Field(..., description="time zone of event in Formatted as an IANA Time Zone Database name, e.g. 'Europe/Zurich'")
    
class Event(BaseModel):
    summary: str = Field(..., description="name of the event")
    description: str = Field(..., description="OPTIONAL description of the event")
    start: EventTime
    end: EventTime

class Events(BaseModel):
    events: list[Event] = Field(..., description="A list of events")

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

class RedditCommentsParams(BaseModel):
    url: str = Field(..., description="URL of the Reddit page to get comments from. For example, https://www.reddit.com/r/TravelHacks/comments/12ppmqx/must_dos_in_cancun/")

class ItineraryParams(BaseModel):
    location: str = Field(..., description="The destination city or region")
    start_date: str = Field(..., description="Start date of the trip in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date of the trip in YYYY-MM-DD format")
    interests: Optional[List[str]] = Field(default_factory=list, description="Optional list of travel interests (e.g. food, museums, hiking)")