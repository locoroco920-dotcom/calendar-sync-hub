import os.path
import datetime
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    """Reads events from events.csv and adds them to the user's primary Google Calendar."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("Error: credentials.json not found.")
                print("Please create a project in Google Cloud Console, enable the Google Calendar API,")
                print("create OAuth 2.0 Client IDs, download the JSON file, rename it to 'credentials.json',")
                print("and place it in this directory.")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        if not os.path.exists("events.csv"):
            print("events.csv not found.")
            return

        # Read events from CSV
        df = pd.read_csv("events.csv")
        
        print(f"Found {len(df)} events in events.csv. Starting import...")

        for index, row in df.iterrows():
            event_name = row['Event Name']
            start_time_str = row['Date']
            location = row['Location'] if pd.notna(row['Location']) else ""
            link = row['Link'] if pd.notna(row['Link']) else ""
            organization = row['Organization'] if pd.notna(row['Organization']) else ""
            source = row['Source'] if pd.notna(row['Source']) else ""
            
            try:
                # Parse start time
                start_dt = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                # Assume 1 hour duration
                end_dt = start_dt + datetime.timedelta(hours=1)
                
                # Format for Google API
                # Note: We are assuming the times in CSV are local to New York
                start_iso = start_dt.isoformat()
                end_iso = end_dt.isoformat()
                
                description = f"Organization: {organization}\nLink: {link}\nSource: {source}"

                event_body = {
                    'summary': event_name,
                    'location': location,
                    'description': description,
                    'start': {
                        'dateTime': start_iso,
                        'timeZone': 'America/New_York', 
                    },
                    'end': {
                        'dateTime': end_iso,
                        'timeZone': 'America/New_York',
                    },
                }

                # Optional: Check for duplicates (simple check based on time and summary)
                # This is a basic check and might slow down large imports significantly due to API calls.
                # For now, we will just insert. 
                
                print(f"Adding event: {event_name} at {start_time_str}")
                event_result = service.events().insert(calendarId='primary', body=event_body).execute()
                print(f"Event created: {event_result.get('htmlLink')}")
                
            except ValueError as e:
                print(f"Skipping event due to date error: {event_name}. Error: {e}")
            except Exception as e:
                print(f"Error adding event {event_name}: {e}")

        print("Import complete.")

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
