import { useState, useMemo } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useCalendarEvents } from '@/hooks/useCalendarEvents';
import { getEventsForDate } from '@/lib/icsParser';
import { EventCard } from '@/components/EventCard';
import { format, isSameDay } from 'date-fns';
import { CalendarDays, Loader2 } from 'lucide-react';

export function EventCalendar() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const { events, loading, error } = useCalendarEvents();

  const selectedEvents = useMemo(() => {
    if (!selectedDate) return [];
    return getEventsForDate(events, selectedDate);
  }, [events, selectedDate]);

  // Get dates that have events for highlighting
  const eventDates = useMemo(() => {
    return events.map((event) => new Date(event.start));
  }, [events]);

  const modifiers = useMemo(() => ({
    hasEvent: (date: Date) => eventDates.some((eventDate) => isSameDay(date, eventDate)),
  }), [eventDates]);

  const modifiersStyles = {
    hasEvent: {
      fontWeight: 'bold' as const,
    },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-destructive">Error loading calendar: {error}</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
      <Card className="w-fit">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <CalendarDays className="h-5 w-5" />
            Calendar
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={setSelectedDate}
            modifiers={modifiers}
            modifiersStyles={modifiersStyles}
            className="rounded-md"
            components={{
              DayContent: ({ date }) => {
                const hasEvent = eventDates.some((eventDate) => isSameDay(date, eventDate));
                return (
                  <div className="relative w-full h-full flex items-center justify-center">
                    {date.getDate()}
                    {hasEvent && (
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-primary" />
                    )}
                  </div>
                );
              },
            }}
          />
          <div className="mt-4 text-sm text-muted-foreground">
            <Badge variant="outline" className="gap-1">
              {events.length} total events
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">
            {selectedDate ? format(selectedDate, 'EEEE, MMMM d, yyyy') : 'Select a date'}
          </CardTitle>
          {selectedEvents.length > 0 && (
            <Badge variant="secondary" className="w-fit">
              {selectedEvents.length} event{selectedEvents.length !== 1 ? 's' : ''}
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] pr-4">
            {selectedEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <CalendarDays className="h-12 w-12 mb-2 opacity-50" />
                <p>No events scheduled for this day</p>
              </div>
            ) : (
              <div className="space-y-4">
                {selectedEvents
                  .sort((a, b) => a.start.getTime() - b.start.getTime())
                  .map((event) => (
                    <EventCard key={event.id} event={event} />
                  ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
