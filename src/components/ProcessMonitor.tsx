import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Pause, StopCircle, Play } from "lucide-react";
import { supabase, API_URL } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

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
  program?: Program;
  manualConfig?: {
    targetPressure: number;
    duration: number;
  };
  onStop: () => void;
}

interface ChartDataPoint {
  time: string;
  pressure: number;
  temperature: number;
}

export function ProcessMonitor({ program, manualConfig, onStop }: ProcessMonitorProps) {
  const [status, setStatus] = useState<'running' | 'paused'>('running');
  const [currentStep, setCurrentStep] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);
  const [currentPressure, setCurrentPressure] = useState(0);
  const [currentTemperature, setCurrentTemperature] = useState(25);
  const [sessionId, setSessionId] = useState<string>('');
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const { toast } = useToast();
  const intervalRef = useRef<NodeJS.Timeout>();
  const logIntervalRef = useRef<NodeJS.Timeout>();

  const isManualMode = !!manualConfig;
  const programName = isManualMode ? "Manual Control" : (program?.program_name || "");
  const programId = program?.id || null;

  // Create steps array - either from program or manual config
  const steps = isManualMode && manualConfig
    ? [{ psi_range: `${manualConfig.targetPressure}`, duration_minutes: manualConfig.duration, action: "steady" }]
    : (program?.steps || []);

  // Debug: Log when component props change
  useEffect(() => {
    console.log('ProcessMonitor mounted with:', {
      isManualMode,
      manualConfig,
      program,
      steps
    });
  }, []);

  useEffect(() => {
    let sensorPoll: NodeJS.Timeout;
    let statusPoll: NodeJS.Timeout;
    
    startSession();
    
    // Fetch initial sensor reading immediately
    const fetchInitialReading = async () => {
      try {
        const response = await fetch(`${API_URL}/sensor-readings/latest`);
        const data = await response.json();
        if (data && 'pressure' in data && 'temperature' in data) {
          console.log('Initial sensor reading:', data);
          setCurrentPressure(data.pressure as number);
          setCurrentTemperature(data.temperature as number);
        }
      } catch (error) {
        console.error('Failed to fetch initial reading:', error);
      }
    };
    
    // Fetch immediately
    fetchInitialReading();
    
    // Poll for sensor readings from API every second
    sensorPoll = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/sensor-readings/latest`);
        const data = await response.json();
        if (data && 'pressure' in data && 'temperature' in data) {
          setCurrentPressure(data.pressure as number);
          setCurrentTemperature(data.temperature as number);
        }
      } catch (error) {
        // Silent fail - API not running
      }
    }, 1000);
    
    // Poll for session status every 5 seconds
    statusPoll = setInterval(async () => {
      if (sessionId) {
        try {
          const response = await fetch(`${API_URL}/sessions`);
          const sessions = await response.json();
          const currentSession = sessions.find((s: any) => s.id.toString() === sessionId);
          
          if (currentSession && (currentSession.status === 'completed' || currentSession.status === 'stopped')) {
            console.log('Session completed:', currentSession.status);
            setStatus('paused');
            if (intervalRef.current) clearInterval(intervalRef.current);
            completeProcess();
          }
        } catch (error) {
          // Silent fail
        }
      }
    }, 5000);
    
    return () => {
      clearInterval(sensorPoll);
      clearInterval(statusPoll);
    };
  }, [sessionId]);

  // Start simulation and progress updates
  useEffect(() => {
    console.log('useEffect [status, currentStep] running, status:', status, 'currentStep:', currentStep);
    
    // Clean up any existing intervals first
    if (intervalRef.current) {
      console.log('Clearing existing interval');
      clearInterval(intervalRef.current);
    }
    if (logIntervalRef.current) {
      clearInterval(logIntervalRef.current);
    }
    
    // Only start if running
    if (status === 'running') {
      console.log('Starting simulation and logging');
      startProcessSimulation();
      startDataLogging();
    }
    
    return () => {
      console.log('Cleaning up intervals');
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      if (logIntervalRef.current) {
        clearInterval(logIntervalRef.current);
        logIntervalRef.current = undefined;
      }
    };
  }, [status, currentStep]);

  const startSession = async () => {
    // Try to get the current active session from API
    try {
      const response = await fetch(`${API_URL}/sessions`);
      const sessions = await response.json();
      const activeSession = sessions.find((s: any) => s.status === 'running');
      
      if (activeSession) {
        setSessionId(activeSession.id.toString());
        console.log('Set sessionId to:', activeSession.id);
      } else {
        // Fallback session ID
        setSessionId('local-' + Date.now());
        console.log('No active session found, using local ID');
      }
    } catch (error) {
      // Fallback session ID
      setSessionId('local-' + Date.now());
      console.error('Failed to fetch sessions:', error);
    }
  };

  const startProcessSimulation = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    const step = steps[currentStep];
    if (!step) {
      console.error('No step found for currentStep:', currentStep, 'Steps:', steps);
      return;
    }

    console.log('Starting interval for step:', currentStep, 'duration:', step.duration_minutes);
    
    // Don't use currentPressure from closure - fetch fresh value
    let iteration = 0;
    
    intervalRef.current = setInterval(async () => {
      // Fetch fresh sensor data for this iteration
      let pressure = 0;
      let temperature = 25;
      
      try {
        const response = await fetch(`${API_URL}/sensor-readings/latest`);
        const data = await response.json();
        if (data && 'pressure' in data && 'temperature' in data) {
          pressure = data.pressure as number;
          temperature = data.temperature as number;
        }
      } catch (error) {
        // Silent fail
      }
      
      // Only add to chart if we have valid sensor data
      if (pressure > 0 || temperature > 0) {
        // Update chart data with real sensor readings
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        setChartData(prev => {
          const newData = [...prev, {
            time: timeStr,
            pressure: pressure,
            temperature: temperature
          }];
          // Keep only last 60 data points (1 minute of data)
          const slicedData = newData.slice(-60);
          
          // Log every 5 seconds for debugging
          iteration++;
          if (iteration % 5 === 0) {
            console.log('Chart update:', {
              chartLength: slicedData.length,
              pressure,
              temperature,
              latestPoint: slicedData[slicedData.length - 1]
            });
          }
          
          return slicedData;
        });
      }

      // Update step progress - use the step from the closure, not steps[currentStep]
      const step = steps[currentStep];
      if (step) {
        setStepProgress(prev => {
          // Calculate elapsed time for accurate progress
          // If progress is already > 0, it means we're resuming, calculate based on actual time
          const duration = step.duration_minutes * 60; // Convert to seconds
          
          // Calculate what progress SHOULD be based on elapsed time
          // This handles both fresh starts and resumed sessions
          const currentProgress = prev;
          const newProgress = currentProgress + (100 / duration);
          
          if (newProgress >= 100) {
            if (currentStep < steps.length - 1) {
              setCurrentStep(currentStep + 1);
              return 0;
            } else {
              completeProcess();
              return 100;
            }
          }
          
          // Debug log
          iteration++;
          if (iteration % 10 === 0) {
            console.log('[PROGRESS]', {
              currentProgress,
              newProgress,
              duration,
              stepMinutes: step.duration_minutes
            });
          }
          
          return newProgress;
        });
      }
    }, 1000);
  };

  const startDataLogging = () => {
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);

    // Data logging is handled by the sensor service automatically
    // No need to log here since sensor_service.py does it every second
    // This is just a placeholder for UI functionality
    
    console.log('Data logging started (no-op, handled by backend)');
  };

  const completeProcess = async () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);

    // Session completion is handled by the sensor service
    toast({
      title: "Process Complete",
      description: `${programName} completed successfully`,
    });
  };

  const handlePause = async () => {
    if (status === 'running') {
      // Pause
      try {
        await fetch(`${API_URL}/pause-control`, { method: 'POST' });
        setStatus('paused');
        toast({
          title: "Process Paused",
          description: "Pressure control paused",
        });
      } catch (e) {
        console.error('Failed to pause:', e);
      }
    } else {
      // Resume
      try {
        await fetch(`${API_URL}/resume-control`, { method: 'POST' });
        setStatus('running');
        toast({
          title: "Process Resumed",
          description: "Pressure control resumed",
        });
      } catch (e) {
        console.error('Failed to resume:', e);
      }
    }
  };

  const handleStop = async () => {
    console.log('Stopping process...');
    
    // Clean up intervals
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    if (logIntervalRef.current) {
      clearInterval(logIntervalRef.current);
      logIntervalRef.current = undefined;
    }

    // Stop session via API
    try {
      const response = await fetch(`${API_URL}/stop-control`, { method: 'POST' });
      const result = await response.json();
      console.log('Stop API response:', result);
    } catch (e) {
      console.error('Failed to stop via API:', e);
    }

    toast({
      title: "Process Stopped",
      description: "Process terminated by operator",
      variant: "destructive"
    });

    // Call parent handler to go back
    onStop();
  };

  const currentStepData = steps[currentStep];
  const totalSteps = steps.length;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <Card className="p-6 bg-card border-border">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                {programName}
              </h1>
              <p className="text-muted-foreground mt-1">
                {isManualMode && manualConfig
                  ? `Manual Control - ${manualConfig.targetPressure} PSI for ${manualConfig.duration} min`
                  : `Step ${currentStep + 1} of ${totalSteps} - ${currentStepData?.action.toUpperCase()} to ${currentStepData?.psi_range} PSI`
                }
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
                <p className="text-xs text-muted-foreground mb-2">Target: {currentStepData?.psi_range} PSI</p>
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
              <p className="text-2xl text-muted-foreground mt-2">°C</p>
              <div className="mt-6">
                <p className="text-xs text-muted-foreground mb-2">Operating Temperature</p>
                <Progress value={(currentTemperature / 150) * 100} className="h-2" />
              </div>
            </div>
          </Card>
        </div>

        {/* Real-time Charts */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Pressure vs Time Chart */}
          <Card className="p-6 bg-card border-border">
            <h3 className="text-lg font-bold mb-4 text-foreground">PRESSURE vs TIME</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="time" 
                  stroke="#888"
                  tick={{ fill: '#888', fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#888"
                  tick={{ fill: '#888' }}
                  domain={[0, 60]}
                  label={{ value: 'PSI', angle: -90, position: 'insideLeft', fill: '#888' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#888' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="pressure" 
                  stroke="#22c55e" 
                  strokeWidth={2}
                  dot={false}
                  name="Pressure (PSI)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Temperature vs Time Chart */}
          <Card className="p-6 bg-card border-border">
            <h3 className="text-lg font-bold mb-4 text-foreground">TEMPERATURE vs TIME</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="time" 
                  stroke="#888"
                  tick={{ fill: '#888', fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#888"
                  tick={{ fill: '#888' }}
                  domain={[0, 150]}
                  label={{ value: '°C', angle: -90, position: 'insideLeft', fill: '#888' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#888' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="temperature" 
                  stroke="#f59e0b" 
                  strokeWidth={2}
                  dot={false}
                  name="Temperature (°C)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Step Progress */}
        <Card className="p-6 bg-card border-border">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-foreground">Step Progress</h2>
              <span className="text-muted-foreground">
                {Math.floor((isManualMode && manualConfig ? manualConfig.duration : (currentStepData?.duration_minutes || 0)) * stepProgress / 100)} / {isManualMode && manualConfig ? manualConfig.duration : (currentStepData?.duration_minutes || 0)} minutes
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
        {!isManualMode && (
          <Card className="p-6 bg-card border-border">
            <h2 className="text-xl font-bold text-foreground mb-4">Process Timeline</h2>
            <div className="space-y-2">
              {steps.map((step, idx) => (
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
                      <p className="text-sm text-muted-foreground">{isManualMode && manualConfig ? manualConfig.duration : step.duration_minutes} minutes</p>
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
        )}
      </div>
    </div>
  );
}
