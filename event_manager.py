import pandas as pd
import os
from datetime import datetime

DATA_FILE = "events.csv"

def load_events():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Ensure Date is datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading events: {e}")
            return pd.DataFrame(columns=["Event Name", "Date", "Location", "Organization", "Link", "Source"])
    else:
        return pd.DataFrame(columns=["Event Name", "Date", "Location", "Organization", "Link", "Source"])

def save_events(df):
    df.to_csv(DATA_FILE, index=False)

def add_event(event_data):
    df = load_events()
    new_row = pd.DataFrame([event_data])
    df = pd.concat([df, new_row], ignore_index=True)
    # Remove duplicates based on Event Name and Date
    df = df.drop_duplicates(subset=['Event Name', 'Date'], keep='last')
    # Sort by Date
    df = df.sort_values(by='Date')
    save_events(df)

def get_upcoming_events():
    df = load_events()
    if df.empty:
        return df
    today = pd.Timestamp.now().normalize()
    return df[df['Date'] >= today].sort_values(by='Date')
