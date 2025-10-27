-- Create autoclave_programs table
CREATE TABLE IF NOT EXISTS autoclave_programs (
    id SERIAL PRIMARY KEY,
    program_number INTEGER NOT NULL UNIQUE,
    program_name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,  -- Array of step objects
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_program_number ON autoclave_programs(program_number);

