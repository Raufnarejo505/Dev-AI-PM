# Quick Start Guide

## 🚀 Starting the System

### Quick Start: Command Line

Open PowerShell or Command Prompt in this directory, then run:

```bash
docker-compose up --build -d
```

---

## 📊 Check Status

After starting, check if services are running:

```bash
docker-compose ps
```

Use: `docker-compose ps`

---

## 🌐 Access the Application

Once services are running (wait 1-2 minutes):

1. **Open browser:** http://localhost:3000
2. **Login with:**
   - Email: `admin@example.com`
   - Password: `admin123`

---

## 📋 Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **AI Service:** http://localhost:8001

---

## 🛑 Stop Services

```bash
docker-compose down
```

Or press `Ctrl+C` if running in foreground

---

## 🔍 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## ⚠️ Troubleshooting

### Services Won't Start
- Make sure Docker Desktop is running
- Check ports 3000, 8000, 8001, 1883, 5432 are not in use
- Check logs: `docker-compose logs [service-name]`

### Frontend Not Loading
- Wait 1-2 minutes for services to fully start
- Check backend: http://localhost:8000/health
- Check browser console (F12) for errors

### Need Help?
- See `README.md` for detailed guide
- Check logs: `docker-compose logs [service-name]`

---

**Ready? Run `docker-compose up --build` to begin!** 🚀
