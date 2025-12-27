import { EventCalendar } from '@/components/EventCalendar';
import logo from '@/assets/logo.png';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Header */}
      <header className="relative overflow-hidden border-b bg-card">
        <div className="absolute inset-0 hero-gradient" />
        <div className="container relative py-8 md:py-12">
          <div className="flex flex-col md:flex-row items-center gap-6 md:gap-8">
            <img 
              src={logo} 
              alt="Meadowlands Chamber" 
              className="h-16 md:h-20 w-auto animate-fade-up"
            />
            <div className="text-center md:text-left animate-fade-up" style={{ animationDelay: '0.1s' }}>
              <h1 className="text-2xl md:text-4xl font-heading font-bold tracking-tight text-foreground">
                Event Tracker
              </h1>
              <p className="text-muted-foreground mt-2 text-sm md:text-base max-w-md">
                Stay updated with local events and activities from the Meadowlands Chamber and surrounding communities
              </p>
            </div>
          </div>
        </div>
        {/* Decorative bottom wave */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-30" />
      </header>

      <main className="container py-8 md:py-12">
        <EventCalendar />
      </main>

      {/* Footer */}
      <footer className="border-t bg-card/50 py-6">
        <div className="container text-center text-sm text-muted-foreground">
          <p>Building Connections. Driving Business Growth.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
