# Meadowlands Chamber - Competitor Event Tracker

This tool helps the Meadowlands Chamber track competitor events to avoid scheduling conflicts.

## Project Structure

- `dashboard.py`: The Streamlit application for visualizing events.
- `event_manager.py`: Handles data loading and saving (CSV).
- `initial_data.py`: Loads the initial list of events provided in the requirements.
- `scraper.py`: A framework for monitoring competitor websites.
- `requirements.txt`: Python dependencies.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Data**:
    Load the initial set of identified 2026 events.
    ```bash
    python initial_data.py
    ```

## Usage

### Running the Dashboard
To view the event calendar and timeline:
```bash
streamlit run dashboard.py
```

### Running the Scraper
To check competitor websites (currently checks connectivity and structure):
```bash
python scraper.py
```

## Data
The event data is stored in `events.csv`. You can manually edit this file or use the `event_manager.py` functions to add new events programmatically.
