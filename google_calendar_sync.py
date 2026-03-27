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

def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def sync_calendar():
    """Reads events from events.csv and adds them to the user's primary Google Calendar."""
    log = []
    def log_msg(msg):
        print(msg)
        log.append(msg)

    creds = get_credentials()
    if not creds:
        log_msg("Error: credentials.json not found. Please setup Google Cloud credentials.")
        return "\n".join(log)

    try:
        service = build("calendar", "v3", credentials=creds)

        if not os.path.exists("events.csv"):
            log_msg("events.csv not found.")
            return "\n".join(log)

        # Read events from CSV
        df = pd.read_csv("events.csv")
        if df.empty:
            log_msg("No events found in CSV.")
            return "\n".join(log)

        log_msg(f"Found {len(df)} events in events.csv. Checking for duplicates...")

        # Get date range to fetch existing events
        df['dt'] = pd.to_datetime(df['Date'])
        min_date = df['dt'].min().isoformat() + 'Z'
        max_date = (df['dt'].max() + datetime.timedelta(days=1)).isoformat() + 'Z'

        # Fetch existing events
        events_result = service.events().list(calendarId='primary', timeMin=min_date,
                                              timeMax=max_date, singleEvents=True,
                                              orderBy='startTime').execute()
        existing_events = events_result.get('items', [])
        
        # Create a set of existing events for fast lookup (summary + start_time)
        existing_set = set()
        for event in existing_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Normalize start time string to compare (remove Z if present, handle offsets)
            # Simple comparison: just use the first 16 chars (YYYY-MM-DDTHH:MM)
            if start:
                key = (event.get('summary'), start[:16])
                existing_set.add(key)

        added_count = 0
        skipped_count = 0

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
                
                start_iso = start_dt.isoformat()
                end_iso = end_dt.isoformat()
                
                # Check duplicate
                # We construct the key same way as above
                check_key = (event_name, start_iso[:16])
                
                if check_key in existing_set:
                    skipped_count += 1
                    continue

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

                service.events().insert(calendarId='primary', body=event_body).execute()
                log_msg(f"Added: {event_name}")
                added_count += 1
                
            except Exception as e:
                log_msg(f"Error adding event {event_name}: {e}")

        log_msg(f"Sync complete. Added {added_count} new events. Skipped {skipped_count} duplicates.")

    except HttpError as error:
        log_msg(f"An error occurred: {error}")
    
    return "\n".join(log)

if __name__ == "__main__":
    sync_calendar()
