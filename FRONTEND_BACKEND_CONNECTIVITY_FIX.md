# Frontend-Backend Connectivity Fix

## Problem
Frontend was not connecting to backend because:
1. Hardcoded `localhost:5000` URLs in frontend components
2. No API proxying from Nginx to backend container
3. Environment variables not passed during Docker build

## Solution Implemented

### 1. Centralized API URL Configuration
- Updated `src/integrations/supabase/client.ts` to export `API_URL` constant
- Uses `import.meta.env.VITE_API_BASE_URL` for Docker builds
- Falls back to `http://localhost:5000` for local development

### 2. Nginx API Proxy
- Updated `nginx.conf` to proxy `/api/` requests to backend container
- Uses Docker service name `backend:5000` for internal networking
- All API requests from frontend now route through Nginx

### 3. Updated All Frontend Components
- `src/pages/Index.tsx`: Uses `API_URL` constant
- `src/components/ProcessMonitor.tsx`: Uses `API_URL` constant
- `src/components/ProgramSelection.tsx`: Uses `API_URL` constant
- `src/components/HistoricalData.tsx`: Uses `API_URL` constant

### 4. Docker Configuration
- `docker-compose.yml`: Passes `VITE_API_BASE_URL` during build
- `Dockerfile.frontend`: Accepts build args for API URL
- Built with `npm run build` using the environment variable

## How It Works

### Local Development (PC)
- Frontend runs on `localhost:8080` (Vite dev server)
- Backend runs on `localhost:5000` (Flask API)
- Frontend directly calls `localhost:5000/api/*`
- No Docker involved

### Docker Deployment (Raspberry Pi)
- Frontend container runs Nginx on port 80
- Backend container runs Flask on port 5000
- Nginx proxies `/api/*` → `backend:5000/api/*`
- Frontend JavaScript calls `/api/*` (relative URLs)
- Nginx handles routing internally

## Testing

### Local Testing
```bash
# Terminal 1: Start backend
cd backend
python api_server.py
python sensor_control_service.py

# Terminal 2: Start frontend
cd ..  # to root directory
npm run dev
# Open http://localhost:8080
```

### Docker Testing
```bash
# Build and start all services
docker compose up -d --build

# Check logs
docker compose logs frontend
docker compose logs backend

# Access application
# From Raspberry Pi: http://localhost
# From network: http://<raspberry-pi-ip>
```

## Status
✅ Fixed - Frontend now correctly connects to backend in both local and Docker environments

