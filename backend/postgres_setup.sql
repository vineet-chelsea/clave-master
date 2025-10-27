-- PostgreSQL Setup for Autoclave Sensor Readings
-- Run this to create the database and table

-- Create database (run this as postgres user)
-- CREATE DATABASE autoclave;

-- Connect to autoclave database and run:

-- Create sensor_readings table
CREATE TABLE IF NOT EXISTS public.sensor_readings (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  pressure DECIMAL(10, 2) NOT NULL,
  temperature DECIMAL(10, 2) NOT NULL
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
  ON public.sensor_readings(timestamp DESC);

-- Grant access (optional, depending on your setup)
-- GRANT ALL ON sensor_readings TO postgres;
-- GRANT ALL ON SEQUENCE sensor_readings_id_seq TO postgres;

-- Verify table exists
SELECT * FROM sensor_readings LIMIT 5;

