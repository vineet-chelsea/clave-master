import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Play } from "lucide-react";

interface ManualControlProps {
  onBack: () => void;
  onStart: (targetPressure: number, duration: number) => void;
  currentPressure: number;
  currentTemperature: number;
}

export const ManualControl = ({ 
  onBack, 
  onStart,
  currentPressure,
  currentTemperature
}: ManualControlProps) => {
  const [targetPressure, setTargetPressure] = useState(20);
  const [duration, setDuration] = useState(30); // minutes

  const handleStart = () => {
    if (duration > 0) {
      onStart(targetPressure, duration);
    }
  };

  return (
    <div className="min-h-screen bg-industrial-bg text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <Button
          variant="outline"
          onClick={onBack}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Mode Selection
        </Button>

        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">MANUAL CONTROL</h1>
          <p className="text-muted-foreground">Direct pressure and duration control</p>
        </div>

        {/* Current Readings */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="bg-industrial-panel border-industrial-border p-6">
            <div className="text-industrial-muted text-sm mb-2">CURRENT PRESSURE</div>
            <div className="text-4xl font-bold text-industrial-active">
              {currentPressure.toFixed(1)} <span className="text-2xl">PSI</span>
            </div>
          </Card>

          <Card className="bg-industrial-panel border-industrial-border p-6">
            <div className="text-industrial-muted text-sm mb-2">CURRENT TEMPERATURE</div>
            <div className="text-4xl font-bold text-industrial-warning">
              {currentTemperature.toFixed(1)} <span className="text-2xl">°C</span>
            </div>
          </Card>
        </div>

        {/* Manual Controls */}
        <Card className="bg-industrial-panel border-industrial-border p-8">
          <div className="space-y-8">
            {/* Pressure Slider */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <Label className="text-lg">TARGET PRESSURE</Label>
                <span className="text-3xl font-bold text-primary">
                  {targetPressure} <span className="text-xl">PSI</span>
                </span>
              </div>
              <Slider
                value={[targetPressure]}
                onValueChange={(value) => setTargetPressure(value[0])}
                min={0}
                max={50}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-industrial-muted">
                <span>0 PSI</span>
                <span>25 PSI</span>
                <span>50 PSI</span>
              </div>
            </div>

            {/* Duration Input */}
            <div className="space-y-4">
              <Label className="text-lg">DURATION (Minutes)</Label>
              <Input
                type="number"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                min={1}
                max={480}
                className="text-2xl font-bold h-16 bg-industrial-display border-industrial-border text-foreground"
              />
              <p className="text-sm text-industrial-muted">
                Maximum: 480 minutes (8 hours)
              </p>
            </div>

            {/* Start Button */}
            <Button
              onClick={handleStart}
              disabled={duration <= 0}
              className="w-full h-16 text-xl bg-industrial-active hover:bg-industrial-active/90"
            >
              <Play className="mr-2 h-6 w-6" />
              START MANUAL PROCESS
            </Button>
          </div>
        </Card>

        {/* Safety Information */}
        <Card className="bg-industrial-warning/10 border-industrial-warning p-4">
          <h3 className="font-bold text-industrial-warning mb-2">⚠ SAFETY NOTICE</h3>
          <ul className="text-sm space-y-1 text-industrial-muted">
            <li>• Monitor pressure and temperature continuously</li>
            <li>• Maximum safe pressure: 50 PSI</li>
            <li>• Emergency stop available during operation</li>
            <li>• All operations logged to database</li>
          </ul>
        </Card>
      </div>
    </div>
  );
};
