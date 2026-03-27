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
]

def fetch_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
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
            
            # Extract Location
            location = "See Link"
            detail_box = item.find('div', class_='uevents-detailbox')
            if detail_box:
                for div in detail_box.find_all('div'):
                    text = div.get_text(strip=True)
                    if text.startswith("Where:"):
                        location = text.replace("Where:", "").strip()
                        break
            
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
            
            # Location is not in the table, default to generic
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
