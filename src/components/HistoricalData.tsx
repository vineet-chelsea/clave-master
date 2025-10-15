import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Download, BarChart3 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format } from "date-fns";
import html2canvas from 'html2canvas';

interface HistoricalDataProps {
  onBack: () => void;
}

interface ProcessSession {
  id: string;
  program_name: string;
  start_time: string;
  end_time: string | null;
  status: string;
  operator_name: string | null;
}

interface ProcessLog {
  id: string;
  timestamp: string;
  pressure: number;
  temperature: number;
  valve_position: number | null;
  status: string;
}

export const HistoricalData = ({ onBack }: HistoricalDataProps) => {
  const [sessions, setSessions] = useState<ProcessSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [logs, setLogs] = useState<ProcessLog[]>([]);
  const [showChart, setShowChart] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const pressureChartRef = useRef<HTMLDivElement>(null);
  const temperatureChartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    const { data, error } = await supabase
      .from('process_sessions')
      .select('*')
      .order('start_time', { ascending: false })
      .limit(50);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to fetch sessions",
        variant: "destructive",
      });
      return;
    }

    setSessions(data || []);
  };

  const fetchLogsForSession = async (sessionId: string) => {
    setLoading(true);
    setSelectedSession(sessionId);
    setShowChart(false);
    
    const { data, error } = await supabase
      .from('process_logs')
      .select('*')
      .eq('session_id', sessionId)
      .order('timestamp', { ascending: true });

    setLoading(false);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to fetch logs",
        variant: "destructive",
      });
      setLogs([]);
      return;
    }

    setLogs(data || []);
  };

  const downloadChart = async (chartRef: React.RefObject<HTMLDivElement>, chartName: string) => {
    if (!chartRef.current) {
      toast({
        title: "Error",
        description: "Chart not found",
        variant: "destructive",
      });
      return;
    }

    try {
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#0a0a0a',
        scale: 2
      });
      
      const image = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      const session = sessions.find(s => s.id === selectedSession);
      link.download = `${chartName}_${session?.program_name?.replace(/\s+/g, '_')}_${format(new Date(), 'yyyyMMdd_HHmmss')}.png`;
      link.href = image;
      link.click();

      toast({
        title: "Download Successful",
        description: `Downloaded ${chartName} chart`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download chart",
        variant: "destructive",
      });
    }
  };

  const exportToExcel = () => {
    if (logs.length === 0) {
      toast({
        title: "No Data",
        description: "Please select a session first",
        variant: "destructive",
      });
      return;
    }

    const session = sessions.find(s => s.id === selectedSession);
    
    // Prepare data for Excel
    const excelData = logs.map(log => ({
      'Timestamp': format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss'),
      'Program Name': session?.program_name || 'N/A',
      'Pressure (PSI)': log.pressure.toFixed(2),
      'Temperature (°C)': log.temperature.toFixed(2),
      'Valve Position (%)': log.valve_position?.toFixed(2) || 'N/A',
      'Status': log.status.toUpperCase()
    }));

    // Create worksheet
    const ws = XLSX.utils.json_to_sheet(excelData);
    
    // Set column widths
    ws['!cols'] = [
      { wch: 20 }, // Timestamp
      { wch: 25 }, // Program Name
      { wch: 15 }, // Pressure
      { wch: 18 }, // Temperature
      { wch: 18 }, // Valve Position
      { wch: 12 }  // Status
    ];

    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Process Data');

    // Generate filename with timestamp
    const filename = `Process_${session?.program_name?.replace(/\s+/g, '_')}_${format(new Date(), 'yyyyMMdd_HHmmss')}.xlsx`;

    // Save file
    XLSX.writeFile(wb, filename);

    toast({
      title: "Export Successful",
      description: `Downloaded ${filename}`,
    });
  };

  const chartData = logs.map(log => ({
    time: format(new Date(log.timestamp), 'HH:mm:ss'),
    pressure: log.pressure,
    temperature: log.temperature
  }));

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <Button
          variant="outline"
          onClick={onBack}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Mode Selection
        </Button>

        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">HISTORICAL DATA</h1>
          <p className="text-muted-foreground">Review past autoclave process runs</p>
        </div>

        {/* Sessions List */}
        <Card className="bg-card border-border p-6">
          <h2 className="text-2xl font-bold mb-4 text-foreground">Recent Process Sessions</h2>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Program Name</TableHead>
                  <TableHead>Start Time</TableHead>
                  <TableHead>End Time</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Operator</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((session) => {
                  const duration = session.end_time 
                    ? Math.round((new Date(session.end_time).getTime() - new Date(session.start_time).getTime()) / 60000)
                    : 'In Progress';
                  
                  return (
                    <TableRow 
                      key={session.id}
                      className={selectedSession === session.id ? 'bg-primary/10' : ''}
                    >
                      <TableCell className="font-medium">{session.program_name}</TableCell>
                      <TableCell>{format(new Date(session.start_time), 'yyyy-MM-dd HH:mm')}</TableCell>
                      <TableCell>
                        {session.end_time 
                          ? format(new Date(session.end_time), 'yyyy-MM-dd HH:mm')
                          : 'Running'
                        }
                      </TableCell>
                      <TableCell>{typeof duration === 'number' ? `${duration} min` : duration}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          session.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          session.status === 'stopped' ? 'bg-red-500/20 text-red-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {session.status.toUpperCase()}
                        </span>
                      </TableCell>
                      <TableCell>{session.operator_name || 'N/A'}</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => fetchLogsForSession(session.id)}
                          disabled={loading && selectedSession === session.id}
                        >
                          {loading && selectedSession === session.id ? 'Loading...' : 'View Details'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </Card>

        {/* Selected Session Details */}
        {selectedSession && (
          <>
            {loading ? (
              <Card className="bg-card border-border p-12 text-center">
                <p className="text-muted-foreground text-lg">Loading session data...</p>
              </Card>
            ) : logs.length === 0 ? (
              <Card className="bg-card border-border p-12 text-center">
                <p className="text-muted-foreground text-lg">No log data available for this session.</p>
              </Card>
            ) : (
              <>
                {/* Action Buttons */}
                <div className="flex gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => setShowChart(!showChart)}
                className="gap-2"
              >
                <BarChart3 className="w-5 h-5" />
                {showChart ? 'Hide Charts' : 'Show Charts'}
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={exportToExcel}
                className="gap-2"
              >
                <Download className="w-5 h-5" />
                Export to Excel
              </Button>
            </div>

            {/* Charts */}
            {showChart && (
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="bg-card border-border p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-foreground">PRESSURE vs TIME</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadChart(pressureChartRef, 'Pressure')}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </Button>
                  </div>
                  <div ref={pressureChartRef}>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis 
                          dataKey="time" 
                          stroke="#888"
                          tick={{ fill: '#888', fontSize: 11 }}
                          interval="preserveStartEnd"
                        />
                        <YAxis 
                          stroke="#888"
                          tick={{ fill: '#888' }}
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
                  </div>
                </Card>

                <Card className="bg-card border-border p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-foreground">TEMPERATURE vs TIME</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadChart(temperatureChartRef, 'Temperature')}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </Button>
                  </div>
                  <div ref={temperatureChartRef}>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis 
                          dataKey="time" 
                          stroke="#888"
                          tick={{ fill: '#888', fontSize: 11 }}
                          interval="preserveStartEnd"
                        />
                        <YAxis 
                          stroke="#888"
                          tick={{ fill: '#888' }}
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
                  </div>
                </Card>
              </div>
            )}

            {/* Data Table */}
            <Card className="bg-card border-border p-6">
              <h3 className="text-xl font-bold mb-4 text-foreground">Process Log Data</h3>
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Pressure (PSI)</TableHead>
                      <TableHead>Temperature (°C)</TableHead>
                      <TableHead>Valve Position (%)</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell>{format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}</TableCell>
                        <TableCell className="text-green-400 font-bold">{log.pressure.toFixed(2)}</TableCell>
                        <TableCell className="text-yellow-400 font-bold">{log.temperature.toFixed(2)}</TableCell>
                        <TableCell>{log.valve_position?.toFixed(2) || 'N/A'}</TableCell>
                        <TableCell>
                          <span className="text-xs font-bold">{log.status.toUpperCase()}</span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>
              </>
            )}
          </>
        )}

        {sessions.length === 0 && (
          <Card className="bg-card border-border p-12 text-center">
            <p className="text-muted-foreground text-lg">No historical data available. Run a process to generate data.</p>
          </Card>
        )}
      </div>
    </div>
  );
};
