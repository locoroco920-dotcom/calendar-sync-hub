import pandas as pd
from icalendar import Calendar, Event, vText
import datetime
import os

def generate_ics_file(output_file="public/events.ics"):
    """Reads events.csv and generates an ICS file for calendar import."""
    
    # Ensure public directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if not os.path.exists("events.csv"):
        return None

    df = pd.read_csv("events.csv")
    
    cal = Calendar()
    cal.add('prodid', '-//Meadowlands Event Tracker//mxm.dk//')
    cal.add('version', '2.0')

    for index, row in df.iterrows():
        event = Event()
        
        event_name = row['Event Name']
        start_time_str = row['Date']
        end_time_str = row.get('End Date', None)
        location = row['Location'] if pd.notna(row['Location']) else ""
        link = row['Link'] if pd.notna(row['Link']) else ""
        organization = row['Organization'] if pd.notna(row['Organization']) else ""
        
        try:
            start_dt = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")

            # Use actual end time if available, otherwise set end = start (no fake duration)
            if pd.notna(end_time_str) and str(end_time_str).strip():
                try:
                    end_dt = datetime.datetime.strptime(str(end_time_str), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    end_dt = start_dt
            else:
                end_dt = start_dt
            
            event.add('summary', event_name)
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('dtstamp', datetime.datetime.now())
            
            description = f"Organization: {organization}\nLink: {link}"
            event.add('description', description)
            
            if location:
                event.add('location', location)
            
            # Create a unique ID for the event to avoid duplicates on re-import
            # Using a simple hash of name and time
            uid = f"{start_time_str}-{event_name}".replace(" ", "_").replace(":", "").replace("@", "") + "@meadowlands_tracker"
            event.add('uid', uid)

            cal.add_component(event)
            
        except ValueError:
            continue

    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    return output_file

if __name__ == "__main__":
    generate_ics_file()
    print("ICS file generated: public/events.ics")
