import { EventCalendar } from '@/components/EventCalendar';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container py-6">
          <h1 className="text-3xl font-bold tracking-tight">Meadowlands Event Tracker</h1>
          <p className="text-muted-foreground mt-1">
            Stay updated with local events and activities
          </p>
        </div>
      </header>
      <main className="container py-8">
        <EventCalendar />
      </main>
    </div>
  );
};

export default Index;
