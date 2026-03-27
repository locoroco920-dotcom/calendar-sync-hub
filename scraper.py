import requests
from bs4 import BeautifulSoup
import pandas as pd
from event_manager import add_event
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SOURCES = [
    {"org": "NJBIA", "url": "https://njbia.org/events/"},
    {"org": "NJ Chamber", "url": "https://www.njchamber.com/component/content/category/34-events"},
    {"org": "CIANJ", "url": "https://members.cianj.org/calendar/Search?term=&DateFilter=0&from=&to=&CategoryValues=&mode=0"},
    {"org": "Hudson County Chamber", "url": "https://business.hudsonchamber.org/chambereventcalendar"},
    {"org": "NRBP", "url": "https://web.newarkrbp.org/events"},
    {"org": "North Jersey Chamber", "url": "https://northjerseychamber.org/index.php/events/events-calendar/"},
    {"org": "Bergen County Chamber", "url": "https://bergencountychamber.com/events/list/"},
    {"org": "MCRCC", "url": "https://www.mcrcc.org/events/"},
    {"org": "BCRCC", "url": "https://www.bcrcc.com/events"},
    {"org": "CCSNJ", "url": "https://business.chambersnj.com/eventcalendar"},
    {"org": "NJSBDC", "url": "https://clients.njsbdc.com/events.aspx"},
    {"org": "BNI New Jersey", "url": "https://bninewjersey.com/en-US/events"},
    {"org": "AACCNJ", "url": "https://www.aaccnj.com/calendar-of-events"},
    {"org": "SHCCNJ", "url": "https://business.shccnj.org/events"},
    {"org": "Fort Lee Regional Chamber", "url": "https://www.fortleechamber.com/events"},
    {"org": "Greater Paterson Chamber", "url": "https://cca.greaterpatersoncc.org/EvtListingMainSearch.aspx?class=B"},
    {"org": "Morris County Chamber", "url": "https://api-internal.weblinkconnect.com/api/Events?UpcomingEventsOnly=true&PageNumber=0&PageSize=200"},
    {"org": "NJEDA", "url": "https://www.njeda.gov/events/"},
    {"org": "Choose New Jersey", "url": "https://choosenj.com/wp-json/wp/v2/event?per_page=50"},
]

def fetch_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        # Special handling for WeblinkConnect API (Morris County Chamber)
        if 'api-internal.weblinkconnect.com' in url:
            headers['Accept'] = 'application/json'
            headers['x-tenant-hostname'] = 'web.morrischamber.org'
            headers['Origin'] = 'https://web.morrischamber.org'
            headers['Referer'] = 'https://web.morrischamber.org/atlas/calendar'
        timeout = 30 if 'api-internal.weblinkconnect.com' in url else 10
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None

def parse_time_string(time_str):
    """Parse a time string like '5 p.m.', '9:30 a.m.', 'noon', '12:00 Noon', '8:30 AM' into (hour, minute) or None."""
    if not time_str:
        return None
    time_str = time_str.strip().lower()
    if time_str in ('noon', '12 noon'):
        return (12, 0)
    if time_str == 'midnight':
        return (0, 0)
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?|noon)', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).replace('.', '').strip()
        if period == 'noon':
            return (12, minute)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return (hour, minute)
    return None

def get_njbia_time(url):
    try:
        html = fetch_page(url)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        # <span class='detail__time'> ... <span class="text"> 12:00 pm ...
        time_span = soup.find('span', class_='detail__time')
        if time_span:
            text_span = time_span.find('span', class_='text')
            if text_span:
                time_text = text_span.get_text(strip=True)
                # Extract "12:00 pm" from "12:00 pm - 1:00 pm"
                match = re.search(r'(\d{1,2}:\d{2}\s*[ap]m)', time_text, re.IGNORECASE)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        logging.error(f"Error fetching time for {url}: {e}")
        return None

