import { useState, useEffect, useCallback, useRef } from 'react';
import { CalendarEvent, fetchAndParseICS } from '@/lib/icsParser';

const API_BASE = import.meta.env.VITE_API_URL || 'https://calendar-sync-hub.onrender.com';

export function useCalendarEvents(icsUrl: string = '/events.ics') {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const triggered = useRef(false);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const parsedEvents = await fetchAndParseICS(icsUrl);
      setEvents(parsedEvents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
      console.error('Error loading ICS file:', err);
    } finally {
      setLoading(false);
    }
  }, [icsUrl]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // Fire-and-forget: ask the Render API to scrape fresh data for the next visitor
  useEffect(() => {
    if (triggered.current || !API_BASE) return;
    triggered.current = true;
    fetch(`${API_BASE}/api/update`, { method: 'POST' }).catch(() => {
      // Silently ignore — this is best-effort
    });
  }, []);

  return { events, loading, error, refetch: loadEvents };
}
