
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from agent.schemas import Event
from datetime import datetime
import os
import json

def google_authenticate():
    """
    Gets credentials to use Google API
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    return creds

def build_event_data(event: Event):
    """
    Parses Event object into json data to be used in API call
    """
    try:
        start_iso_dt = datetime.fromisoformat(event.start.dateTime)
        end_iso_dt = datetime.fromisoformat(event.end.dateTime)

        event_data = {
            "calendarId": "primary",
            "summary": event.summary,
            "start": {
                'dateTime': start_iso_dt.isoformat(),
                'timeZone': event.start.timeZone
            },
            "end": {
                'dateTime': end_iso_dt.isoformat(),
                'timeZone': event.end.timeZone
            }
        }
        if event.description:
            event_data["description"] = event.description

        return event_data
    except Exception as e:
        print("Error parsing event", e)
        return None
    
def extract_event_links(batch_responses):
    """
    Extracts URL links from Google Batch API response
    """
    event_links = []
    
    for request_id, (headers, body_bytes) in batch_responses.items():
        try:
            # Decode bytes to string, then load as JSON
            event_json = json.loads(body_bytes.decode("utf-8"))
            summary = event_json.get("summary")
            html_link = event_json.get("htmlLink")
            
            if summary and html_link:
                event_links.append(f"{summary}: ({html_link})")
        except Exception as e:
            print(f"Failed to parse response for request_id {request_id}: {e}")

    return event_links