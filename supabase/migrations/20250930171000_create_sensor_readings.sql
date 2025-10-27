-- Create table for realtime sensor readings
CREATE TABLE public.sensor_readings (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  pressure DECIMAL(10, 2) NOT NULL,
  temperature DECIMAL(10, 2) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;

-- Create policies for public access
CREATE POLICY "Anyone can view sensor readings" ON public.sensor_readings FOR SELECT USING (true);
CREATE POLICY "Anyone can insert sensor readings" ON public.sensor_readings FOR INSERT WITH CHECK (true);

-- Create index for performance
CREATE INDEX idx_sensor_readings_timestamp ON public.sensor_readings(timestamp DESC);

-- Enable realtime for sensor readings
ALTER PUBLICATION supabase_realtime ADD TABLE public.sensor_readings;
