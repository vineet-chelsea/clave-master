# Quick Docker Deployment Checklist - Raspberry Pi

## Pre-Deployment
- [ ] SSH into Raspberry Pi
- [ ] Navigate to project directory
- [ ] Backup docker-compose.yml

## Deployment Steps
- [ ] `git pull origin main` - Pull latest changes
- [ ] `docker-compose down` - Stop all containers
- [ ] `docker-compose build --no-cache` - Rebuild images with new dependencies
- [ ] `docker-compose up -d` - Start all containers
- [ ] `docker-compose ps` - Verify all containers are running
- [ ] `docker-compose logs -f` - Check logs for errors

## Verification
- [ ] `curl http://localhost:5000/api/health` - API responds
- [ ] `curl http://localhost` - Frontend accessible
- [ ] Check container status: `docker-compose ps`
- [ ] Test PDF report generation
- [ ] Verify IST timezone in frontend
- [ ] Check database: `docker-compose exec postgres psql -U postgres -d autoclave`
- [ ] **Add all programs:** `docker-compose exec backend python3 add_all_25_programs.py`

## Quick Commands

```bash
# Full deployment
git pull && docker-compose down && docker-compose build --no-cache && docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart specific service
docker-compose restart backend

# Check status
docker-compose ps

# Stop everything
docker-compose down
```

## New Dependencies (Auto-installed in Docker)
- Python: reportlab, matplotlib, pytz
- npm: date-fns-tz

## Troubleshooting
- Container won't start → Check logs: `docker-compose logs backend`
- Serial device error → Verify `/dev/ttyACM0` exists
- Port conflict → Check: `sudo netstat -tulpn | grep 5000`
- Database issues → Check: `docker-compose logs postgres`

