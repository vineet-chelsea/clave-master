import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Pause, StopCircle, Play, ArrowLeft } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface Program {
  id: string;
  program_name: string;
  steps: Array<{
    psi_range: string;
    duration_minutes: number;
    action: string;
  }>;
}

interface ProcessMonitorProps {
  program: Program;
  onStop: () => void;
}

export function ProcessMonitor({ program, onStop }: ProcessMonitorProps) {
  const [status, setStatus] = useState<'running' | 'paused'>('running');
  const [currentStep, setCurrentStep] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);
  const [currentPressure, setCurrentPressure] = useState(0);
  const [currentTemperature, setCurrentTemperature] = useState(75);
  const [sessionId, setSessionId] = useState<string>('');
  const { toast } = useToast();
  const intervalRef = useRef<NodeJS.Timeout>();
  const logIntervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    startSession();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (status === 'running') {
      startProcessSimulation();
      startDataLogging();
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    }
  }, [status, currentStep]);

  const startSession = async () => {
    const { data, error } = await supabase
      .from('process_sessions')
      .insert({
        program_id: program.id,
        program_name: program.program_name,
        status: 'running'
      })
      .select()
      .single();

    if (error) {
      toast({
        title: "Error",
        description: "Failed to start session",
        variant: "destructive"
      });
      return;
    }

    setSessionId(data.id);
  };

  const startProcessSimulation = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    const step = program.steps[currentStep];
    const targetPressure = parseFloat(step.psi_range.split('-')[step.psi_range.includes('-') ? 1 : 0]);
    const duration = step.duration_minutes * 60; // Convert to seconds

    intervalRef.current = setInterval(() => {
      setStepProgress((prev) => {
        const newProgress = prev + (100 / duration);
        
        if (newProgress >= 100) {
          if (currentStep < program.steps.length - 1) {
            setCurrentStep(currentStep + 1);
            return 0;
          } else {
            completeProcess();
            return 100;
          }
        }
        return newProgress;
      });

      // Simulate pressure changes
      setCurrentPressure((prev) => {
        const diff = targetPressure - prev;
        return prev + (diff * 0.05); // Gradually approach target
      });

      // Simulate temperature changes
      setCurrentTemperature((prev) => {
        const targetTemp = 120 + (targetPressure * 2);
        const diff = targetTemp - prev;
        return prev + (diff * 0.03);
      });
    }, 1000);
  };

  const startDataLogging = () => {
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);

    logIntervalRef.current = setInterval(async () => {
      if (sessionId) {
        await supabase.from('process_logs').insert({
          session_id: sessionId,
          program_id: program.id,
          program_name: program.program_name,
          pressure: currentPressure,
          temperature: currentTemperature,
          valve_position: (currentPressure / 50) * 100, // Simulated valve position
          status: status
        });
      }
    }, 5000); // Log every 5 seconds
  };

  const completeProcess = async () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);

    await supabase
      .from('process_sessions')
      .update({ status: 'completed', end_time: new Date().toISOString() })
      .eq('id', sessionId);

    toast({
      title: "Process Complete",
      description: `${program.program_name} completed successfully`,
    });
  };

  const handlePause = () => {
    setStatus(status === 'running' ? 'paused' : 'running');
  };

  const handleStop = async () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);

    await supabase
      .from('process_sessions')
      .update({ status: 'stopped', end_time: new Date().toISOString() })
      .eq('id', sessionId);

    toast({
      title: "Process Stopped",
      description: "Process terminated by operator",
      variant: "destructive"
    });

    onStop();
  };

  const currentStepData = program.steps[currentStep];
  const totalSteps = program.steps.length;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <Card className="p-6 bg-card border-border">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                {program.program_name}
              </h1>
              <p className="text-muted-foreground mt-1">
                Step {currentStep + 1} of {totalSteps} - {currentStepData.action.toUpperCase()} to {currentStepData.psi_range} PSI
              </p>
            </div>
            <div className={`px-6 py-3 rounded-lg font-bold text-lg ${
              status === 'running' 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {status.toUpperCase()}
            </div>
          </div>
        </Card>

        {/* Main Display */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-8 bg-card border-2 border-border">
            <div className="text-center">
              <p className="text-sm text-muted-foreground uppercase tracking-wide mb-4">
                Current Pressure
              </p>
              <p className="text-7xl font-bold text-primary">
                {currentPressure.toFixed(1)}
              </p>
              <p className="text-2xl text-muted-foreground mt-2">PSI</p>
              <div className="mt-6">
                <p className="text-xs text-muted-foreground mb-2">Target: {currentStepData.psi_range} PSI</p>
                <Progress value={(currentPressure / 50) * 100} className="h-2" />
              </div>
            </div>
          </Card>

          <Card className="p-8 bg-card border-2 border-border">
            <div className="text-center">
              <p className="text-sm text-muted-foreground uppercase tracking-wide mb-4">
                Current Temperature
              </p>
              <p className="text-7xl font-bold text-primary">
                {currentTemperature.toFixed(1)}
              </p>
              <p className="text-2xl text-muted-foreground mt-2">°F</p>
              <div className="mt-6">
                <p className="text-xs text-muted-foreground mb-2">Operating Temperature</p>
                <Progress value={(currentTemperature / 250) * 100} className="h-2" />
              </div>
            </div>
          </Card>
        </div>

        {/* Step Progress */}
        <Card className="p-6 bg-card border-border">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-foreground">Step Progress</h2>
              <span className="text-muted-foreground">
                {Math.floor((currentStepData.duration_minutes * stepProgress) / 100)} / {currentStepData.duration_minutes} minutes
              </span>
            </div>
            <Progress value={stepProgress} className="h-4" />
          </div>
        </Card>

        {/* Control Buttons */}
        <div className="flex gap-4 justify-center">
          <Button
            size="lg"
            variant="outline"
            onClick={handlePause}
            className="gap-2 px-8 py-6 text-lg"
          >
            {status === 'running' ? (
              <>
                <Pause className="w-6 h-6" />
                PAUSE
              </>
            ) : (
              <>
                <Play className="w-6 h-6" />
                RESUME
              </>
            )}
          </Button>
          <Button
            size="lg"
            variant="destructive"
            onClick={handleStop}
            className="gap-2 px-8 py-6 text-lg"
          >
            <StopCircle className="w-6 h-6" />
            STOP PROCESS
          </Button>
        </div>

        {/* Process Timeline */}
        <Card className="p-6 bg-card border-border">
          <h2 className="text-xl font-bold text-foreground mb-4">Process Timeline</h2>
          <div className="space-y-2">
            {program.steps.map((step, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-4 rounded ${
                  idx === currentStep
                    ? 'bg-primary/20 border-2 border-primary'
                    : idx < currentStep
                    ? 'bg-green-500/10 border border-green-500/30'
                    : 'bg-secondary border border-border'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                    idx === currentStep
                      ? 'bg-primary text-primary-foreground'
                      : idx < currentStep
                      ? 'bg-green-500 text-white'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">{step.action.toUpperCase()} - {step.psi_range} PSI</p>
                    <p className="text-sm text-muted-foreground">{step.duration_minutes} minutes</p>
                  </div>
                </div>
                {idx === currentStep && (
                  <div className="text-sm font-semibold text-primary">IN PROGRESS</div>
                )}
                {idx < currentStep && (
                  <div className="text-sm font-semibold text-green-400">COMPLETED</div>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
