import streamlit as st
import pandas as pd
from event_manager import get_upcoming_events
import plotly.express as px
from google_calendar_sync import sync_calendar
from create_ics import generate_ics_file

st.set_page_config(page_title="Meadowlands Event Tracker", layout="wide")

st.title("Meadowlands Chamber - Competitor Event Tracker")
st.markdown("Track upcoming events to avoid scheduling conflicts.")

# Sidebar Actions
st.sidebar.header("Actions")

# Google Calendar Sync
if st.sidebar.button("Sync to Google Calendar"):
    with st.spinner("Syncing events to Google Calendar..."):
        log_output = sync_calendar()
        st.sidebar.text_area("Sync Log", log_output, height=200)

# ICS Download
st.sidebar.markdown("---")
if st.sidebar.button("Generate Calendar File (.ics)"):
    ics_path = generate_ics_file()
    if ics_path:
        with open(ics_path, "rb") as f:
            st.sidebar.download_button(
                label="Download .ics File",
                data=f,
                file_name="meadowlands_events.ics",
                mime="text/calendar"
            )
        st.sidebar.success("File generated! Click above to download.")
    else:
        st.sidebar.error("Could not generate file.")

# Load Data
df = get_upcoming_events()

if df.empty:
    st.warning("No upcoming events found. Please run the scraper or load initial data.")
else:
    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # Organization Filter
    orgs = ["All"] + sorted(df['Organization'].unique().tolist())
    selected_org = st.sidebar.selectbox("Select Organization", orgs)
    
    # Date Range Filter
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Apply Filters
    filtered_df = df.copy()
    if selected_org != "All":
        filtered_df = filtered_df[filtered_df['Organization'] == selected_org]
    
    filtered_df = filtered_df[
        (filtered_df['Date'].dt.date >= start_date) & 
        (filtered_df['Date'].dt.date <= end_date)
    ]

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Events", len(filtered_df))
    col2.metric("Organizations Tracking", filtered_df['Organization'].nunique())

    # Timeline View
    st.subheader("Event Timeline")
    if not filtered_df.empty:
        fig = px.timeline(
            filtered_df, 
            x_start="Date", 
            x_end="Date", 
            y="Organization", 
            color="Organization",
            hover_data=["Event Name", "Location"],
            title="Upcoming Events Timeline"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    # Data Table
    st.subheader("Detailed Event List")
    
    # Format date for display
    display_df = filtered_df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df[["Date", "Event Name", "Organization", "Location", "Link"]],
        use_container_width=True,
        column_config={
            "Link": st.column_config.LinkColumn("Event Link")
        }
    )

    # Recurring Conflicts Section
    st.subheader("Recurring Conflicts to Note")
    st.markdown("""
    - **BNI Chapters**: Tuesdays at 7:00 AM & 9:00 AM (Weekly)
    - **North Jersey Chamber**: Business Growth Roundtable (2nd/3rd Friday, 9:30 AM)
    - **Hudson County Chamber**: The Breakfast Club (Monthly, 3rd Friday, 8:00 AM)
    """)
