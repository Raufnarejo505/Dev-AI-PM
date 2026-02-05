# Step-by-Step Deployment on Netcup Server

## Current Status
✅ Files uploaded to `/root/Predictive Maintenance/` on server `37.120.176.43`

## Next Steps

### Method 1: Using WinSCP Console (Easiest)

1. **In WinSCP, click the "Console" button** (you already have it open)

2. **Run these commands one by one:**

```bash
# Navigate to project directory
cd "/root/Predictive Maintenance"

# Check current directory
pwd

# List files to verify upload
ls -la
```

3. **Check if Docker is installed:**

```bash
docker --version
docker compose version
```

**If Docker is NOT installed**, run:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose-plugin -y
```

4. **Create environment file:**

```bash
cp backend/env.example backend/.env
```

5. **Generate JWT Secret:**

```bash
openssl rand -hex 32
```

**Copy the output** (it will look like: `a1b2c3d4e5f6...`)

6. **Edit environment file:**

```bash
nano backend/.env
```

**In the nano editor:**
- Find the line: `JWT_SECRET=change-me`
- Replace with: `JWT_SECRET=<paste-your-generated-secret>`
- Find: `POSTGRES_PASSWORD=pm_pass`
- Change to: `POSTGRES_PASSWORD=YourStrongPassword123!`
- Save: Press `Ctrl+X`, then `Y`, then `Enter`

7. **Make deployment script executable:**

```bash
chmod +x deploy-netcup.sh
```

8. **Run deployment:**

```bash
./deploy-netcup.sh
```

**OR manually:**

```bash
# Build all services
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d
```

9. **Wait for services to start (30-60 seconds), then check status:**

```bash
docker compose -f docker-compose.prod.yml ps
```

**All services should show "Up" status**

10. **Check backend health:**

```bash
curl http://localhost/health
```

**Expected output:** `{"status":"ok",...}`

11. **Seed demo data (optional):**

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

12. **View logs (if needed):**

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

### Method 2: Using SSH (Alternative)

If WinSCP console doesn't work well, use SSH:

1. **Open PowerShell or Command Prompt on your Windows machine**

2. **Connect via SSH:**
```bash
ssh root@37.120.176.43
```

3. **Then run all the commands from Method 1**

## Verification

After deployment, test these URLs:

- **Frontend**: http://37.120.176.43
- **Backend API**: http://37.120.176.43/api
- **API Docs**: http://37.120.176.43/api/docs
- **Health Check**: http://37.120.176.43/health

## Common Issues

### "Command not found: docker"
- Docker is not installed
- Run: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`

### "Permission denied"
- Make script executable: `chmod +x deploy-netcup.sh`
- Or use: `bash deploy-netcup.sh` instead

### "Port already in use"
- Check what's using port 80: `netstat -tulpn | grep :80`
- Stop conflicting service: `systemctl stop apache2` or `systemctl stop nginx`

### Services won't start
- Check logs: `docker compose -f docker-compose.prod.yml logs`
- Check disk space: `df -h`
- Check memory: `free -h`

## Quick Commands Reference

```bash
# View service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml stop

# Rebuild after code changes
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Access Your Application

Once deployed, access at:
- **http://37.120.176.43**
- Login with: `admin@example.com` / `admin123`

---

**Note**: The WinSCP console is perfect for running these commands. Just copy-paste each command and press Enter.