def parse_njbia(html, org, url):
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0
    
    # Find all event rows
    rows = soup.find_all('div', class_='events-table-row')
    
    for row in rows:
        try:
            # Extract Title and Link
            title_div = row.find('div', class_='event-title')
            if not title_div:
                continue
            link_tag = title_div.find('a')
            if not link_tag:
                continue
            
            title = link_tag.get_text(strip=True)
            link = link_tag['href']
            
            # Extract Date
            date_div = row.find('div', class_='event-date')
            date_str = date_div.get_text(strip=True) if date_div else ""
            
            # Extract Type/Location
            type_div = row.find('div', class_='event-type')
            event_type = type_div.get_text(strip=True) if type_div else "See Link"
            
            # Parse Date
            try:
                date_obj = pd.to_datetime(date_str)
                
                # Fetch time from detail page
                if link:
                    event_time = get_njbia_time(link)
                    if event_time:
                        full_date_str = f"{date_obj.strftime('%Y-%m-%d')} {event_time}"
                        try:
                            date_obj = pd.to_datetime(full_date_str)
                        except:
                            logging.warning(f"Could not parse combined date/time: {full_date_str}")
            except:
                logging.warning(f"Could not parse date: {date_str}")
                continue

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": event_type,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1
            
        except Exception as e:
            logging.error(f"Error parsing row: {e}")
            continue
            
    logging.info(f"Found {events_found} events for {org}")

def parse_nj_chamber(html, org, url):
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0
    
    # Find all event items
    items = soup.find_all('div', class_='g-array-item-text')
    
    # Default year logic - assuming upcoming events are 2026 based on user context
    # In a robust system, we'd check the current date and infer the year.
    default_year = 2026 

    for item in items:
        try:
            # Extract Date
            date_div = item.find('div', class_='uevents-date')
            if not date_div:
                continue
            date_text = date_div.get_text(strip=True)
            
            # Handle date ranges like "March 31 & April 1"
            clean_date_text = date_text.split('&')[0].strip()
            
            # Try to parse date
            try:
                full_date_str = f"{clean_date_text} {default_year}"
                full_date_str = full_date_str.replace('.', '')
                date_obj = datetime.strptime(full_date_str, "%b %d %Y")
            except ValueError:
                try:
                     date_obj = datetime.strptime(full_date_str, "%B %d %Y")
                except:
                    logging.warning(f"Could not parse date: {full_date_str}")
                    continue

            # Extract Title
            title_div = item.find('div', class_='uevents-title')
            title = title_div.get_text(strip=True) if title_div else "No Title"
            
            # Extract Location and Time from detailbox
            location = "See Link"
            detail_box = item.find('div', class_='uevents-detailbox')
            if detail_box:
                for div in detail_box.find_all('div'):
                    text = div.get_text(strip=True)
                    if text.startswith("Where:"):
                        location = text.replace("Where:", "").strip()
                    elif text.startswith("When:"):
                        when_text = text.replace("When:", "").strip()
                        time_parts = parse_time_string(when_text)
                        if time_parts:
                            date_obj = date_obj.replace(hour=time_parts[0], minute=time_parts[1])
            
            # Extract Link
            link = url # Default
            button_box = item.find('div', class_='uevents-buttonbox')
            if button_box:
                a_tag = button_box.find('a')
                if a_tag and a_tag.has_attr('href'):
                    href = a_tag['href']
                    if href.startswith('/'):
                        link = f"https://www.njchamber.com{href}"
                    else:
                        link = href

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1
            
        except Exception as e:
            logging.error(f"Error parsing item: {e}")
            continue
            
    logging.info(f"Found {events_found} events for {org}")

def parse_cianj(html, org, url):
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0
    
    # Find all event cards
    cards = soup.find_all('div', class_='gz-events-card')
    
    for card in cards:
        try:
            # Extract Title and Link
            title_tag = card.find('a', class_='gz-event-card-title')
            if not title_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            link = title_tag['href']
            if link.startswith('/'):
                link = f"https://members.cianj.org{link}"
            
            # Extract Date from meta tag
            start_date_meta = card.find('meta', itemprop='startDate')
            if start_date_meta:
                date_str = start_date_meta['content']
                try:
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                except ValueError:
                    logging.warning(f"Could not parse date: {date_str}")
                    continue
            else:
                continue

            # Extract Location
            location = "See Link"
            
            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1
            
        except Exception as e:
            logging.error(f"Error parsing card: {e}")
            continue
            
    logging.info(f"Found {events_found} events for {org}")

