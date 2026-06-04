# PPE Detection Dashboard - Setup Guide

A real-time surveillance dashboard for construction site safety monitoring with live PPE detection powered by YOLOv8.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Dashboard (Port 3000)                 │
│     - Live video feeds                                          │
│     - Real-time alerts & notifications                          │
│     - Statistics & charts                                       │
│     - Multiple camera management                                │
└─────────────────────────────────────────────────────────────────┘
              │                                       │
              │ HTTP + WebSocket                      │
              │                                       │
┌─────────────────────────────────────────────────────────────────┐
│                  Flask Backend (Port 5000)                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         YOLOv8 PPE Detection Engine                      │  │
│  │  Multi-threaded camera streams + detection processing   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Stream Manager                                   │  │
│  │  Handles multiple cameras, statistics, real-time events │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
              │                   │                  │
              │                   │                  │
         Webcam (0)          Video File          IP Camera
```

## Features

✅ **Live Video Streaming** - Multi-camera support with real-time video feed
✅ **PPE Detection** - Detects: Hardhat, Mask, Safety Vest, and missing PPE
✅ **Real-time Alerts** - Instant notifications for safety violations  
✅ **Statistics Dashboard** - Detection counts, charts, and analytics
✅ **Multiple Cameras** - Manage multiple surveillance cameras
✅ **Responsive UI** - Works on desktop, tablet, and mobile

## Installation

### Prerequisites
- Python 3.8+
- Node.js 14+ and npm
- 4GB RAM (8GB+ recommended for smooth processing)
- Webcam or video source

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Run the backend server:**
```bash
python app.py
```
- Backend will start at `http://localhost:5000`
- Models will be loaded automatically

### Frontend Setup

1. **Install Node dependencies:**
```bash
cd ../frontend
npm install
```

2. **Start the React development server:**
```bash
npm start
```
- Dashboard will open at `http://localhost:3000`

### Docker Setup (Optional)

**Run both services with Docker Compose:**

```bash
docker-compose up -d
```

This starts:
- Backend: `http://localhost:5000`
- Frontend: `http://localhost:3000`

---

## Usage

### 1. Connect a Camera

1. Open the dashboard at `http://localhost:3000`
2. In "Add Camera" section:
   - **Camera ID**: Give it a name (e.g., "Main Gate", "Entrance")
   - **Source**: 
     - `0` for default webcam
     - `1`, `2`, etc. for other connected USB cameras
     - `/path/to/video.mp4` for video files
     - `rtsp://stream.url` for IP cameras
3. Click "Add Camera"

### 2. Monitor Live Feed

- Select a camera from the list
- Watch real-time video with PPE detection annotations
- Green boxes = Safe (proper PPE detected)
- Red boxes = Safety violation (missing PPE)

### 3. View Alerts

- Alerts appear in the "Recent Alerts" section
- Red badges show count of missing PPE items
- Click alert for more details

### 4. Check Statistics

- **Total Detections**: All objects detected in current session
- **Safe Items**: Workers with proper PPE
- **Missing PPE**: Safety violations (no hardhat, mask, vest)
- **Detection Breakdown**: Pie chart of all detections by class
- **Detection Classes**: Table summary of each PPE type

---

## API Endpoints

### GET `/cameras`
List all connected cameras
```json
{"cameras": ["MainGate", "Entrance", "Exit"]}
```

### POST `/cameras`
Add a new camera
```json
{
  "camera_id": "MainGate",
  "source": 0
}
```

### DELETE `/cameras/<camera_id>`
Remove a camera

### GET `/stats`
Get statistics for all cameras
```json
{
  "MainGate": {
    "total_detections": 150,
    "detections_by_class": {
      "Hardhat": 100,
      "NO-Hardhat": 10,
      "Person": 120
    },
    "recent_alerts": [...]
  }
}
```

### GET `/stats/<camera_id>`
Get statistics for specific camera

### GET `/video_feed/<camera_id>`
Stream video feed (MJPEG format)

---

## WebSocket Events

**Client receives:**
- `alert` - Safety violation detected
- `detection` - Objects detected in frame
- `camera_added` - New camera connected
- `camera_removed` - Camera disconnected

---

## Troubleshooting

### Backend won't start
```
Error: Cannot open webcam
→ Solution: Ensure no other app is using the camera. Try source: 1 or 2
```

### Frontend can't connect to backend
```
Error: Connection refused on localhost:5000
→ Solution: 
  1. Make sure backend is running: python backend/app.py
  2. Check if port 5000 is not blocked by firewall
  3. Try: http://localhost:5000 in browser
```

### Video feed not loading
```
→ Solution: 
  1. Check camera connection
  2. Verify source parameter (0 for webcam)
  3. Check system permissions for camera access
```

### Memory usage high
```
→ Solution:
  1. Reduce number of cameras
  2. Lower video resolution
  3. Restart backend service
```

---

## Configuration

Edit `backend/app.py` to customize:

```python
# Line 28 - Model confidence threshold (0-1)
results = model(frame, conf=0.5)[0]

# Line 74 - Frame capture interval (milliseconds)
if cv2.waitKey(5000) & 0xFF == ord('q'):

# Line 5 - Backend port
socketio.run(app, host='0.0.0.0', port=5000)
```

---

## Examples

### Monitor Multiple Construction Sites
```
1. Add Camera: "Site-A-Main" (source: 0)
2. Add Camera: "Site-B-Gate" (source: 1)
3. Add Camera: "Site-C-CCTV" (source: /path/to/stream.mp4)
4. Switch between cameras in dashboard
5. Get unified alerts across all sites
```

### Record Video with Detections
```python
# Modify backend/app.py to save annotated frames
out = cv2.VideoWriter('output.mp4', ...)
out.write(annotated_frame)
```

### Deploy on Cloud (Azure/AWS)
```
1. Package with Docker
2. Deploy backend to App Service/EC2
3. Deploy frontend to Static Web App/S3
4. Connect via public IP instead of localhost
```

---

## Performance Tips

- Use hardware-accelerated GPU if available
- Connect webcam directly to computer (avoid USB hubs)
- For IP cameras, ensure stable network connection
- Limit to 2-3 cameras for smooth 30 FPS
- Use lower resolution video sources for faster processing

---

## License

PPE Detection Dashboard built on:
- YOLOv8 (Ultralytics)
- Flask
- React
- OpenCV

---

## Support

For issues or questions:
1. Check troubleshooting section
2. Verify all dependencies are installed
3. Check logs in browser console and terminal
