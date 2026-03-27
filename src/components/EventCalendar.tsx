import React, { useState, useMemo, useEffect } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { useCalendarEvents } from '@/hooks/useCalendarEvents';
import { getEventsForDate } from '@/lib/icsParser';
import { EventCard } from '@/components/EventCard';
import { format, isSameDay } from 'date-fns';
import { CalendarDays, Loader2, Sparkles, Filter } from 'lucide-react';

export function EventCalendar() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const { events, loading, error } = useCalendarEvents();

  // All known calendar sources
  const ALL_ORGANIZATIONS = useMemo(() => [
    'African American Chamber of Commerce of New Jersey (AACCNJ)',
    'Bergen County Chamber of Commerce',
    'Choose New Jersey',
    'Commerce and Industry Association of NJ (CIANJ)',
    'Fort Lee Regional Chamber of Commerce',
    'Greater Paterson Chamber of Commerce',
    'Hudson County Chamber of Commerce',
    'Middlesex County Regional Chamber of Commerce',
    'Morris County Chamber of Commerce',
    'New Jersey Business & Industry Association (NJBIA)',
    'New Jersey Chamber of Commerce',
    'New Jersey Economic Development Authority (NJEDA)',
    'Newark Regional Business Partnership (NRBP)',
    'North Jersey Chamber of Commerce',
    'Statewide Hispanic Chamber of Commerce of NJ (SHCCNJ)',
  ], []);

  const [selectedOrgs, setSelectedOrgs] = useState<Set<string>>(() => new Set([
    'African American Chamber of Commerce of New Jersey (AACCNJ)',
    'Bergen County Chamber of Commerce',
    'Choose New Jersey',
    'Commerce and Industry Association of NJ (CIANJ)',
    'Fort Lee Regional Chamber of Commerce',
    'Greater Paterson Chamber of Commerce',
    'Hudson County Chamber of Commerce',
    'Middlesex County Regional Chamber of Commerce',
    'Morris County Chamber of Commerce',
    'New Jersey Business & Industry Association (NJBIA)',
    'New Jersey Chamber of Commerce',
    'New Jersey Economic Development Authority (NJEDA)',
    'Newark Regional Business Partnership (NRBP)',
    'North Jersey Chamber of Commerce',
    'Statewide Hispanic Chamber of Commerce of NJ (SHCCNJ)',
  ]));

  // Merge hardcoded orgs with any dynamically found ones
  const organizations = useMemo(() => {
    const orgs = new Set<string>(ALL_ORGANIZATIONS);
    events.forEach((e) => {
      if (e.organization) orgs.add(e.organization);
    });
    return Array.from(orgs).sort();
  }, [events, ALL_ORGANIZATIONS]);

  const toggleOrg = (org: string) => {
    setSelectedOrgs((prev) => {
      const next = new Set(prev);
      if (next.has(org)) {
        next.delete(org);
      } else {
        next.add(org);
      }
      return next;
    });
  };

  // Add any new dynamic orgs to selectedOrgs
  React.useEffect(() => {
    const dynamicOrgs = events.map(e => e.organization).filter(Boolean) as string[];
    setSelectedOrgs(prev => {
      const next = new Set(prev);
      let changed = false;
      dynamicOrgs.forEach(org => {
        if (!next.has(org)) { next.add(org); changed = true; }
      });
      return changed ? next : prev;
    });
  }, [events]);

  // Filter events by selected orgs
  const filteredEvents = useMemo(() => {
    if (selectedOrgs.size === 0) return [];
    return events.filter((e) => !e.organization || selectedOrgs.has(e.organization));
  }, [events, selectedOrgs]);

  const selectedEvents = useMemo(() => {
    if (!selectedDate) return [];
    return getEventsForDate(filteredEvents, selectedDate);
  }, [filteredEvents, selectedDate]);

  const eventDates = useMemo(() => {
    return filteredEvents.map((event) => new Date(event.start));
  }, [filteredEvents]);

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
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-muted-foreground animate-pulse">Loading events...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="card-shadow border-destructive/50">
          <CardContent className="p-6">
            <p className="text-destructive">Error loading calendar: {error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:gap-8 lg:grid-cols-[auto_1fr]">
      {/* Left Column: Calendar + Filter */}
      <div className="space-y-6">
        {/* Calendar Card */}
        <Card className="w-full card-shadow animate-fade-up">
          <CardHeader className="pb-3 border-b">
            <CardTitle className="flex items-center gap-2 text-lg font-heading font-semibold">
              <CalendarDays className="h-5 w-5 text-primary" />
              Calendar
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              modifiers={modifiers}
              modifiersStyles={modifiersStyles}
              className="rounded-lg"
              components={{
                DayContent: ({ date }) => {
                  const hasEvent = eventDates.some((eventDate) => isSameDay(date, eventDate));
                  return (
                    <div className="relative w-full h-full flex items-center justify-center">
                      {date.getDate()}
                      {hasEvent && (
                        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 event-dot animate-pulse-glow" />
                      )}
                    </div>
                  );
                },
              }}
            />
            <div className="mt-4 pt-4 border-t flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <Badge variant="secondary" className="font-medium">
                {filteredEvents.length} upcoming events
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Filter Card */}
        {organizations.length > 0 && (
          <Card className="card-shadow animate-fade-up" style={{ animationDelay: '0.05s' }}>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="flex items-center gap-2 text-lg font-heading font-semibold">
                <Filter className="h-5 w-5 text-primary" />
                Calendars
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <ScrollArea className="h-[200px] pr-3">
                <div className="space-y-3">
                  {organizations.map((org) => (
                    <label
                      key={org}
                      className="flex items-center gap-3 cursor-pointer group"
                    >
                      <Checkbox
                        checked={selectedOrgs.has(org)}
                        onCheckedChange={() => toggleOrg(org)}
                      />
                      <span className="text-sm font-medium group-hover:text-primary transition-colors">
                        {org}
                      </span>
                    </label>
                  ))}
                </div>
              </ScrollArea>
              <div className="mt-4 pt-3 border-t flex gap-2">
                <button
                  onClick={() => setSelectedOrgs(new Set(organizations))}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  Select All
                </button>
                <span className="text-muted-foreground text-xs">·</span>
                <button
                  onClick={() => setSelectedOrgs(new Set())}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  Clear All
                </button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Events List Card */}
      <Card className="card-shadow animate-fade-up" style={{ animationDelay: '0.1s' }}>
        <CardHeader className="pb-3 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <CardTitle className="text-lg font-heading font-semibold">
              {selectedDate ? format(selectedDate, 'EEEE, MMMM d, yyyy') : 'Select a date'}
            </CardTitle>
            {selectedEvents.length > 0 && (
              <Badge className="w-fit bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
                {selectedEvents.length} event{selectedEvents.length !== 1 ? 's' : ''}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          <ScrollArea className="h-[500px] pr-4">
            {selectedEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                  <CalendarDays className="h-8 w-8 opacity-50" />
                </div>
                <p className="font-medium">No events scheduled</p>
                <p className="text-sm mt-1">Select a date with events to view details</p>
              </div>
            ) : (
              <div className="space-y-4">
                {selectedEvents
                  .sort((a, b) => a.start.getTime() - b.start.getTime())
                  .map((event, index) => (
                    <div
                      key={event.id}
                      className="animate-scale-in"
                      style={{ animationDelay: `${index * 0.05}s` }}
                    >
                      <EventCard event={event} />
                    </div>
                  ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