def parse_hudson_chamber(html, org, url):
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0
    
    # Find all event cards
    cards = soup.find_all('div', class_='gz-events-card')
    
    for card in cards:
        try:
            # Extract Title and Link
            title_tag = card.find('a', class_='gz-event-card-title')
            if not title_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href', '')
            
            # Extract Date from meta tag
            start_date_meta = card.find('meta', itemprop='startDate')
            if start_date_meta:
                date_str = start_date_meta['content']
                try:
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                except ValueError:
                    logging.warning(f"Could not parse date: {date_str}")
                    continue
            else:
                continue

            # Extract Location
            location = "Hudson County Chamber" # Default as not found in card
            
            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1
            
        except Exception as e:
            logging.error(f"Error parsing card: {e}")
            continue
            
    logging.info(f"Found {events_found} events for {org}")

def parse_nrbp(html, org, url):
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0
    
    # Find the table
    table = soup.find('table', class_='EventListBody')
    if not table:
        logging.warning(f"Event table not found for {org}")
        return
        
    rows = table.find_all('tr')
    
    for row in rows:
        # Skip header row
        if 'EventListHeader' in row.get('class', []):
            continue
            
        cols = row.find_all('td')
        if len(cols) < 3:
            continue
            
        try:
            # Date
            date_span = cols[0].find('span')
            date_str = date_span.get_text(strip=True) if date_span else cols[0].get_text(strip=True)
            
            # Title and Link
            link_tag = cols[2].find('a')
            if not link_tag:
                continue
                
            title = link_tag.get_text(strip=True)
            link = link_tag.get('href', '')
            if link.startswith('/'):
                link = f"https://web.newarkrbp.org{link}"
                
            # Parse Date
            try:
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            except ValueError:
                logging.warning(f"Could not parse date: {date_str}")
                continue
            
            # Fetch detail page for event time
            location = "See Link"
            try:
                detail_html = fetch_page(link)
                if detail_html:
                    # Time is in JSON data: "EventTime":"12:00 Noon"
                    time_match = re.search(r'"EventTime"\s*:\s*"(\d{1,2}:\d{2}\s*(?:Noon|[AP]M))"', detail_html, re.IGNORECASE)
                    if time_match:
                        t_str = time_match.group(1).replace('Noon', 'PM')
                        time_parts = parse_time_string(t_str)
                        if time_parts:
                            date_obj = date_obj.replace(hour=time_parts[0], minute=time_parts[1])
                    # Try to extract location from JSON data
                    loc_match = re.search(r'"LocationName"\s*:\s*"([^"]+)"', detail_html)
                    if loc_match:
                        location = loc_match.group(1)
            except Exception as e:
                logging.warning(f"Could not fetch NRBP detail page for time: {e}")

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1
            
        except Exception as e:
            logging.error(f"Error parsing row: {e}")
            continue
            
    logging.info(f"Found {events_found} events for {org}")

