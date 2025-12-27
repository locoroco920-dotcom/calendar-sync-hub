import { useState, useEffect, useCallback } from 'react';
import { CalendarEvent, fetchAndParseICS } from '@/lib/icsParser';

export function useCalendarEvents(icsUrl: string = '/events.ics') {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return { events, loading, error, refetch: loadEvents };
}
