# Running on Different Port (When Port 80 is Already in Use)

## ⚠️ Important: Don't Stop Other Person's Project

Instead of stopping their project, run your project on a different port (e.g., 3000 or 8080).

## Option 1: Run on Port 3000 (Recommended)

### Step 1: Check what's using port 80

```bash
# See what's using port 80
netstat -tulpn | grep :80
# OR
ss -tulpn | grep :80
# OR
lsof -i :80
```

### Step 2: Modify docker-compose.prod.yml

Change the frontend port mapping from `80:80` to `3000:80`:

```yaml
frontend:
  # ... other config ...
  ports:
    - "3000:80"  # Changed from "80:80"
    # - "443:443"  # Keep commented if no SSL
```

### Step 3: Restart frontend

```bash
docker compose -f docker-compose.prod.yml up -d frontend
```

### Step 4: Access your application

- **Frontend**: http://37.120.176.43:3000
- **Backend API**: http://37.120.176.43:3000/api
- **API Docs**: http://37.120.176.43:3000/api/docs

## Option 2: Run on Port 8080

Same process, but use port 8080:

```yaml
frontend:
  ports:
    - "8080:80"
```

Access at: http://37.120.176.43:8080

## Option 3: Use a Subdomain (If You Have DNS Access)

If you have DNS control, you can:
1. Point a subdomain to the same IP
2. Configure nginx reverse proxy to route based on domain
3. Keep both projects running on port 80

## ⚠️ If You MUST Stop the Other Project (Only with Permission)

**ONLY do this if you have explicit permission from the other person!**

### Check what's running

```bash
# Check all running containers
docker ps

# Check system services
systemctl list-units --type=service --state=running | grep -E 'apache|nginx|httpd'

# Check what's using port 80
netstat -tulpn | grep :80
```

### Stop Apache (if running)

```bash
systemctl stop apache2
systemctl disable apache2  # Prevent auto-start
```

### Stop Nginx (if running)

```bash
systemctl stop nginx
systemctl disable nginx  # Prevent auto-start
```

### Stop Docker containers (if other project uses Docker)

```bash
# List all containers
docker ps -a

# Stop specific container (replace CONTAINER_NAME)
docker stop CONTAINER_NAME

# Or stop all containers (DANGEROUS - stops everything!)
docker stop $(docker ps -q)
```

## Recommended Solution: Use Port 3000

**Best approach**: Modify your `docker-compose.prod.yml` to use port 3000 instead of 80. This way:
- ✅ You don't disrupt the other person's project
- ✅ Both projects can run simultaneously
- ✅ No conflicts
- ✅ Easy to access: http://your-server-ip:3000

## Quick Fix Commands

```bash
# 1. Edit docker-compose.prod.yml
nano docker-compose.prod.yml

# 2. Change frontend ports from "80:80" to "3000:80"

# 3. Restart frontend
docker compose -f docker-compose.prod.yml up -d frontend

# 4. Verify
curl http://localhost:3000/health
```

---

**Remember**: Always coordinate with the other person before stopping their services!