def parse_north_jersey_chamber(html, org, url):
    # The HTML contains widgets, but the main calendar is dynamic.
    # We use the MembershipWorks API to fetch the full list.
    import time
    import json
    
    events_found = 0
    
    # API Endpoint
    # Use a timestamp for the past to ensure we get current events
    timestamp = int(time.time())
    api_url = f"https://api.membershipworks.com/v2/events?org=19335&sdp={timestamp}"
    
    try:
        logging.info(f"Fetching API: {api_url}")
        response = requests.get(api_url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Origin': 'https://northjerseychamber.org',
            'Referer': 'https://northjerseychamber.org/'
        })
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('evt', [])
            
            for item in items:
                try:
                    title = item.get('ttl', 'No Title')
                    date_str = item.get('szp', '') # e.g. "Thu Jan 15 2026, 4:00pm EST"
                    partial_url = item.get('url', '')
                    location = item.get('adn', 'See Link')
                    
                    link = f"https://northjerseychamber.org/index.php/events/events-calendar/#!event/{partial_url}"
                    
                    # Date parsing
                    start_date = None
                    if date_str:
                        # Remove timezone if present (EST/EDT)
                        date_str_clean = re.sub(r'\s+[A-Z]{3}$', '', date_str)
                        try:
                            start_date = datetime.strptime(date_str_clean, '%a %b %d %Y, %I:%M%p')
                        except ValueError:
                            logging.warning(f"Failed to parse date: {date_str}")
                            continue
                    
                    if start_date:
                        data = {
                            "Event Name": title,
                            "Date": start_date,
                            "Organization": org,
                            "Location": location,
                            "Link": link,
                            "Source": "Scraper"
                        }
                        add_event(data)
                        events_found += 1
                except Exception as e:
                    logging.error(f"Error parsing API item: {e}")
                    continue
        else:
            logging.error(f"API request failed: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Error fetching API: {e}")

    logging.info(f"Found {events_found} events for {org} via API")

