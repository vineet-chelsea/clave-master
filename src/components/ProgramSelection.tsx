import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_URL } from "@/integrations/supabase/client";

interface RollCategory {
  id: number;
  category_name: string;
  is_active: boolean;
}

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
  const [rollCategories, setRollCategories] = useState<RollCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [subRollName, setSubRollName] = useState<string>("");
  const [numberOfRolls, setNumberOfRolls] = useState<string>("");
  const [rollId, setRollId] = useState<string>("");
  const [operatorName, setOperatorName] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadRollCategories();
  }, []);

  useEffect(() => {
    // Update sub-roll name when category changes (only if currently empty or matches previous category)
    if (selectedCategory) {
      const category = rollCategories.find(c => c.category_name === selectedCategory);
      if (category) {
        // Only update if subRollName is empty or matches the category (user hasn't customized it)
        if (!subRollName || subRollName === selectedCategory) {
          setSubRollName(category.category_name);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory, rollCategories]);

  const loadRollCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/roll-categories`);
      const data = await response.json();
      setRollCategories(data);
    } catch (error) {
      console.error('Failed to load roll categories:', error);
      toast({
        title: "Error",
        description: "Failed to load roll categories",
        variant: "destructive"
      });
    }
  };

  const handleStartProgram = async () => {
    // Validation
    if (!selectedCategory) {
      toast({
        title: "Validation Error",
        description: "Please select a roll category",
        variant: "destructive"
      });
      return;
    }

    if (!numberOfRolls || parseInt(numberOfRolls) < 1 || parseInt(numberOfRolls) > 100) {
      toast({
        title: "Validation Error",
        description: "Please enter a valid number of rolls (1-100)",
        variant: "destructive"
      });
      return;
    }

    if (!rollId) {
      toast({
        title: "Validation Error",
        description: "Please enter a Roll ID",
        variant: "destructive"
      });
      return;
    }

    if (!operatorName) {
      toast({
        title: "Validation Error",
        description: "Please enter an operator name",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);

    try {
      // Get program for this category and quantity
      const programResponse = await fetch(
        `${API_URL}/programs/by-category?roll_category_name=${encodeURIComponent(selectedCategory)}&number_of_rolls=${numberOfRolls}`
      );

      if (!programResponse.ok) {
        const errorData = await programResponse.json();
        throw new Error(errorData.error || 'Failed to get program');
      }

      const programData = await programResponse.json();

      // Start the program with all the new fields
      const startResponse = await fetch(`${API_URL}/start-auto-program`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          roll_category_name: selectedCategory,
          number_of_rolls: parseInt(numberOfRolls),
          sub_roll_name: subRollName || selectedCategory,
          roll_id: rollId,
          operator_name: operatorName
        })
      });

      if (!startResponse.ok) {
        const errorData = await startResponse.json();
        throw new Error(errorData.error || 'Failed to start program');
      }

      const startData = await startResponse.json();

      // Convert to Program format for onStartProgram
      const program: Program = {
        id: programData.id.toString(),
        program_number: programData.program_number,
        program_name: programData.program_name,
        description: programData.description || '',
        steps: programData.steps
      };

      onStartProgram(program);
    } catch (error: any) {
      console.error('Failed to start program:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to start program",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
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

        {/* Program Selection Form */}
        <Card className="p-6">
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-foreground">Program Configuration</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Roll Category Dropdown */}
              <div className="space-y-2">
                <Label htmlFor="roll-category">Roll Category *</Label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger id="roll-category">
                    <SelectValue placeholder="Select roll category" />
                  </SelectTrigger>
                  <SelectContent>
                    {rollCategories.map((category) => (
                      <SelectItem key={category.id} value={category.category_name}>
                        {category.category_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Sub-Roll Name Input */}
              <div className="space-y-2">
                <Label htmlFor="sub-roll-name">Sub-Roll Name</Label>
                <Input
                  id="sub-roll-name"
                  value={subRollName}
                  onChange={(e) => setSubRollName(e.target.value)}
                  placeholder={selectedCategory || "Enter sub-roll name"}
                />
                <p className="text-xs text-muted-foreground">
                  Defaults to roll category name. Can be edited.
                </p>
              </div>

              {/* Number of Rolls */}
              <div className="space-y-2">
                <Label htmlFor="number-of-rolls">Number of Rolls * (1-100)</Label>
                <Input
                  id="number-of-rolls"
                  type="number"
                  min="1"
                  max="100"
                  value={numberOfRolls}
                  onChange={(e) => setNumberOfRolls(e.target.value)}
                  placeholder="Enter number of rolls"
                />
              </div>

              {/* Roll ID */}
              <div className="space-y-2">
                <Label htmlFor="roll-id">Roll ID *</Label>
                <Input
                  id="roll-id"
                  value={rollId}
                  onChange={(e) => setRollId(e.target.value)}
                  placeholder="Enter roll ID for reporting"
                />
              </div>

              {/* Operator Name */}
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="operator-name">Operator Name *</Label>
                <Input
                  id="operator-name"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  placeholder="Enter operator name"
                />
              </div>
            </div>

            {/* Start Button */}
            <div className="flex justify-end pt-4">
              <Button
                size="lg"
                onClick={handleStartProgram}
                disabled={loading}
                className="gap-2 text-lg px-8 py-6 bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg"
              >
                <Play className="w-6 h-6" />
                {loading ? "Starting..." : "START SESSION"}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
