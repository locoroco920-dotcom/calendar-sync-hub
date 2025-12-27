import { CalendarEvent } from '@/lib/icsParser';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin, Clock, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';

interface EventCardProps {
  event: CalendarEvent;
}

export function EventCard({ event }: EventCardProps) {
  const organizationMatch = event.description.match(/Organization:\s*([^\n]+)/);
  const organization = organizationMatch ? organizationMatch[1].trim() : null;

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-primary">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base font-semibold leading-tight">
            {event.summary}
          </CardTitle>
        </div>
        {organization && (
          <Badge variant="secondary" className="w-fit text-xs">
            {organization}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Clock className="h-4 w-4 shrink-0" />
          <span>
            {format(event.start, 'h:mm a')} - {format(event.end, 'h:mm a')}
          </span>
        </div>
        {event.location && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="h-4 w-4 shrink-0" />
            <span>{event.location}</span>
          </div>
        )}
        {event.url && (
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-primary hover:underline"
          >
            <ExternalLink className="h-4 w-4 shrink-0" />
            <span>View Details</span>
          </a>
        )}
      </CardContent>
    </Card>
  );
}
