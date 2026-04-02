# 🚀 Quick Start Guide - Temple Crowd Management System

## Prerequisites

1. **Python Virtual Environment** (already set up in `venv/`)
2. **Node.js** (for frontend)
3. **Python packages** (Flask, YOLO, etc.)

## Step-by-Step Run Instructions

### 1️⃣ Start Flask Backend (Port 5001)

Open Terminal 1:
```bash
cd /Users/tharunkumar/Desktop/temple_crowd_project
source venv/bin/activate

# Install flask-cors if not already installed (optional, has fallback)
pip install flask-cors

# Start Flask backend
python yolo_processor_mongo.py
```

**Expected Output:**
```
✅ Loaded environment variables from .env file
✅ MongoDB connected successfully (or ⚠️ NOT CONNECTED if offline)
✅ YOLO + Mongo Backend Started
📡 API running on http://localhost:5001
✅ Created default users: operator/operator123, admin/admin123
```

**Keep this terminal running!**

---

### 2️⃣ Start Frontend (React/Vite)

Open Terminal 2:
```bash
cd /Users/tharunkumar/Desktop/temple_crowd_project/temple-watch-main

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Open browser:** http://localhost:5173

**Keep this terminal running!**

---

### 3️⃣ Start Streamlit Dashboard (Port 8501)

Open Terminal 3:
```bash
cd /Users/tharunkumar/Desktop/temple_crowd_project
source venv/bin/activate

# Start Streamlit
streamlit run app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://...
```

**Keep this terminal running!**

---

## 🎯 How to Use

### Operator Login
1. Go to http://localhost:5173
2. Select **Operator** role
3. Username: `operator`
4. Password: `operator123`
5. Click **Sign In**
6. You'll see:
   - Live video feeds from all zones
   - Real-time crowd counts
   - Status indicator (NORMAL/WARNING/OVERCROWDED)

### Admin Login
1. Go to http://localhost:5173
2. Select **Admin** role
3. Username: `admin`
4. Password: `admin123`
5. Click **Sign In**
6. Click any section button to open Streamlit dashboard:
   - **Dashboard** → Overview
   - **Crowd Monitoring** → Live monitoring
   - **Heatmap Analysis** → Heatmap view
   - **Analytics & Trends** → Historical data
   - **Threshold Settings** → Configure thresholds

---

## ✅ Verification Checklist

### Backend Running?
```bash
curl http://localhost:5001/live_counts
```
Should return JSON with zone counts.

### Frontend Running?
Visit http://localhost:5173 - should show login page.

### Streamlit Running?
Visit http://localhost:8501 - should show Streamlit dashboard.

---

## 🔧 Troubleshooting

### "Failed to connect to server" on login
- ✅ Check Flask backend is running on port 5001
- ✅ Check terminal 1 for errors

### Video feeds not showing
- ✅ Check Flask backend is processing videos
- ✅ Check `latest_frame_*.jpg` files are being created in project root
- ✅ Verify video sources in `yolo_processor_mongo.py`

### Streamlit not loading data
- ✅ Check Flask backend is running
- ✅ Check API_BASE in `app.py` is `http://localhost:5001`

### CORS errors
- ✅ Install flask-cors: `pip install flask-cors`
- ✅ Or use the manual CORS fallback (already implemented)

---

## 📝 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Operator | `operator` | `operator123` |
| Admin | `admin` | `admin123` |

---

## 🎬 All Systems Running?

You should have **3 terminals running**:
1. ✅ Flask backend (port 5001)
2. ✅ Frontend dev server (port 5173)
3. ✅ Streamlit dashboard (port 8501)

**Ready to monitor temple crowd!** 🛕
