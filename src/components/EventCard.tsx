import { CalendarEvent } from '@/lib/icsParser';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin, Clock, ExternalLink, Building2 } from 'lucide-react';
import { format } from 'date-fns';

interface EventCardProps {
  event: CalendarEvent;
}

export function EventCard({ event }: EventCardProps) {
  const organizationMatch = event.description.match(/Organization:\s*([^\n]+)/);
  const organization = organizationMatch ? organizationMatch[1].trim() : null;

  return (
    <Card className="group overflow-hidden border-l-4 border-l-primary bg-card hover:bg-accent/30 transition-all duration-300 card-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-base font-heading font-semibold leading-tight group-hover:text-primary transition-colors">
            {event.summary}
          </CardTitle>
        </div>
        {organization && (
          <Badge variant="secondary" className="w-fit text-xs gap-1.5 mt-1">
            <Building2 className="h-3 w-3" />
            {organization}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-2.5 text-sm">
        <div className="flex items-center gap-2.5 text-muted-foreground">
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            <Clock className="h-3.5 w-3.5 text-primary" />
          </div>
          <span className="font-medium">
            {event.start.getHours() === 0 && event.start.getMinutes() === 0
              ? 'Time TBD'
              : format(event.start, 'h:mm a')}
          </span>
        </div>
        {event.location && (
          <div className="flex items-center gap-2.5 text-muted-foreground">
            <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <MapPin className="h-3.5 w-3.5 text-primary" />
            </div>
            <span className="line-clamp-1">{event.location}</span>
          </div>
        )}
        {event.url && (
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-primary font-medium hover:underline underline-offset-2 mt-1 group/link"
          >
            <ExternalLink className="h-4 w-4 transition-transform group-hover/link:translate-x-0.5" />
            <span>View Details</span>
          </a>
        )}
      </CardContent>
    </Card>
  );
}
