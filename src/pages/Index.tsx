import { useState } from "react";
import { ModeSelection } from "@/components/ModeSelection";
import { ProgramSelection } from "@/components/ProgramSelection";
import { ProcessMonitor } from "@/components/ProcessMonitor";
import { useToast } from "@/hooks/use-toast";

type AppMode = 'selection' | 'auto-program' | 'auto-running' | 'manual';

interface Program {
  id: string;
  program_name: string;
  steps: Array<{
    psi_range: string;
    duration_minutes: number;
    action: string;
  }>;
}

const Index = () => {
  const [mode, setMode] = useState<AppMode>('selection');
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const { toast } = useToast();

  const handleModeSelect = (selectedMode: 'auto' | 'manual') => {
    if (selectedMode === 'auto') {
      setMode('auto-program');
    } else {
      setMode('manual');
      toast({
        title: "Manual Mode",
        description: "Manual mode will be available in the next update",
      });
    }
  };

  const handleStartProgram = (program: Program) => {
    setSelectedProgram(program);
    setMode('auto-running');
    toast({
      title: "Program Started",
      description: `Starting ${program.program_name}`,
    });
  };

  const handleStopProcess = () => {
    setMode('selection');
    setSelectedProgram(null);
  };

  return (
    <>
      {mode === 'selection' && (
        <ModeSelection onSelectMode={handleModeSelect} />
      )}
      
      {mode === 'auto-program' && (
        <ProgramSelection
          onBack={() => setMode('selection')}
          onStartProgram={handleStartProgram}
          currentPressure={0}
          currentTemperature={75}
        />
      )}
      
      {mode === 'auto-running' && selectedProgram && (
        <ProcessMonitor
          program={selectedProgram}
          onStop={handleStopProcess}
        />
      )}
    </>
  );
};

export default Index;
