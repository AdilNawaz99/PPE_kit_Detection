import cv2
import threading
import json
import time
import os
from collections import deque, defaultdict
from datetime import datetime
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from ultralytics import YOLO
import numpy as np

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'best.pt')
VIOLATION_DIR = os.path.join(PROJECT_ROOT, 'output', 'violations')
VIOLATION_CLASSES = {'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest'}
CAPTURE_INTERVAL_SECONDS = 5

os.makedirs(VIOLATION_DIR, exist_ok=True)

# Load the trained model
model = YOLO(MODEL_PATH)

# Store camera streams
cameras = {}
detection_stats = defaultdict(lambda: {
    'total_detections': 0,
    'detections_by_class': defaultdict(int),
    'alerts': deque(maxlen=100),
    'violations': deque(maxlen=100),
    'last_detection': None,
    'last_updated': None
})

class CameraStream:
    def __init__(self, camera_id, source):
        self.camera_id = camera_id
        self.source = source
        self.cap = None
        self.is_running = False
        self.frame = None
        self.detection_frame = None
        self.lock = threading.Lock()
        self.last_violation_capture = 0.0
        self.last_frame_at = 0.0
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.thread.start()
            
    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def _open_capture(self):
        """Open camera/video source with Windows-friendly webcam fallback."""
        cap = None
        if isinstance(self.source, int):
            for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, None):
                try:
                    cap = cv2.VideoCapture(self.source, backend) if backend is not None else cv2.VideoCapture(self.source)
                    if cap.isOpened():
                        break
                    cap.release()
                except Exception:
                    if cap is not None:
                        cap.release()
                    cap = None
        else:
            try:
                cap = cv2.VideoCapture(self.source)
            except Exception:
                cap = None

        if cap is not None and cap.isOpened():
            # Best-effort defaults for smoother webcam streams.
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
        return cap

    def _placeholder_jpeg(self, text):
        canvas = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(canvas, f"Camera: {self.camera_id}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(canvas, text, (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 180, 255), 2)
        cv2.putText(canvas, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), (20, 155),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)
        ok, buffer = cv2.imencode('.jpg', canvas)
        return buffer.tobytes() if ok else None
            
    def _capture_frames(self):
        try:
            self.cap = self._open_capture()
            if self.cap is None or not self.cap.isOpened():
                print(f"Failed to open camera {self.camera_id}, retrying...")

            consecutive_failures = 0
                
            while self.is_running:
                if self.cap is None or not self.cap.isOpened():
                    time.sleep(1.0)
                    self.cap = self._open_capture()
                    continue

                ret, frame = self.cap.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= 15:
                        print(f"Reconnecting camera {self.camera_id} after read failures...")
                        if self.cap:
                            self.cap.release()
                        self.cap = self._open_capture()
                        consecutive_failures = 0
                    time.sleep(0.03)
                    continue
                consecutive_failures = 0
                self.last_frame_at = time.time()
                    
                # Run detection
                results = model(frame, conf=0.5)[0]
                
                # Draw boxes
                annotated_frame = frame.copy()
                detections = []
                frame_violations = []
                
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    class_id = int(box.cls[0] if hasattr(box.cls, '__len__') else box.cls)
                    confidence = float(box.conf[0] if hasattr(box.conf, '__len__') else box.conf)
                    class_name = results.names[class_id]
                    
                    # Check for missing PPE violations
                    if class_name in VIOLATION_CLASSES:
                        color = (0, 0, 255)  # Red for safety violations
                        frame_violations.append({
                            'class': class_name,
                            'confidence': float(confidence)
                        })
                    else:
                        color = (0, 255, 0)  # Green for safe
                    
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{class_name} {confidence:.2f}"
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    detections.append({
                        'class': class_name,
                        'confidence': float(confidence)
                    })
                    
                    # Update stats
                    detection_stats[self.camera_id]['total_detections'] += 1
                    detection_stats[self.camera_id]['detections_by_class'][class_name] += 1
                    detection_stats[self.camera_id]['last_detection'] = datetime.now().isoformat()
                    detection_stats[self.camera_id]['last_updated'] = datetime.now().isoformat()

                # Capture violation evidence at most every 5 seconds per camera.
                if frame_violations:
                    now = time.time()
                    if now - self.last_violation_capture >= CAPTURE_INTERVAL_SECONDS:
                        self.last_violation_capture = now
                        timestamp = datetime.now()
                        file_name = f"{self.camera_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                        file_name = file_name.replace(' ', '_')
                        file_path = os.path.join(VIOLATION_DIR, file_name)
                        cv2.imwrite(file_path, annotated_frame)

                        violation_types = sorted({item['class'] for item in frame_violations})
                        violation_event = {
                            'camera_id': self.camera_id,
                            'violation_types': violation_types,
                            'detections': frame_violations,
                            'timestamp': timestamp.isoformat(),
                            'image_url': f"/violations/{file_name}",
                            'description': f"PPE violation found: {', '.join(violation_types)}. Snapshot captured for review."
                        }

                        alert_event = {
                            'camera_id': self.camera_id,
                            'class': ', '.join(violation_types),
                            'confidence': max(item['confidence'] for item in frame_violations),
                            'timestamp': timestamp.isoformat(),
                            'description': f"{self.camera_id}: {', '.join(violation_types)} detected."
                        }

                        detection_stats[self.camera_id]['alerts'].append(alert_event)
                        detection_stats[self.camera_id]['violations'].append(violation_event)

                        socketio.emit('alert', alert_event)
                        socketio.emit('violation_event', violation_event)
                
                # Add timestamp and camera ID
                cv2.putText(annotated_frame, f"Camera: {self.camera_id}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(annotated_frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                with self.lock:
                    self.frame = frame
                    self.detection_frame = annotated_frame
                    
                # Emit frame to connected clients
                if len(detections) > 0:
                    socketio.emit('detection', {
                        'camera_id': self.camera_id,
                        'detections': detections,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            print(f"Error in camera stream {self.camera_id}: {e}")
        finally:
            self.is_running = False
            if self.cap:
                self.cap.release()
    
    def get_frame(self):
        with self.lock:
            if self.detection_frame is not None:
                ret, buffer = cv2.imencode('.jpg', self.detection_frame)
                if ret:
                    return buffer.tobytes()

        # Avoid hanging stream endpoint when camera has not produced frames yet.
        return self._placeholder_jpeg('Waiting for live camera frames...')

def generate_frames(camera_id):
    """Generate frames for streaming video"""
    if camera_id not in cameras:
        return
        
    camera = cameras[camera_id]
    while True:
        frame_bytes = camera.get_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.01)

# Routes
@app.route('/')
def index():
    return jsonify({'status': 'Backend running', 'version': '1.0', 'frontend': 'http://localhost:3000'})

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    """Stream video feed for a specific camera"""
    return Response(generate_frames(camera_id),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/violations/<path:filename>')
def get_violation_image(filename):
    """Serve saved violation snapshot images."""
    return send_from_directory(VIOLATION_DIR, filename)

@app.route('/cameras', methods=['GET', 'POST'])
def manage_cameras():
    """Get all cameras or add a new camera"""
    if request.method == 'POST':
        data = request.json
        camera_id = data.get('camera_id')
        source = data.get('source')  # 0 for webcam, or video file path
        
        if camera_id and source is not None:
            try:
                if isinstance(source, int):
                    parsed_source = source
                elif isinstance(source, str):
                    stripped_source = source.strip()
                    parsed_source = int(stripped_source) if stripped_source.isdigit() else stripped_source
                else:
                    parsed_source = source

                # Make camera creation idempotent to handle duplicate POSTs from UI retries/StrictMode.
                if camera_id in cameras:
                    return jsonify({
                        'success': True,
                        'message': f'Camera {camera_id} already exists',
                        'camera_id': camera_id
                    }), 200

                # Most local webcams cannot be opened by multiple streams at the same time.
                if isinstance(parsed_source, int):
                    for existing_id, existing_camera in cameras.items():
                        if isinstance(existing_camera.source, int) and existing_camera.source == parsed_source:
                            return jsonify({
                                'success': False,
                                'error': f'Source {parsed_source} is already in use by {existing_id}. Remove it first.'
                            }), 409

                camera = CameraStream(camera_id, parsed_source)
                camera.start()
                cameras[camera_id] = camera
                
                # Initialize stats
                detection_stats[camera_id] = {
                    'total_detections': 0,
                    'detections_by_class': defaultdict(int),
                    'alerts': deque(maxlen=100),
                    'violations': deque(maxlen=100),
                    'last_detection': None,
                    'last_updated': None
                }
                
                socketio.emit('camera_added', {'camera_id': camera_id})
                return jsonify({'success': True, 'message': f'Camera {camera_id} added'}), 201
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 400
        else:
            return jsonify({'success': False, 'error': 'Missing camera_id or source'}), 400
    
    else:  # GET
        camera_list = list(cameras.keys())
        return jsonify({'cameras': camera_list})

@app.route('/cameras/<camera_id>', methods=['DELETE'])
def remove_camera(camera_id):
    """Remove a camera"""
    if camera_id in cameras:
        cameras[camera_id].stop()
        del cameras[camera_id]
        socketio.emit('camera_removed', {'camera_id': camera_id})
        return jsonify({'success': True, 'message': f'Camera {camera_id} removed'})
    return jsonify({'success': False, 'error': 'Camera not found'}), 404

@app.route('/stats/<camera_id>')
def get_stats(camera_id):
    """Get statistics for a camera"""
    if camera_id in detection_stats:
        stats = detection_stats[camera_id]
        cam = cameras.get(camera_id)
        now_ts = time.time()
        live = bool(cam and cam.last_frame_at and now_ts - cam.last_frame_at <= 3)
        return jsonify({
            'camera_id': camera_id,
            'camera_status': 'live' if live else 'waiting',
            'total_detections': stats['total_detections'],
            'detections_by_class': dict(stats['detections_by_class']),
            'last_detection': stats['last_detection'],
            'last_updated': stats['last_updated'],
            'recent_alerts': list(stats['alerts'])[-10:],
            'recent_violations': list(stats['violations'])[-10:]
        })
    return jsonify({'error': 'Camera not found'}), 404

@app.route('/stats')
def get_all_stats():
    """Get statistics for all cameras"""
    all_stats = {}
    now_ts = time.time()
    for camera_id, stats in detection_stats.items():
        cam = cameras.get(camera_id)
        live = bool(cam and cam.last_frame_at and now_ts - cam.last_frame_at <= 3)
        all_stats[camera_id] = {
            'camera_status': 'live' if live else 'waiting',
            'total_detections': stats['total_detections'],
            'detections_by_class': dict(stats['detections_by_class']),
            'last_detection': stats['last_detection'],
            'last_updated': stats['last_updated'],
            'recent_alerts': list(stats['alerts'])[-5:],
            'recent_violations': list(stats['violations'])[-5:]
        }
    return jsonify(all_stats)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=False, use_reloader=False, host='0.0.0.0', port=5000)