def parse_bergen_county_chamber(html, org, url):
    """Parse Bergen County Chamber events (WordPress The Events Calendar plugin)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    articles = soup.find_all('article', class_='tribe-events-calendar-list__event')

    for article in articles:
        try:
            # Title and Link
            title_tag = article.find('a', class_='tribe-events-calendar-list__event-title-link')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href', url)

            # Date from <time datetime="...">
            time_tag = article.find('time')
            if not time_tag:
                continue
            date_attr = time_tag.get('datetime', '')
            date_text = time_tag.get_text(strip=True)

            # Parse date - datetime attr is like "2026-04-09"
            try:
                date_obj = datetime.strptime(date_attr, "%Y-%m-%d")
                # Try to extract time from text like "April 9 @ 12:00 pm-2:00 pm"
                time_match = re.search(r'@\s*(\d{1,2}:\d{2}\s*[ap]m)', date_text, re.IGNORECASE)
                if time_match:
                    full_str = f"{date_attr} {time_match.group(1)}"
                    try:
                        date_obj = datetime.strptime(full_str, "%Y-%m-%d %I:%M %p")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(full_str, "%Y-%m-%d %I:%M%p")
                        except ValueError:
                            pass
            except ValueError:
                logging.warning(f"Could not parse date: {date_attr}")
                continue

            # Location
            venue = article.find('span', class_='tribe-events-calendar-list__event-venue-title')
            location = venue.get_text(strip=True) if venue else "See Link"

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing Bergen County event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_mcrcc(html, org, url):
    """Parse MCRCC events (WordPress The Events Calendar plugin)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    articles = soup.find_all('article', class_='tribe-events-calendar-list__event')

    for article in articles:
        try:
            title_tag = article.find('a', class_='tribe-events-calendar-list__event-title-link')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href', url)

            time_tag = article.find('time')
            if not time_tag:
                continue
            date_attr = time_tag.get('datetime', '')
            date_text = time_tag.get_text(strip=True)

            try:
                date_obj = datetime.strptime(date_attr, "%Y-%m-%d")
                time_match = re.search(r'@\s*(\d{1,2}:\d{2}\s*[ap]m)', date_text, re.IGNORECASE)
                if time_match:
                    full_str = f"{date_attr} {time_match.group(1)}"
                    try:
                        date_obj = datetime.strptime(full_str, "%Y-%m-%d %I:%M %p")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(full_str, "%Y-%m-%d %I:%M%p")
                        except ValueError:
                            pass
            except ValueError:
                logging.warning(f"Could not parse date: {date_attr}")
                continue

            venue = article.find('span', class_='tribe-events-calendar-list__event-venue-title')
            location = venue.get_text(strip=True) if venue else "See Link"

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing MCRCC event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_bcrcc(html, org, url):
    """Parse BCRCC events (Glue Up platform)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    # Find all glueup event links, grouped by href (each event has image link + title link)
    from collections import OrderedDict
    seen_hrefs = OrderedDict()
    all_links = soup.find_all('a', href=lambda h: h and 'glueup.com/event' in h)
    for link_tag in all_links:
        href = link_tag['href']
        text = link_tag.get_text(strip=True)
        # Skip thumbnail-only links
        if text and not text.startswith('thumbnails') and href not in seen_hrefs:
            seen_hrefs[href] = text

    # Find date strings near events - they appear as text nodes like "08 Apr 2026 | 11:00 AM - 01:30 PM"
    # Also find location strings
    region = soup.find('div', class_='region-content')
    if not region:
        logging.warning(f"Could not find content region for {org}")
        return

    # Find all row divs that contain event info
    rows = region.find_all('div', class_='row')
    for row in rows:
        try:
            event_link = row.find('a', href=lambda h: h and 'glueup.com/event' in h)
            if not event_link:
                continue

            href = event_link['href']

            # Get title - find the non-thumbnail link text
            title = None
            for a in row.find_all('a', href=href):
                text = a.get_text(strip=True)
                if text and not text.startswith('thumbnails'):
                    # Clean up duplicated text like "Learn Before LunchLearn Before Lunch..."
                    # Remove "(opens in a new window)" suffix
                    text = re.sub(r'\s*\(opens in a new window\)\s*$', '', text)
                    # If text is duplicated, take the first half
                    half = len(text) // 2
                    if half > 3 and text[:half] == text[half:half*2]:
                        text = text[:half]
                    title = text.strip()
                    break
            if not title:
                continue

            # Find date text in the row
            row_text = row.get_text(' ', strip=True)
            date_match = re.search(r'(\d{2}\s+\w{3}\s+\d{4})\s*\|\s*(\d{1,2}:\d{2}\s*[AP]M)', row_text)
            if not date_match:
                continue

            date_str = date_match.group(1)
            time_str = date_match.group(2)

            try:
                date_obj = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %I:%M %p")
            except ValueError:
                try:
                    date_obj = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %I:%M%p")
                except ValueError:
                    logging.warning(f"Could not parse date: {date_str} {time_str}")
                    continue

            # Extract location from row text (between time range and title)
            loc_match = re.search(r'\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M\s+(.*?)(?=' + re.escape(title[:20]) + ')', row_text)
            location = loc_match.group(1).strip() if loc_match else "See Link"

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": href,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing BCRCC event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_ccsnj(html, org, url):
    """Parse CCSNJ events (GrowthZone platform, same as CIANJ/Hudson)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    cards = soup.find_all('div', class_='gz-events-card')

    for card in cards:
        try:
            title_tag = card.find('a', class_='gz-event-card-title')
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag['href']

            # Date from meta tag
            start_date_meta = card.find('meta', itemprop='startDate')
            if start_date_meta:
                date_str = start_date_meta['content']
                try:
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                except ValueError:
                    logging.warning(f"Could not parse date: {date_str}")
                    continue
            else:
                continue

            location = "See Link"

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing CCSNJ event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_njsbdc(html, org, url):
    """Parse NJSBDC events/workshops."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    blocks = soup.find_all('div', class_='cdeventlistmainblock')

    for block in blocks:
        try:
            # Title and Link
            title_div = block.find('div', class_='cdeventtitle')
            if not title_div:
                continue
            link_tag = title_div.find('a')
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag.get('href', '')
            if href and not href.startswith('http'):
                link = f"https://clients.njsbdc.com/{href}"
            else:
                link = href

            # Date/Time
            time_div = block.find('div', class_='cdeventtime')
            if not time_div:
                continue
            time_text = time_div.get_text(strip=True)

            # Parse "Mon, Mar 30 1:00 PM to 2:00 PM" or "Sat, Apr 4 9:00 AM to 2:00 PM"
            date_match = re.search(r'(\w{3}),\s*(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*[AP]M)', time_text)
            if not date_match:
                # Try without day-of-week
                date_match = re.search(r'(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*[AP]M)', time_text)
                if date_match:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    time_part = date_match.group(3)
                else:
                    continue
            else:
                month = date_match.group(2)
                day = date_match.group(3)
                time_part = date_match.group(4)

            # Assume current year context (2026)
            year = datetime.now().year
            try:
                date_obj = datetime.strptime(f"{month} {day} {year} {time_part}", "%b %d %Y %I:%M %p")
            except ValueError:
                try:
                    date_obj = datetime.strptime(f"{month} {day} {year} {time_part}", "%b %d %Y %I:%M%p")
                except ValueError:
                    logging.warning(f"Could not parse date: {month} {day} {year} {time_part}")
                    continue

            # Location
            loc_div = block.find('div', class_='cdeventlocation')
            location = loc_div.get_text(strip=True) if loc_div else "See Link"
            # Clean up location text
            location = re.sub(r'\s+', ' ', location).strip()
            if len(location) > 100:
                location = location[:100]

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing NJSBDC event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_bni(html, org, url):
    """Parse BNI New Jersey events."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    # BNI event calendar is mostly JavaScript-rendered; try to find any static event links
    event_links = soup.find_all('a', href=lambda h: h and '/event' in h.lower() if h else False)
    for link_tag in event_links:
        try:
            title = link_tag.get_text(strip=True)
            if not title:
                continue
            link = link_tag.get('href', '')
            if link and not link.startswith('http'):
                link = f"https://bninewjersey.com{link}"

            # Try to find date near event
            parent = link_tag.parent
            date_text = parent.get_text(strip=True) if parent else ''
            date_match = re.search(r'(\w+ \d{1,2},?\s*\d{4})', date_text)
            if date_match:
                try:
                    date_obj = datetime.strptime(date_match.group(1).replace(',', ''), "%B %d %Y")
                except ValueError:
                    continue
            else:
                continue

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": "See Link",
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing BNI event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_aaccnj(html, org, url):
    """Parse AACCNJ events (static HTML with caption-text divs)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    caption_divs = soup.find_all('div', class_='caption-text')
    for div in caption_divs:
        try:
            paragraphs = div.find_all('p', class_='rteBlock')
            if len(paragraphs) < 2:
                continue

            title = paragraphs[0].get_text(strip=True)
            date_text = paragraphs[1].get_text(strip=True)

            if not title or not date_text:
                continue

            # Parse date like "April 16, 2026"
            try:
                date_obj = datetime.strptime(date_text, "%B %d, %Y")
            except ValueError:
                logging.warning(f"Could not parse AACCNJ date: {date_text}")
                continue

            # Try to find a link
            link_tag = div.find('a', href=True)
            link = link_tag['href'] if link_tag else url
            if link and not link.startswith('http'):
                link = f"https://www.aaccnj.com{link}"

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": "See Link",
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing AACCNJ event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_growthzone_cards(html, org, url):
    """Shared parser for GrowthZone sites that use card layout with span content datetime
    (SHCCNJ, Fort Lee Regional Chamber)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    cards = soup.find_all('div', class_='gz-events-card')
    for card in cards:
        try:
            # Title from h5.gz-card-title > a
            title_h5 = card.find('h5', class_='gz-card-title')
            if not title_h5:
                continue
            link_tag = title_h5.find('a')
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            link = link_tag.get('href', url)

            # Date from span with content attribute like "2026-02-04T12:00"
            date_span = card.find('span', attrs={'content': True})
            if not date_span:
                continue

            date_str = date_span['content']
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except ValueError:
                    logging.warning(f"Could not parse GrowthZone date: {date_str}")
                    continue

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": "See Link",
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing {org} event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_shccnj(html, org, url):
    """Parse SHCCNJ events (GrowthZone card layout)."""
    parse_growthzone_cards(html, org, url)

