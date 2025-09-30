import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PlayCircle, Hand, History } from "lucide-react";

interface ModeSelectionProps {
  onSelectMode: (mode: 'auto' | 'manual' | 'history') => void;
}

export function ModeSelection({ onSelectMode }: ModeSelectionProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="max-w-6xl w-full space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold text-foreground tracking-tight">
            AUTOCLAVE CONTROL SYSTEM
          </h1>
          <p className="text-xl text-muted-foreground">
            Select Operating Mode
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card 
            className="p-8 border-2 border-border hover:border-primary transition-all cursor-pointer group bg-card"
            onClick={() => onSelectMode('auto')}
          >
            <div className="flex flex-col items-center space-y-6">
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <PlayCircle className="w-12 h-12 text-primary" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-foreground">AUTO MODE</h2>
                <p className="text-muted-foreground">
                  Select and run pre-programmed cycles
                </p>
              </div>
              <Button 
                size="lg" 
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                SELECT AUTO MODE
              </Button>
            </div>
          </Card>

          <Card 
            className="p-8 border-2 border-border hover:border-primary transition-all cursor-pointer group bg-card"
            onClick={() => onSelectMode('manual')}
          >
            <div className="flex flex-col items-center space-y-6">
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <Hand className="w-12 h-12 text-primary" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-foreground">MANUAL MODE</h2>
                <p className="text-muted-foreground">
                  Direct control of pressure and valves
                </p>
              </div>
              <Button 
                size="lg" 
                className="w-full bg-secondary hover:bg-secondary/90 text-secondary-foreground"
              >
                SELECT MANUAL MODE
              </Button>
            </div>
          </Card>

          <Card 
            className="p-8 border-2 border-border hover:border-primary transition-all cursor-pointer group bg-card"
            onClick={() => onSelectMode('history')}
          >
            <div className="flex flex-col items-center space-y-6">
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <History className="w-12 h-12 text-primary" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-foreground">HISTORY</h2>
                <p className="text-muted-foreground">
                  View past data & export reports
                </p>
              </div>
              <Button 
                size="lg" 
                className="w-full bg-accent hover:bg-accent/90 text-accent-foreground"
              >
                VIEW HISTORY
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
