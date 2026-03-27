import sys
import io

# Force UTF-8 output for Windows consoles/redirection
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from datetime import datetime, timedelta
import os

DATA_FILE = "events.csv"

def load_events():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading events: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def display_schedule():
    df = load_events()
    if df.empty:
        print("No events found.")
        return

    # Filter for valid dates
    df = df.dropna(subset=['Date'])
    
    # Sort by Date
    df = df.sort_values(by='Date')
    
    # Filter for upcoming events (optional, but usually desired)
    today = pd.Timestamp.now().normalize()
    # If you want to see past events too, comment this out. 
    # But usually "free days" implies future.
    # Let's stick to the full list or maybe start from today?
    # The user said "display which days are not taken", usually implies future planning.
    # Let's filter >= today.
    upcoming_df = df[df['Date'] >= today].copy()
    
    if upcoming_df.empty:
        print("No upcoming events found.")
        return

    print(f"\n{'='*60}")
    print(f"{'UPCOMING EVENTS SCHEDULE':^60}")
    print(f"{'='*60}")
    
    # Group by date to handle multiple events on same day
    events_by_date = upcoming_df.groupby(upcoming_df['Date'].dt.date)
    
    start_date = upcoming_df['Date'].min().date()
    end_date = upcoming_df['Date'].max().date()
    
    # Create a full range of dates
    full_date_range = pd.date_range(start=start_date, end=end_date)
    
    for date_ts in full_date_range:
        current_date = date_ts.date()
        date_str = current_date.strftime("%A, %B %d, %Y")
        
        if current_date in events_by_date.groups:
            # Day has events
            day_events = events_by_date.get_group(current_date)
            print(f"\n[BUSY] {date_str}")
            for _, row in day_events.iterrows():
                # Check if time is exactly midnight (00:00:00) which usually means no time was scraped
                if row['Date'].time() == datetime.min.time():
                    print(f"  - {row['Event Name']} ({row['Organization']})")
                else:
                    time_str = row['Date'].strftime("%I:%M %p")
                    print(f"  - {time_str}: {row['Event Name']} ({row['Organization']})")
        else:
            # Day is free
            print(f"\n[FREE] {date_str}")
            print("  - No events scheduled")

    print(f"\n{'='*60}")

if __name__ == "__main__":
    display_schedule()
