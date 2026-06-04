# PPE Detection Dashboard - Quick Reference

## 🚀 Quick Start

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
bash start.sh
```

### Manual Start (Any OS)

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm start
```

Dashboard opens at: **http://localhost:3000**

---

## 📊 Dashboard Features

| Feature | Details |
|---------|---------|
| **Live Streaming** | Real-time video from webcam or video file |
| **Multi-Camera** | Monitor multiple cameras simultaneously |
| **PPE Detection** | Hardhat, Mask, Safety Vest detection |
| **Alert System** | Real-time notifications for safety violations |
| **Statistics** | Detection counts, charts, and analytics |
| **Responsive UI** | Works on desktop, tablet, mobile |

---

## 🎥 Adding Cameras

1. Open dashboard (http://localhost:3000)
2. Scroll to "Add Camera"
3. Enter:
   - **Camera ID**: Unique name (e.g., "Main Gate")
   - **Source**: 
     - `0` = Default webcam
     - `1`, `2` = Other USB cameras
     - `/path/to/video.mp4` = Video file
     - `rtsp://camera-ip` = IP camera
4. Click "Add Camera"

---

## 🔧 Configuration

### Change Detection Threshold
Edit `backend/app.py` line 28:
```python
results = model(frame, conf=0.5)[0]  # Change 0.5 to 0.3-0.9
```

### Change Backend Port
Edit `backend/app.py` last line:
```python
socketio.run(app, host='0.0.0.0', port=5000)  # Change 5000
```

### Change Frontend Port
In `frontend/`, run:
```bash
PORT=3001 npm start
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Python is installed: `python --version` |
| Can't connect frontend to backend | Ensure backend running on :5000, check firewall |
| Webcam not working | Try source `1` or `2`, check camera is not in use |
| High memory usage | Reduce number of cameras, restart backend |
| Slow frame rate | Use `conf=0.7` for faster detection |

---

## 📁 Project Structure

```
.
├── backend/                    # Flask server
│   ├── app.py                 # Main application
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile             # Docker config
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── App.js            # Main dashboard component
│   │   ├── App.css           # Styles
│   │   └── index.js          # Entry point
│   ├── package.json          # JS dependencies
│   ├── Dockerfile            # Docker config
│   └── nginx.conf            # Nginx config
├── models/                     # YOLOv8 model
│   └── best.pt               # Trained model
├── start.bat                  # Windows quick start
├── start.sh                   # Linux/Mac quick start
└── docker-compose.yml        # Docker setup

```

---

## 🌐 API Endpoints

```
GET  /cameras              - List all cameras
POST /cameras              - Add new camera
DEL  /cameras/<id>         - Remove camera
GET  /stats                - Get all statistics
GET  /stats/<id>           - Get camera statistics
GET  /video_feed/<id>      - Stream video
```

---

## 🐳 Docker (Optional)

```bash
# Build and start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📝 Example Use Cases

1. **Single Site Monitoring**
   - Add 1 webcam
   - Monitor workers entering/exiting

2. **Multi-Site Supervision**
   - Add cameras from 3 construction sites
   - Switch between sites in dashboard
   - Get unified alerts

3. **Recording & Playback**
   - Add video file as source
   - Review footage with PPE detection

---

## 🚨 Safety Violation Alerts

The system detects and alerts on:
- ❌ **NO-Hardhat** - No hard hat detected
- ❌ **NO-Mask** - No face mask detected  
- ❌ **NO-Safety Vest** - No safety vest detected

Green box = Safe ✅  
Red box = Danger ⚠️

---

## 📞 Support

For issues:
1. Check terminal output for error messages
2. Verify all prerequisites are installed
3. Check browser console (F12) for frontend errors
4. Ensure camera is not being used by another app

Happy monitoring! 🎥🛡️
