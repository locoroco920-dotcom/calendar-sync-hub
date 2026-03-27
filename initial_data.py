import pandas as pd
from event_manager import save_events

def initialize_data():
    events = [
        {
            "Date": "2026-01-13",
            "Event Name": "The Future of AI: How to Compete and Win",
            "Organization": "NJBIA",
            "Location": "Trenton",
            "Link": "https://njbia.org/events/",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-13",
            "Event Name": "BINJE's Best Awards Reception",
            "Organization": "NJ Chamber",
            "Location": "Heldrich Hotel, New Brunswick",
            "Link": "https://www.njchamber.com/component/content/category/34-events",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-16",
            "Event Name": "Inaugural Leadership Summit",
            "Organization": "NRBP",
            "Location": "Seton Hall Law School, Newark",
            "Link": "https://web.newarkrbp.org/events",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-22",
            "Event Name": "Networking Luncheon",
            "Organization": "MCRCC",
            "Location": "Pines Manor, Edison",
            "Link": "https://www.mcrcc.org/events/",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-22",
            "Event Name": "Happy Hour Mixer",
            "Organization": "Hudson County Chamber",
            "Location": "TBD",
            "Link": "https://business.hudsonchamber.org/chambereventcalendar",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-30",
            "Event Name": "Public Policy Forum 2026",
            "Organization": "NJBIA",
            "Location": "TBD",
            "Link": "https://njbia.org/events/",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-01-30",
            "Event Name": "Real Estate 2026 Forecast and Legislative Update",
            "Organization": "CIANJ",
            "Location": "TBD",
            "Link": "https://members.cianj.org/calendar",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-02-04",
            "Event Name": "Fireside Chat: Future-Proofing Your Business",
            "Organization": "North Jersey Chamber",
            "Location": "William Paterson University",
            "Link": "https://northjerseychamber.org/index.php/events/events-calendar/",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-02-26",
            "Event Name": "Happy Hour Mixer",
            "Organization": "Hudson County Chamber",
            "Location": "TBD",
            "Link": "https://business.hudsonchamber.org/chambereventcalendar",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-03-12",
            "Event Name": "Annual Meeting (11:00 AM – 2:00 PM)",
            "Organization": "Hudson County Chamber",
            "Location": "TBD",
            "Link": "https://business.hudsonchamber.org/chambereventcalendar",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-03-31",
            "Event Name": "ReNew Jersey Business Summit & Expo (Day 1)",
            "Organization": "NJ Chamber",
            "Location": "Harrah’s Atlantic City",
            "Link": "https://www.njchamber.com/component/content/category/34-events",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-04-01",
            "Event Name": "ReNew Jersey Business Summit & Expo (Day 2)",
            "Organization": "NJ Chamber",
            "Location": "Harrah’s Atlantic City",
            "Link": "https://www.njchamber.com/component/content/category/34-events",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-05-19",
            "Event Name": "Community Leaders of Distinction 2026",
            "Organization": "MCRCC",
            "Location": "TBD",
            "Link": "https://www.mcrcc.org/events/",
            "Source": "Manual Entry"
        },
        {
            "Date": "2026-06-11",
            "Event Name": "Challenge Cup Golf Outing",
            "Organization": "NJ Chamber",
            "Location": "TBD",
            "Link": "https://www.njchamber.com/component/content/category/34-events",
            "Source": "Manual Entry"
        }
    ]

    df = pd.DataFrame(events)
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    save_events(df)
    print(f"Initialized {len(df)} events.")

if __name__ == "__main__":
    initialize_data()
