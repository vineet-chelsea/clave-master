import { useState, useEffect } from "react";
import { ModeSelection } from "@/components/ModeSelection";
import { ProgramSelection } from "@/components/ProgramSelection";
import { ProcessMonitor } from "@/components/ProcessMonitor";
import { ManualControl } from "@/components/ManualControl";
import { HistoricalData } from "@/components/HistoricalData";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";

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
  const [currentPressure, setCurrentPressure] = useState<number>(0);
  const [currentTemperature, setCurrentTemperature] = useState<number>(25);
  const { toast } = useToast();

  useEffect(() => {
    // Check if there's an active session on page load
    const checkActiveSession = async () => {
      console.log('[INDEX] Checking for active sessions on page load...');
      try {
        const response = await fetch('http://localhost:5000/api/sessions');
        const sessions = await response.json();
        
        console.log('[INDEX] All sessions:', sessions);
        
        // Check for active running sessions (look for most recent running session)
        const activeSession = sessions.find((s: any) => s.status === 'running');
        
        console.log('[INDEX] Active session:', activeSession);
        
        if (activeSession) {
          // Check if it's an auto program (has steps_data)
          if (activeSession.steps_data && Array.isArray(activeSession.steps_data) && activeSession.steps_data.length > 0) {
            // AUTO PROGRAM - restore with program data
            console.log('[INDEX] ✓ Restoring auto program session');
            console.log('Program:', activeSession.program_name);
            console.log('Steps:', activeSession.steps_data.length);
            
            // Find the program from steps_data
            const program: Program = {
              id: activeSession.id.toString(),
              program_name: activeSession.program_name || 'Auto Program',
              steps: activeSession.steps_data
            };
            
            setSelectedProgram(program);
            setMode('auto-running');
            
            toast({
              title: "Session Restored",
              description: `Resuming: ${program.program_name}`,
            });
          } else if (activeSession.target_pressure && activeSession.duration_minutes) {
            // MANUAL MODE - restore with manual config
            console.log('[INDEX] ✓ Restoring manual session');
            console.log('Target pressure:', activeSession.target_pressure);
            console.log('Duration:', activeSession.duration_minutes);
            
            const targetPressure = parseFloat(activeSession.target_pressure);
            const duration = parseInt(activeSession.duration_minutes);
            
            setManualConfig({
              targetPressure: targetPressure,
              duration: duration
            });
            setMode('manual-running');
            
            toast({
              title: "Session Restored",
              description: `Resuming: ${targetPressure} PSI for ${duration} min`,
            });
          } else {
            console.log('[INDEX] ✗ Session missing required data');
            console.log('[INDEX] Session data:', {
              hasSteps: !!activeSession.steps_data,
              hasTarget: !!activeSession.target_pressure,
              hasDuration: !!activeSession.duration_minutes,
              status: activeSession.status
            });
          }
        } else {
          console.log('[INDEX] No active session found');
        }
      } catch (error) {
        console.error('[INDEX] Failed to check active session:', error);
      }
    };

    checkActiveSession();
  }, []);

  useEffect(() => {
    // Fetch latest sensor reading from API
    const fetchLatestReading = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/sensor-readings/latest');
        const data = await response.json();
        if (data && 'pressure' in data && 'temperature' in data) {
          setCurrentPressure(data.pressure as number);
          setCurrentTemperature(data.temperature as number);
        }
      } catch (error) {
        console.error('Failed to fetch sensor reading:', error);
      }
    };

    fetchLatestReading();

    // Poll for updates every second
    const interval = setInterval(fetchLatestReading, 1000);
    
    // Also check for active session every 2 seconds (in case one starts)
    const sessionCheck = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:5000/api/sessions');
        const sessions = await response.json();
        const activeSession = sessions.find((s: any) => s.status === 'running');
        
        if (activeSession && mode === 'selection') {
          // We were on selection screen but a session is active - restore it
          console.log('[INDEX] 🔄 Active session found while on selection screen, restoring...', activeSession);
          
          // Check if it's an auto program
          if (activeSession.steps_data && Array.isArray(activeSession.steps_data) && activeSession.steps_data.length > 0) {
            // Auto program
            const program: Program = {
              id: activeSession.id.toString(),
              program_name: activeSession.program_name || 'Auto Program',
              steps: activeSession.steps_data
            };
            
            setSelectedProgram(program);
            setMode('auto-running');
          } else if (activeSession.target_pressure && activeSession.duration_minutes) {
            // Manual mode
            const targetPressure = parseFloat(activeSession.target_pressure);
            const duration = parseInt(activeSession.duration_minutes);
            
            setManualConfig({
              targetPressure: targetPressure,
              duration: duration
            });
            setMode('manual-running');
          }
          
          toast({
            title: "Session Detected",
            description: "Resuming active session...",
          });
        }
      } catch (error) {
        console.error('[INDEX] Session check error:', error);
      }
    }, 2000); // Check every 2 seconds

    return () => {
      clearInterval(interval);
      clearInterval(sessionCheck);
    };
  }, [mode]);

  const handleModeSelect = (selectedMode: 'auto' | 'manual' | 'history') => {
    if (selectedMode === 'auto') {
      setMode('auto-program');
    } else if (selectedMode === 'manual') {
      setMode('manual-config');
    } else {
      setMode('history');
    }
  };

  const handleStartProgram = async (program: Program) => {
    try {
      // Calculate total duration and extract steps
      const totalDuration = program.steps.reduce((sum, step) => sum + step.duration_minutes, 0);
      
      // Send program steps to backend for multi-step execution
      const response = await fetch('http://localhost:5000/api/start-auto-program', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          program_name: program.program_name,
          steps: program.steps,
          total_duration: totalDuration
        })
      });
      
      const result = await response.json();
      
      console.log('API Response:', result);
      
      if (result.success) {
        setSelectedProgram(program);
        setMode('auto-running');
        toast({
          title: "Program Started",
          description: `Starting ${program.program_name}`,
        });
      } else {
        console.error('API returned error:', result.error);
        throw new Error(result.error || 'Failed to start program');
      }
    } catch (error) {
      console.error('Failed to start program:', error);
      console.error('Error details:', error instanceof Error ? error.stack : '');
      toast({
        title: "Failed to Start",
        description: error instanceof Error ? error.message : "Could not start program",
        variant: "destructive"
      });
    }
  };

  const handleManualStart = async (targetPressure: number, duration: number) => {
    try {
      // Call API to start control session
      const response = await fetch('http://localhost:5000/api/start-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_pressure: targetPressure,
          duration_minutes: duration,
          program_name: 'Manual Control'
        })
      });
      
      const result = await response.json();
      
      console.log('API Response:', result);
      
      if (result.success) {
        setManualConfig({ targetPressure, duration });
        setMode('manual-running');
        toast({
          title: "Manual Process Started",
          description: `Target: ${targetPressure} PSI for ${duration} minutes`,
        });
      } else {
        console.error('API returned error:', result.error);
        throw new Error(result.error || 'Failed to start session');
      }
    } catch (error) {
      console.error('Failed to start control:', error);
      console.error('Error details:', error instanceof Error ? error.stack : '');
      toast({
        title: "Failed to Start",
        description: error instanceof Error ? error.message : "Could not start pressure control",
        variant: "destructive"
      });
    }
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
          currentPressure={currentPressure}
          currentTemperature={currentTemperature}
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
          currentPressure={currentPressure}
          currentTemperature={currentTemperature}
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
