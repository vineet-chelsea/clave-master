import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Download, BarChart3, FileText, ChevronLeft, ChevronRight } from "lucide-react";
import { supabase, API_URL } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format } from "date-fns";
import { formatInTimeZone, toZonedTime } from "date-fns-tz";
import html2canvas from 'html2canvas';

interface HistoricalDataProps {
  onBack: () => void;
}

// IST timezone constant
const IST_TIMEZONE = 'Asia/Kolkata';

// Module-level export lock - persists across all component instances and re-renders
let globalExportLock = false;
let exportLockTimeout: NodeJS.Timeout | null = null;
let downloadCounter = 0; // Track how many downloads have been initiated

// Helper function to format date in IST
const formatIST = (date: string | Date | null | undefined, formatStr: string) => {
  if (!date) return 'N/A';
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return 'Invalid Date';
    return formatInTimeZone(dateObj, IST_TIMEZONE, formatStr);
  } catch (error) {
    console.error('Error formatting date:', error, date);
    return 'Invalid Date';
  }
};

interface ProcessSession {
  id: string;
  program_name: string;
  start_time: string;
  end_time: string | null;
  status: string;
  operator_name: string | null;
  roll_category_name?: string | null;
  sub_roll_name?: string | null;
  roll_id?: string | null;
  number_of_rolls?: number | null;
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
  const [exportingExcel, setExportingExcel] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalSessions, setTotalSessions] = useState(0);
  const [perPage] = useState(10); // Sessions per page
  const { toast } = useToast();
  const pressureChartRef = useRef<HTMLDivElement>(null);
  const temperatureChartRef = useRef<HTMLDivElement>(null);
  const isExportingRef = useRef(false); // Use ref for immediate synchronous check

  useEffect(() => {
    fetchSessions(currentPage);
  }, [currentPage]);

  const fetchSessions = async (page: number = 1) => {
    try {
      setLoading(true);
      // Use pagination parameters
      const url = `${API_URL}/sessions?page=${page}&per_page=${perPage}`;
      const response = await fetch(url);
      const data = await response.json();
      
      // Handle paginated response
      let sessionsData: any[] = [];
      let paginationData = null;
      
      if (data.sessions && data.pagination) {
        // New format with pagination
        sessionsData = data.sessions;
        paginationData = data.pagination;
        setTotalPages(paginationData.total_pages);
        setTotalSessions(paginationData.total);
      } else if (Array.isArray(data)) {
        // Fallback for old format
        sessionsData = data;
        setTotalPages(1);
        setTotalSessions(data.length);
      } else {
        sessionsData = [];
        setTotalPages(1);
        setTotalSessions(0);
      }
      
      // Map API response to component interface
      const mappedData = sessionsData.map((session: any) => ({
        id: session.id.toString(),
        program_name: session.program_name || 'Manual Control',
        start_time: session.start_time,
        end_time: session.end_time,
        status: session.status,
        operator_name: session.operator_name || null,
        roll_category_name: session.roll_category_name || null,
        sub_roll_name: session.sub_roll_name || null,
        roll_id: session.roll_id || null,
        number_of_rolls: session.number_of_rolls || null
      }));
      
      setSessions(mappedData);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      toast({
        title: "Error",
        description: "Failed to fetch sessions",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchLogsForSession = async (sessionId: string) => {
    setLoading(true);
    setSelectedSession(sessionId);
    setShowChart(false);
    
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/logs`);
      const data = await response.json();
      
      // Map API response to component interface
      const mappedData = data.map((log: any, index: number) => ({
        id: index.toString(),
        timestamp: log.timestamp,
        pressure: log.pressure,
        temperature: log.temperature,
        valve_position: log.valve_position,
        status: log.status || 'running'
      }));
      
      setLogs(mappedData);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      toast({
        title: "Error",
        description: "Failed to fetch logs",
        variant: "destructive",
      });
      setLogs([]);
    } finally {
      setLoading(false);
    }
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
      const sessionName = session?.sub_roll_name || session?.roll_category_name || 'Session';
      link.download = `${chartName}_${sessionName.replace(/\s+/g, '_')}_${format(new Date(), 'yyyyMMdd_HHmmss')}.png`;
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

  // Export function with module-level lock
  const exportToExcel = () => {
    // CRITICAL: Check module-level lock FIRST (most important check)
    if (globalExportLock) {
      console.warn('[EXPORT] Blocked by global lock');
      return; // Exit immediately - global lock is active
    }

    // Check ref (component-level check)
    if (isExportingRef.current) {
      console.warn('[EXPORT] Blocked by ref lock');
      return;
    }

    // Validate data
    if (!logs || logs.length === 0) {
      toast({
        title: "No Data",
        description: "Please select a session first",
        variant: "destructive",
      });
      return;
    }

    // Set ALL locks IMMEDIATELY - synchronous, prevents any other calls
    globalExportLock = true; // Module-level lock
    isExportingRef.current = true; // Component-level ref
    setExportingExcel(true); // Component-level state
    downloadCounter++; // Increment counter

    // Clear any existing timeout
    if (exportLockTimeout) {
      clearTimeout(exportLockTimeout);
    }

    // CRITICAL: Double-check lock before proceeding
    if (!globalExportLock || !isExportingRef.current) {
      console.error('[EXPORT] Lock was reset before execution - this should not happen!');
      return;
    }

    try {
      const session = sessions.find(s => s.id === selectedSession);
      
      // Prepare data for Excel
      const excelData = logs.map(log => ({
        'Timestamp': formatIST(log.timestamp, 'yyyy-MM-dd HH:mm:ss'),
        'Roll Category': session?.roll_category_name || 'N/A',
        'Sub-Roll Name': session?.sub_roll_name || 'N/A',
        'Roll ID': session?.roll_id || 'N/A',
        'Number of Rolls': session?.number_of_rolls || 'N/A',
        'Operator Name': session?.operator_name || 'N/A',
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
        { wch: 25 }, // Roll Category
        { wch: 25 }, // Sub-Roll Name
        { wch: 15 }, // Roll ID
        { wch: 15 }, // Number of Rolls
        { wch: 18 }, // Operator Name
        { wch: 15 }, // Pressure
        { wch: 18 }, // Temperature
        { wch: 18 }, // Valve Position
        { wch: 12 }  // Status
      ];

      // Create workbook
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Process Data');

      // Generate filename with timestamp
      const sessionName = session?.sub_roll_name || session?.roll_category_name || 'Session';
      const timestamp = format(new Date(), 'yyyyMMdd_HHmmss_SSS');
      const filename = `Process_${sessionName.replace(/\s+/g, '_')}_${timestamp}.xlsx`;

      // CRITICAL: Final check RIGHT BEFORE file write
      if (!globalExportLock) {
        console.error('[EXPORT] Global lock was reset before file write - ABORTING');
        return;
      }

      // CRITICAL: Only allow ONE download per lock cycle
      if (downloadCounter > 1) {
        console.error(`[EXPORT] Multiple download attempts detected (${downloadCounter}) - ABORTING`);
        return;
      }

      console.log(`[EXPORT] Writing file: ${filename} (Attempt #${downloadCounter})`);

      // Write file - ONLY ONCE
      XLSX.writeFile(wb, filename);

      console.log('[EXPORT] File written successfully');

      // Show toast
      toast({
        title: "Export Successful",
        description: `Downloaded ${filename}`,
      });
    } catch (error) {
      console.error('[EXPORT] Error:', error);
      toast({
        title: "Error",
        description: "Failed to export to Excel",
        variant: "destructive",
      });
    } finally {
      // Reset ALL locks after delay
      exportLockTimeout = setTimeout(() => {
        globalExportLock = false;
        isExportingRef.current = false;
        setExportingExcel(false);
        downloadCounter = 0; // Reset counter
        exportLockTimeout = null;
        console.log('[EXPORT] All locks released, counter reset');
      }, 15000); // 15 second delay - very conservative
    }
  };

  const exportToPDF = async () => {
    if (!selectedSession) {
      toast({
        title: "No Session Selected",
        description: "Please select a session first",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await fetch(`${API_URL}/sessions/${selectedSession}/pdf`, {
        method: 'GET',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to generate PDF');
      }

      // Get filename from Content-Disposition header or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `Report_Session_${selectedSession}_${format(new Date(), 'yyyyMMdd_HHmmss')}.pdf`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "PDF Generated",
        description: `Downloaded ${filename}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to generate PDF report",
        variant: "destructive",
      });
    }
  };

  const chartData = logs.map(log => ({
    time: formatIST(log.timestamp, 'HH:mm:ss'),
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
                  <TableHead>Roll Category</TableHead>
                  <TableHead>Sub-Roll Name</TableHead>
                  <TableHead>Roll ID</TableHead>
                  <TableHead>Qty</TableHead>
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
                      <TableCell className="font-medium">{session.roll_category_name || 'N/A'}</TableCell>
                      <TableCell>{session.sub_roll_name || 'N/A'}</TableCell>
                      <TableCell>{session.roll_id || 'N/A'}</TableCell>
                      <TableCell>{session.number_of_rolls || 'N/A'}</TableCell>
                      <TableCell>{formatIST(session.start_time, 'yyyy-MM-dd HH:mm')}</TableCell>
                      <TableCell>
                        {session.end_time 
                          ? formatIST(session.end_time, 'yyyy-MM-dd HH:mm')
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
          
          {/* Pagination Controls and Session Count */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              {totalPages > 1 && totalSessions > perPage ? (
                <>Showing {((currentPage - 1) * perPage) + 1} to {Math.min(currentPage * perPage, totalSessions)} of {totalSessions} sessions</>
              ) : (
                <>Total: {totalSessions} session{totalSessions !== 1 ? 's' : ''}</>
              )}
            </div>
            {totalPages > 1 && totalSessions > perPage && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1 || loading}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                        disabled={loading}
                        className="min-w-[40px]"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages || loading}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
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
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  
                  // Critical: Check global lock FIRST
                  if (globalExportLock || isExportingRef.current || exportingExcel) {
                    console.warn('[BUTTON] Click blocked - lock active');
                    return; // Exit immediately if any lock is active
                  }
                  
                  // Additional safety: Small delay to prevent rapid clicks
                  const now = Date.now();
                  const lastClick = (window as any).lastExcelClick || 0;
                  if (now - lastClick < 100) {
                    console.warn('[BUTTON] Click too rapid - blocked');
                    return;
                  }
                  (window as any).lastExcelClick = now;
                  
                  exportToExcel();
                }}
                disabled={exportingExcel || isExportingRef.current || globalExportLock}
                className="gap-2"
                type="button"
              >
                <Download className="w-5 h-5" />
                {exportingExcel || isExportingRef.current || globalExportLock ? 'Exporting...' : 'Export to Excel'}
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={exportToPDF}
                className="gap-2"
              >
                <FileText className="w-5 h-5" />
                Generate PDF Report
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
                          domain={[5, 60]}
                          ticks={[5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]}
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
                          domain={[20, 160]}
                          ticks={[20, 40, 60, 80, 100, 120, 140, 160]}
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
                        <TableCell>{formatIST(log.timestamp, 'yyyy-MM-dd HH:mm:ss')}</TableCell>
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
