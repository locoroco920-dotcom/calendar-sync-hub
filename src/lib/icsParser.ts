import ICAL from 'ical.js';

export interface CalendarEvent {
  id: string;
  summary: string;
  description: string;
  location: string;
  start: Date;
  end: Date;
  url?: string;
  organization?: string;
}

export async function fetchAndParseICS(url: string): Promise<CalendarEvent[]> {
  const response = await fetch(url);
  const icsData = await response.text();
  return parseICS(icsData);
}

export function parseICS(icsData: string): CalendarEvent[] {
  const jcalData = ICAL.parse(icsData);
  const vcalendar = new ICAL.Component(jcalData);
  const vevents = vcalendar.getAllSubcomponents('vevent');

  return vevents.map((vevent) => {
    const event = new ICAL.Event(vevent);
    const descriptionValue = vevent.getFirstPropertyValue('description');
    const description = typeof descriptionValue === 'string' ? descriptionValue : '';
    
    // Extract URL and organization from description if present
    const urlMatch = description.match(/Link:\s*(https?:\/\/[^\s]+)/);
    const orgMatch = description.match(/Organization:\s*([^\n]+)/);
    
    return {
      id: event.uid,
      summary: event.summary || 'Untitled Event',
      description: description,
      location: event.location || '',
      start: event.startDate.toJSDate(),
      end: event.endDate.toJSDate(),
      url: urlMatch ? urlMatch[1] : undefined,
      organization: orgMatch ? orgMatch[1].trim() : undefined,
    };
  });
}

export function getEventsForDate(events: CalendarEvent[], date: Date): CalendarEvent[] {
  return events.filter((event) => {
    const eventDate = new Date(event.start);
    return (
      eventDate.getFullYear() === date.getFullYear() &&
      eventDate.getMonth() === date.getMonth() &&
      eventDate.getDate() === date.getDate()
    );
  });
}

export function getEventsForMonth(events: CalendarEvent[], year: number, month: number): CalendarEvent[] {
  return events.filter((event) => {
    const eventDate = new Date(event.start);
    return eventDate.getFullYear() === year && eventDate.getMonth() === month;
  });
}
