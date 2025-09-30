-- Create table for storing autoclave programs
CREATE TABLE public.autoclave_programs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  program_number INTEGER NOT NULL UNIQUE CHECK (program_number >= 1 AND program_number <= 20),
  program_name TEXT NOT NULL,
  description TEXT,
  steps JSONB NOT NULL, -- Array of {psi_range: string, duration_minutes: number}
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create table for process logging
CREATE TABLE public.process_logs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID NOT NULL,
  program_id UUID REFERENCES public.autoclave_programs(id),
  program_name TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  pressure DECIMAL(10, 2) NOT NULL,
  temperature DECIMAL(10, 2) NOT NULL,
  valve_position DECIMAL(5, 2), -- 4-20mA represented as percentage
  status TEXT NOT NULL -- 'running', 'paused', 'stopped', 'completed'
);

-- Create table for process sessions
CREATE TABLE public.process_sessions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  program_id UUID REFERENCES public.autoclave_programs(id),
  program_name TEXT NOT NULL,
  start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  end_time TIMESTAMP WITH TIME ZONE,
  status TEXT NOT NULL DEFAULT 'running', -- 'running', 'paused', 'stopped', 'completed'
  operator_name TEXT
);

-- Enable Row Level Security
ALTER TABLE public.autoclave_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.process_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.process_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (since this is an industrial control system)
CREATE POLICY "Anyone can view programs" ON public.autoclave_programs FOR SELECT USING (true);
CREATE POLICY "Anyone can insert programs" ON public.autoclave_programs FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update programs" ON public.autoclave_programs FOR UPDATE USING (true);

CREATE POLICY "Anyone can view logs" ON public.process_logs FOR SELECT USING (true);
CREATE POLICY "Anyone can insert logs" ON public.process_logs FOR INSERT WITH CHECK (true);

CREATE POLICY "Anyone can view sessions" ON public.process_sessions FOR SELECT USING (true);
CREATE POLICY "Anyone can insert sessions" ON public.process_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update sessions" ON public.process_sessions FOR UPDATE USING (true);

-- Insert sample programs based on the provided example
INSERT INTO public.autoclave_programs (program_number, program_name, description, steps) VALUES
(1, 'Standard Sterilization', 'Standard cycle for general sterilization', 
 '[
   {"psi_range": "5-10", "duration_minutes": 15, "action": "raise"},
   {"psi_range": "10", "duration_minutes": 75, "action": "steady"},
   {"psi_range": "20-25", "duration_minutes": 15, "action": "raise"},
   {"psi_range": "20-25", "duration_minutes": 30, "action": "steady"},
   {"psi_range": "40-45", "duration_minutes": 15, "action": "raise"},
   {"psi_range": "40-45", "duration_minutes": 120, "action": "steady"}
 ]'::jsonb);

-- Create indexes for performance
CREATE INDEX idx_process_logs_session_id ON public.process_logs(session_id);
CREATE INDEX idx_process_logs_timestamp ON public.process_logs(timestamp DESC);
CREATE INDEX idx_process_sessions_status ON public.process_sessions(status);

-- Enable realtime for process logs
ALTER PUBLICATION supabase_realtime ADD TABLE public.process_logs;