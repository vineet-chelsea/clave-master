# Quick Deployment Checklist - Raspberry Pi

## Pre-Deployment
- [ ] SSH into Raspberry Pi
- [ ] Navigate to project directory
- [ ] Create backup (git branch or directory copy)

## Deployment Steps
- [ ] `git pull origin main` - Pull latest changes
- [ ] `cd backend && pip3 install -r requirements.txt` - Update Python packages
- [ ] `cd .. && npm install` - Update npm packages
- [ ] Stop running services (kill processes or systemctl stop)
- [ ] Verify serial port permissions (`/dev/ttyACM0` accessible)
- [ ] Check `.env` file configuration
- [ ] Start sensor control service
- [ ] Start API server
- [ ] Build/restart frontend (if needed)

## Verification
- [ ] `curl http://localhost:5000/api/health` - API responds
- [ ] Check service logs for errors
- [ ] Test PDF report generation
- [ ] Verify IST timezone in frontend
- [ ] Test buzzer activation (if possible)
- [ ] Verify temperature readings

## New Dependencies Added
- Python: `reportlab`, `matplotlib`, `pytz`
- npm: `date-fns-tz`

## Key Files Changed
- `backend/sensor_control_service.py` - Buzzer, temperature adjustment, IST
- `backend/api_server.py` - PDF generation, IST timezone
- `backend/requirements.txt` - New dependencies
- `package.json` - date-fns-tz
- Frontend components - IST timezone support

## Rollback Command
```bash
git checkout <previous-commit-hash>
sudo systemctl restart sensor-control-service api-server
```

