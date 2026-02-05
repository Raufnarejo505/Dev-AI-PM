# Quick Deployment Guide - Netcup Server

## ✅ Project Compatibility

**YES - This project runs perfectly on Netcup Linux servers!**

- ✅ All Dockerfiles use Linux commands (no Windows dependencies)
- ✅ Docker Compose works on Linux
- ✅ Production configuration already included
- ✅ No code changes needed

**WinSCP** is just a file transfer tool - you use it to upload files, then run commands via SSH.

## 🚀 Quick Deployment (5 Steps)

### Step 1: Upload Files to Netcup Server

**Using WinSCP:**
1. Connect to your Netcup server (SFTP)
2. Upload entire project folder to `/opt/predictive-maintenance` (or any directory)

**Using SSH/SCP:**
```bash
scp -r "Predictive Maintenance" root@your-server-ip:/opt/predictive-maintenance
```

### Step 2: Connect via SSH

```bash
ssh root@your-server-ip
cd /opt/predictive-maintenance
```

### Step 3: Install Docker (if not installed)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose-plugin -y
```

### Step 4: Configure Environment

```bash
cp backend/env.example backend/.env
nano backend/.env
# Edit: JWT_SECRET, POSTGRES_PASSWORD (use strong values)
```

### Step 5: Deploy

```bash
# Make deployment script executable
chmod +x deploy-netcup.sh

# Run deployment script
./deploy-netcup.sh

# OR manually:
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## 📋 What's Different for Production?

The `docker-compose.prod.yml` file is already configured with:

- ✅ Database port hidden (internal only)
- ✅ AI service port hidden (internal only)  
- ✅ Backend accessed via nginx only
- ✅ Frontend on ports 80/443
- ✅ Health checks enabled
- ✅ Production nginx config
- ✅ Simulator disabled (commented out)

## 🔧 Required Changes

**Only 2 things you MUST change:**

1. **JWT_SECRET** in `backend/.env`:
   ```bash
   # Generate strong secret:
   openssl rand -hex 32
   # Add to backend/.env: JWT_SECRET=your-generated-secret
   ```

2. **POSTGRES_PASSWORD** in `backend/.env`:
   ```bash
   # Use strong password
   POSTGRES_PASSWORD=your-strong-password-here
   ```

## 🌐 Access After Deployment

- **Frontend**: http://your-server-ip
- **Backend API**: http://your-server-ip/api
- **API Docs**: http://your-server-ip/api/docs

## 📚 Full Documentation

See `NETCUP_DEPLOYMENT.md` for complete deployment guide.

## ⚠️ Important Notes

1. **WinSCP is only for file transfer** - actual deployment runs on Linux server
2. **All commands run via SSH** on the Netcup server
3. **No code changes needed** - project is Linux-compatible
4. **Use `docker-compose.prod.yml`** for production (not `docker-compose.yml`)

---

**That's it! The project is ready for Netcup deployment.** 🎉

