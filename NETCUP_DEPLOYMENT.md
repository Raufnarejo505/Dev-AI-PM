# Netcup Server Deployment Guide

This guide explains how to deploy the Predictive Maintenance Platform to a Netcup VPS server.

## ✅ Compatibility

**The project is fully compatible with Linux servers (including Netcup VPS):**
- ✅ All Dockerfiles use Linux commands
- ✅ Docker Compose works on Linux
- ✅ No Windows-specific dependencies
- ✅ Production configuration already included (`docker-compose.prod.yml`)

## Prerequisites

### Netcup VPS Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+ (recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: Minimum 20GB SSD
- **Docker**: Docker Engine 20.10+
- **Docker Compose**: Version 2.0+
- **Ports**: 80, 443, 1883 (or configure firewall)

### Server Setup

1. **Connect to Netcup VPS via SSH**:
   ```bash
   ssh root@your-netcup-server-ip
   ```

2. **Update system**:
   ```bash
   apt update && apt upgrade -y
   ```

3. **Install Docker**:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   apt install docker-compose-plugin -y
   
   # Verify installation
   docker --version
   docker compose version
   ```

4. **Configure firewall** (if enabled):
   ```bash
   # Allow required ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 1883/tcp  # MQTT (optional, can be internal only)
   ufw allow 22/tcp    # SSH
   ```

## Deployment Steps

### Step 1: Upload Project Files

**Option A: Using WinSCP (Windows)**

1. Open WinSCP
2. Connect to your Netcup server:
   - Host: `your-server-ip`
   - Username: `root` (or your username)
   - Password: Your server password
   - Protocol: SFTP
3. Navigate to `/opt` or `/home/your-user`
4. Create directory: `predictive-maintenance`
5. Upload entire project folder:
   - Select all files and folders
   - Drag and drop to server
   - Wait for upload to complete

**Option B: Using Git (Recommended)**

```bash
# On Netcup server
cd /opt
git clone <your-repository-url> predictive-maintenance
cd predictive-maintenance
```

**Option C: Using SCP Command**

```bash
# From your local machine
scp -r "Predictive Maintenance" root@your-server-ip:/opt/predictive-maintenance
```

### Step 2: Configure Environment

```bash
# Navigate to project directory
cd /opt/predictive-maintenance

# Copy environment example
cp backend/env.example backend/.env

# Edit environment file
nano backend/.env
```

**Required Changes in `backend/.env`**:

```bash
# Database (use strong passwords in production)
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_USER=pm_user
POSTGRES_DB=pm_db

# JWT (MUST CHANGE - use strong random secret)
JWT_SECRET=generate-strong-random-secret-here
# Generate with: openssl rand -hex 32

# AI Service
AI_SERVICE_URL=http://ai-service:8000

# MQTT
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883

# Email (Optional - configure if needed)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASS=your-gmail-app-password
NOTIFICATION_EMAIL_TO=recipient@example.com
```

### Step 3: Configure Production Docker Compose

The `docker-compose.prod.yml` is already configured for production. Review and adjust if needed:

```bash
# Review production config
cat docker-compose.prod.yml
```

**Key Production Settings**:
- Database port not exposed (internal only)
- AI service port not exposed (internal only)
- Backend port not exposed (via nginx only)
- Frontend on ports 80/443
- Health checks enabled
- Restart policies set

### Step 4: Build and Start Services

```bash
# Navigate to project root
cd /opt/predictive-maintenance

# Build all services
docker compose -f docker-compose.prod.yml build

# Start services in background
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### Step 5: Wait for Initialization

Wait 1-2 minutes for services to initialize:

```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend

# Check if database is ready
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U pm_user

# Check backend health
curl http://localhost:8000/health
```

### Step 6: Seed Demo Data (Optional)

```bash
# Seed demo users and sample data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### Step 7: Configure Domain & SSL (Optional)

**If you have a domain name:**

1. **Point domain to server IP**:
   - Add A record: `yourdomain.com` → `your-server-ip`
   - Add A record: `www.yourdomain.com` → `your-server-ip`

2. **Install Certbot for SSL**:
   ```bash
   apt install certbot python3-certbot-nginx -y
   ```

3. **Update nginx configuration**:
   - Edit `frontend/nginx.prod.conf`
   - Add your domain name
   - Configure SSL certificates

4. **Obtain SSL certificate**:
   ```bash
   certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## Verification

### Check All Services

```bash
# Service status
docker compose -f docker-compose.prod.yml ps

# All should show "Up" status
```

### Test Endpoints

```bash
# Backend health
curl http://localhost/health

# System status
curl http://localhost/status

# Frontend (should load)
curl http://localhost
```

### Access Application

- **Frontend**: http://your-server-ip (or http://yourdomain.com)
- **Backend API**: http://your-server-ip/api (or http://yourdomain.com/api)
- **API Docs**: http://your-server-ip/api/docs

## Maintenance Commands

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Update Application

```bash
# Pull latest code (if using Git)
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
# Stop services
docker compose -f docker-compose.prod.yml stop

# Stop and remove containers
docker compose -f docker-compose.prod.yml down
```

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U pm_user pm_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose -f docker-compose.prod.yml exec -T postgres psql -U pm_user pm_db < backup_20251209.sql
```

## Security Considerations

### 1. Change Default Passwords

- Database password
- JWT secret (use strong random value)
- Email credentials

### 2. Firewall Configuration

```bash
# Only allow necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 3. Disable Simulator in Production

The simulator is already disabled in `docker-compose.prod.yml` (commented out). For real deployments, use actual sensor devices.

### 4. Use Environment Variables

Never commit `.env` files. Use environment variables or secrets management.

### 5. Regular Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check memory
free -h

# Check Docker
docker system df
docker system prune  # Clean up if needed
```

### Port Conflicts

```bash
# Check what's using ports
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Stop conflicting services
systemctl stop apache2  # If Apache is running
systemctl stop nginx    # If nginx is running
```

### Database Issues

```bash
# Check database logs
docker compose -f docker-compose.prod.yml logs postgres

# Access database
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db

# Check connections
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Frontend Not Loading

```bash
# Check nginx logs
docker compose -f docker-compose.prod.yml logs frontend

# Check if frontend container is running
docker compose -f docker-compose.prod.yml ps frontend

# Rebuild frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

## Performance Optimization

### Resource Limits

Add to `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Database Optimization

```bash
# Access database
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db

# Create indexes (if needed)
CREATE INDEX idx_sensor_data_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_sensor_data_sensor_id ON sensor_data(sensor_id);
```

## Monitoring

### Set Up Log Rotation

```bash
# Create logrotate config
cat > /etc/logrotate.d/docker-containers << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
EOF
```

### Monitor Resources

```bash
# Docker stats
docker stats

# System resources
htop

# Disk usage
df -h
du -sh /var/lib/docker
```

## Quick Reference

### Essential Commands

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d

# Stop services
docker compose -f docker-compose.prod.yml stop

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Rebuild after code changes
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# Execute commands
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db
```

## Support

For issues:
1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Check service status: `docker compose -f docker-compose.prod.yml ps`
3. Verify network: `docker network ls`
4. Check system resources: `htop`, `df -h`

---

**Note**: WinSCP is only a file transfer tool. The actual deployment runs on the Netcup Linux server using Docker. All commands should be executed on the server via SSH, not in WinSCP.

