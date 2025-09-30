import { useState } from "react";
import { ModeSelection } from "@/components/ModeSelection";
import { ProgramSelection } from "@/components/ProgramSelection";
import { ProcessMonitor } from "@/components/ProcessMonitor";
import { ManualControl } from "@/components/ManualControl";
import { HistoricalData } from "@/components/HistoricalData";
import { useToast } from "@/hooks/use-toast";

type AppMode = 'selection' | 'auto-program' | 'auto-running' | 'manual-config' | 'manual-running' | 'history';

interface Program {
  id: string;
  program_name: string;
  steps: Array<{
    psi_range: string;
    duration_minutes: number;
    action: string;
  }>;
}

interface ManualConfig {
  targetPressure: number;
  duration: number;
}

const Index = () => {
  const [mode, setMode] = useState<AppMode>('selection');
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [manualConfig, setManualConfig] = useState<ManualConfig | null>(null);
  const { toast } = useToast();

  const handleModeSelect = (selectedMode: 'auto' | 'manual' | 'history') => {
    if (selectedMode === 'auto') {
      setMode('auto-program');
    } else if (selectedMode === 'manual') {
      setMode('manual-config');
    } else {
      setMode('history');
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

  const handleManualStart = (targetPressure: number, duration: number) => {
    setManualConfig({ targetPressure, duration });
    setMode('manual-running');
    toast({
      title: "Manual Process Started",
      description: `Target: ${targetPressure} PSI for ${duration} minutes`,
    });
  };

  const handleStopProcess = () => {
    setMode('selection');
    setSelectedProgram(null);
    setManualConfig(null);
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
          currentTemperature={25}
        />
      )}
      
      {mode === 'auto-running' && selectedProgram && (
        <ProcessMonitor
          program={selectedProgram}
          onStop={handleStopProcess}
        />
      )}

      {mode === 'manual-config' && (
        <ManualControl
          onBack={() => setMode('selection')}
          onStart={handleManualStart}
          currentPressure={0}
          currentTemperature={25}
        />
      )}

      {mode === 'manual-running' && manualConfig && (
        <ProcessMonitor
          manualConfig={manualConfig}
          onStop={handleStopProcess}
        />
      )}

      {mode === 'history' && (
        <HistoricalData
          onBack={() => setMode('selection')}
        />
      )}
    </>
  );
};

export default Index;
