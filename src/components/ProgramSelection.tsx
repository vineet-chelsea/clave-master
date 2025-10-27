import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Program {
  id: string;
  program_number: number;
  program_name: string;
  description: string;
  steps: Array<{
    psi_range: string;
    duration_minutes: number;
    action: string;
  }>;
}

interface ProgramSelectionProps {
  onBack: () => void;
  onStartProgram: (program: Program) => void;
  currentPressure: number;
  currentTemperature: number;
}

export function ProgramSelection({ 
  onBack, 
  onStartProgram,
  currentPressure,
  currentTemperature 
}: ProgramSelectionProps) {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadPrograms();
  }, []);

  const loadPrograms = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/programs');
      const data = await response.json();
      
      // Convert API response to Program format
      const formattedPrograms = data.map((p: any) => ({
        id: p.id.toString(),
        program_number: p.program_number,
        program_name: p.program_name,
        description: p.description || '',
        steps: p.steps
      }));
      
      setPrograms(formattedPrograms);
    } catch (error) {
      console.error('Failed to load programs:', error);
      toast({
        title: "Error",
        description: "Failed to load programs",
        variant: "destructive"
      });
    }
  };

  const handleStartProgram = () => {
    if (selectedProgram) {
      onStartProgram(selectedProgram);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={onBack}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Mode Selection
          </Button>
          <h1 className="text-3xl font-bold text-foreground">
            AUTO MODE - PROGRAM SELECTION
          </h1>
        </div>

        {/* Current Readings */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-6 bg-card border-border">
            <div className="text-center">
              <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Current Pressure
              </p>
              <p className="text-5xl font-bold text-primary">
                {currentPressure.toFixed(1)}
              </p>
              <p className="text-lg text-muted-foreground mt-1">PSI</p>
            </div>
          </Card>
          <Card className="p-6 bg-card border-border">
            <div className="text-center">
              <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
                Current Temperature
              </p>
              <p className="text-5xl font-bold text-primary">
                {currentTemperature.toFixed(1)}
              </p>
              <p className="text-lg text-muted-foreground mt-1">°C</p>
            </div>
          </Card>
        </div>

        {/* Program List */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programs.map((program) => (
            <Card
              key={program.id}
              className={`p-6 cursor-pointer transition-all border-2 ${
                selectedProgram?.id === program.id
                  ? 'border-primary bg-primary/10'
                  : 'border-border bg-card hover:border-primary/50'
              }`}
              onClick={() => setSelectedProgram(program)}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-primary">
                    P{program.program_number.toString().padStart(2, '0')}
                  </span>
                  {selectedProgram?.id === program.id && (
                    <div className="w-3 h-3 rounded-full bg-primary animate-pulse" />
                  )}
                </div>
                <h3 className="text-xl font-bold text-foreground">
                  {program.program_name}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {program.description}
                </p>
                <div className="pt-2 space-y-1">
                  {program.steps.map((step, idx) => (
                    <div key={idx} className="text-xs text-muted-foreground flex justify-between">
                      <span>{step.psi_range} PSI</span>
                      <span>{step.duration_minutes} min</span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Start Button */}
        {selectedProgram && (
          <div className="fixed bottom-8 right-8">
            <Button
              size="lg"
              onClick={handleStartProgram}
              className="gap-2 text-lg px-8 py-6 bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg"
            >
              <Play className="w-6 h-6" />
              START PROGRAM
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