def parse_fort_lee(html, org, url):
    """Parse Fort Lee Regional Chamber events (GrowthZone card layout)."""
    parse_growthzone_cards(html, org, url)

def parse_greater_paterson(html, org, url):
    """Parse Greater Paterson Chamber events (CC-Assist calendar grid)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    # Find the month header text like "March, 2026"
    month_text = None
    for span in soup.find_all('span'):
        text = span.get_text(strip=True)
        match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December),?\s*(\d{4})$', text)
        if match:
            month_text = text
            break

    if not month_text:
        logging.warning(f"Could not find month header for {org}")
        return

    month_match = re.match(r'(\w+),?\s*(\d{4})', month_text)
    month_name = month_match.group(1)
    year = int(month_match.group(2))

    # Find day cells that contain events
    day_divs = soup.find_all('div', class_='ccaDay')
    for day_div in day_divs:
        try:
            # Get day number from span.ccaLabel
            label = day_div.find('span', class_='ccaLabel')
            if not label:
                continue
            day_num = label.get_text(strip=True)
            if not day_num.isdigit():
                continue

            # Find event links within this day
            event_infos = day_div.find_all('div', class_='ccaEvtInfo')
            for info in event_infos:
                name_div = info.find('div', class_='ccaEvtName')
                if not name_div:
                    continue
                link_tag = name_div.find('a', href=True)
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                href = link_tag['href']
                if not href.startswith('http'):
                    href = f"https://cca.greaterpatersoncc.org/{href}"

                # Extract time from cell text (e.g. "8:30 AM", "6:00 PM")
                info_text = info.get_text(strip=True)
                time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)', info_text, re.IGNORECASE)

                try:
                    date_obj = datetime.strptime(f"{month_name} {day_num} {year}", "%B %d %Y")
                    if time_match:
                        time_parts = parse_time_string(time_match.group(1))
                        if time_parts:
                            date_obj = date_obj.replace(hour=time_parts[0], minute=time_parts[1])
                except ValueError:
                    continue

                data = {
                    "Event Name": title,
                    "Date": date_obj,
                    "Organization": org,
                    "Location": "See Link",
                    "Link": href,
                    "Source": "Scraper"
                }
                add_event(data)
                events_found += 1

        except Exception as e:
            logging.error(f"Error parsing Greater Paterson event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_morris_county(html, org, url):
    """Parse Morris County Chamber events via WeblinkConnect API."""
    import json

    events_found = 0

    try:
        data = json.loads(html)
    except (json.JSONDecodeError, TypeError):
        logging.warning(f"Morris County API response is not valid JSON")
        return

    results = data.get('Result', [])
    for item in results:
        try:
            title = item.get('EventName', '').strip()
            if not title:
                continue

            # Parse date from StartDate like "2026-03-27T12:00:00Z"
            start_date_str = item.get('StartDate', '')
            if not start_date_str:
                continue

            try:
                date_obj = datetime.strptime(start_date_str[:19], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    date_obj = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
                except ValueError:
                    logging.warning(f"Could not parse Morris County date: {start_date_str}")
                    continue

            # Build location from address fields
            location_parts = []
            for field in ['Location', 'Address1', 'City', 'State']:
                val = item.get(field, '')
                if val and val.strip():
                    location_parts.append(val.strip())
            location = ', '.join(location_parts) if location_parts else 'See Link'
            if len(location) > 100:
                location = location[:100]

            # Link to event detail page
            event_id = item.get('EventId', '')
            special_url = item.get('SpecialDetailsPageURL', '')
            if special_url:
                link = special_url
            elif event_id:
                link = f"https://web.morrischamber.org/atlas/Events/{event_id}"
            else:
                link = url

            event_data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": location,
                "Link": link,
                "Source": "Scraper"
            }
            add_event(event_data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing Morris County event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_njeda(html, org, url):
    """Parse NJEDA events (custom WordPress with div.event cards)."""
    soup = BeautifulSoup(html, 'html.parser')
    events_found = 0

    event_divs = soup.find_all('div', class_='event')
    for ev in event_divs:
        try:
            h4s = ev.find_all('h4')
            if len(h4s) < 2:
                continue

            date_text = h4s[0].get_text(strip=True)
            title = h4s[1].get_text(strip=True)

            if not title or not date_text:
                continue

            # Parse "February 25, 2026"
            try:
                date_obj = datetime.strptime(date_text, "%B %d, %Y")
            except ValueError:
                logging.warning(f"Could not parse NJEDA date: {date_text}")
                continue

            # Get time from bg-green div
            time_div = ev.find('div', class_=lambda c: c and 'bg-green-100' in c if c else False)
            if time_div:
                time_text = time_div.get_text(strip=True)
                time_match = re.search(r'(\d{1,2}:\d{2}\s*[ap]m)', time_text, re.IGNORECASE)
                if time_match:
                    try:
                        combined = f"{date_text} {time_match.group(1)}"
                        date_obj = datetime.strptime(combined, "%B %d, %Y %I:%M %p")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(combined, "%B %d, %Y %I:%M%p")
                        except ValueError:
                            pass

            link_tag = ev.find('a', href=True)
            link = link_tag['href'] if link_tag else url

            data = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": "See Link",
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing NJEDA event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_choose_nj(html, org, url):
    """Parse Choose New Jersey events via WP REST API."""
    import json

    events_found = 0

    try:
        data = json.loads(html)
    except (json.JSONDecodeError, TypeError):
        logging.warning(f"Choose NJ API response is not valid JSON")
        return

    for item in data:
        try:
            title = item.get('title', {}).get('rendered', '').strip()
            if not title:
                continue

            link = item.get('link', url)

            # Try to get event date from excerpt
            excerpt_html = item.get('excerpt', {}).get('rendered', '')
            excerpt_text = BeautifulSoup(excerpt_html, 'html.parser').get_text()

            # Look for date patterns like "May 3-6" or "September 22-26" or "June 22 to June 25"
            date_obj = None
            date_match = re.search(
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
                excerpt_text
            )
            if date_match:
                month = date_match.group(1)
                day = date_match.group(2)
                # Infer year from title or default to upcoming year
                year_match = re.search(r'(\d{4})', title)
                year = int(year_match.group(1)) if year_match else datetime.now().year
                try:
                    date_obj = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

            if not date_obj:
                continue

            data_dict = {
                "Event Name": title,
                "Date": date_obj,
                "Organization": org,
                "Location": "See Link",
                "Link": link,
                "Source": "Scraper"
            }
            add_event(data_dict)
            events_found += 1

        except Exception as e:
            logging.error(f"Error parsing Choose NJ event: {e}")
            continue

    logging.info(f"Found {events_found} events for {org}")

def parse_generic(html, org, url):
    """
    A generic parser placeholder. 
    """
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    logging.info(f"Successfully accessed {org} ({title}) - No specific parser implemented yet.")
    return []

# Map org names to their parser functions
PARSERS = {
    "NJBIA": parse_njbia,
    "NJ Chamber": parse_nj_chamber,
    "CIANJ": parse_cianj,
    "Hudson County Chamber": parse_hudson_chamber,
    "NRBP": parse_nrbp,
    "North Jersey Chamber": parse_north_jersey_chamber,
    "Bergen County Chamber": parse_bergen_county_chamber,
    "MCRCC": parse_mcrcc,
    "BCRCC": parse_bcrcc,
    "CCSNJ": parse_ccsnj,
    "NJSBDC": parse_njsbdc,
    "BNI New Jersey": parse_bni,
    "AACCNJ": parse_aaccnj,
    "SHCCNJ": parse_shccnj,
    "Fort Lee Regional Chamber": parse_fort_lee,
    "Greater Paterson Chamber": parse_greater_paterson,
    "Morris County Chamber": parse_morris_county,
    "NJEDA": parse_njeda,
    "Choose New Jersey": parse_choose_nj,
}

def run_scraper():
    logging.info("Starting scraper run...")
    # Deduplicate sources by org name
    seen_orgs = set()
    for source in SOURCES:
        org = source['org']
        if org in seen_orgs:
            logging.warning(f"Skipping duplicate source: {org}")
            continue
        seen_orgs.add(org)

        logging.info(f"Checking {org}...")
        html = fetch_page(source['url'])
        if html:
            parser = PARSERS.get(org, parse_generic)
            parser(html, org, source['url'])
    logging.info("Scraper run complete.")

if __name__ == "__main__":
    run_scraper()
