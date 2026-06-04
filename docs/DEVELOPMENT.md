# Development & Environment Setup

This document describes how to set up a development environment, run the project locally, and common troubleshooting steps.

## Prerequisites
- OS: Windows 10/11 or Linux (Ubuntu recommended).
- Git
- Python 3.8 - 3.11
- Node.js 16+ and npm
- Docker & Docker Compose (optional, recommended for reproducible stacks)
- (Optional) NVIDIA GPU + CUDA for faster training/inference

## Repository layout (important files)
- `backend/` — Flask API, Socket.IO server, and Python inference glue. See `backend/requirements.txt`.
- `frontend/` — React dashboard and client code.
- `inference.py` — standalone script for live/image/video inference using YOLOv8.
- `models/` — pretrained or custom model weights (`best.pt`).
- `data/` — dataset YAMLs and train/valid/test folders.
- `docker-compose.yml` — compose file to run services in containers.

---

## Python (backend) setup
1. Create and activate a virtual environment (PowerShell shown):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. Optional: create a `.env` file from the template:

```powershell
copy backend\.env.example backend\.env
# Then edit backend\.env if you need to change settings
```

4. Run the backend (development):

```powershell
# from repo root
cd backend
python app.py
# or using flask
# $env:FLASK_APP="app.py"; python -m flask run
```

Notes:
- If Flask refuses to load due to environment variables, set `FLASK_APP` and `FLASK_ENV` accordingly.
- Ensure `models/best.pt` exists when starting inference endpoints.

---

## Frontend setup
1. Install dependencies and run the dev server:

```bash
cd frontend
npm install
npm run start
```

2. Build for production:

```bash
npm run build
```

Notes:
- The dev server runs on `http://localhost:3000` by default and proxies API/socket connections to the backend if configured.

---

## Running inference locally
The repository includes `inference.py` for quick experiments. Examples:

```bash
# Run webcam inference (index 0)
python inference.py --source 0 --model models/best.pt --conf 0.5

# Run on an image and save annotated output
python inference.py --source path/to/image.jpg --model models/best.pt --save

# Run and save webcam output video
python inference.py --source 0 --model models/best.pt --save
```

Arguments:
- `--source` — webcam index, RTSP URL, or path to image/video
- `--model` — path to weights (default `models/best.pt`)
- `--conf` — confidence threshold (0.0 - 1.0)
- `--imgsz` — inference image size

---

## Docker (optional)
You can run the stack using Docker Compose. This is useful for reproducible deployments.

```bash
# Build and run
docker compose up --build
```

Notes:
- For GPU support inside containers, install the NVIDIA Container Toolkit and use GPU-enabled base images.
- Compose configuration and service names are defined in `docker-compose.yml`.

---

## GPU / PyTorch notes
- If you have an NVIDIA GPU, install a PyTorch wheel that matches your CUDA toolkit. See https://pytorch.org for the correct `pip` command (e.g., `cu118`).
- Example (adjust `cu118` to your CUDA version):

```powershell
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
```

If PyTorch or CUDA are misconfigured you may see model load or runtime errors.

---

## Common troubleshooting
- "Cannot open source": verify camera index or RTSP URL and that no other process is using the camera.
- Model load failures: verify `models/best.pt` exists and PyTorch + ultralytics are installed.
- Slow inference: ensure GPU is available; otherwise consider converting model to ONNX/TensorRT or using FP16.
- Frontend unable to connect: check backend is running and Socket.IO endpoint/ CORS settings.

---

## Development tips
- Use a Python linter and formatter (flake8 / black) to maintain code style.
- Run small test jobs when changing `data/` to confirm the label format and class mapping.
- For production edge devices, convert and optimize the model (ONNX -> TensorRT or INT8 quantization) and measure latency.

## Unit Testing
Unit testing verifies individual functions and modules in isolation without running the full camera pipeline or frontend. In this project, unit tests should focus on helper functions, API routes, frame-processing utilities, and state-handling logic using mocked YOLO outputs, synthetic frames, and Flask test clients. This keeps the tests fast, deterministic, and useful for catching regressions when detection logic, response formatting, or file handling changes.

## Integration Testing
Integration testing verifies that the main parts of the system work together as expected. For this project, integration tests should cover the connection between the camera stream, YOLO inference, violation detection, snapshot saving, Socket.IO event emission, backend API responses, and the frontend dashboard flow. These tests use real project components together, with a short sample video or mocked camera source, to confirm that detections appear correctly, violation images are stored, and the dashboard can receive updates without breaking the full workflow.

## Acceptance Testing
    Acceptance testing checks whether the finished system meets the user’s expected behavior in a real usage scenario. For this project, acceptance tests should confirm that a camera feed can be added, PPE violations are detected, alerts are shown on the dashboard, violation snapshots are saved, and the backend responds correctly to user actions. These tests validate the end-to-end workflow from detection to display, ensuring the system is ready for demo or deployment use.

## Conclusion
This PPE detection system combines YOLOv8-based object detection, a Flask backend, and a React dashboard to provide a practical safety monitoring solution for construction sites. It automates the identification of missing hardhats, masks, and safety vests, then presents the results in real time so that violations can be reviewed quickly and evidence can be stored for later analysis.

The project demonstrates how computer vision and web technologies can work together to improve workplace safety and reduce manual monitoring effort. With further improvements such as stronger tracking, wider dataset coverage, and deployment optimizations, the system can become even more reliable and suitable for real-world use.

## Future Works
Future work can focus on improving detection accuracy and reducing false alarms by training on a larger and more diverse PPE dataset. Adding object tracking across frames would help prevent repeated alerts for the same person and make the system more stable in crowded or partially occluded scenes.

The system can also be extended with advanced deployment and monitoring features such as cloud hosting, alert notifications, role-based access, performance dashboards, and edge-device optimization. These enhancements would make the application more scalable, easier to manage, and better suited for real construction-site use.

## References
1. Ultralytics. [YOLOv8 documentation](https://docs.ultralytics.com).
2. Flask Project. [Flask documentation](https://flask.palletsprojects.com).
3. React Team. [React documentation](https://react.dev).
4. OpenCV. [OpenCV documentation](https://docs.opencv.org).
5. Redmon, J., Divvala, S., Girshick, R., and Farhadi, A. [You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640). CVPR, 2016.
6. Bochkovskiy, A., Wang, C.-Y., and Liao, H.-Y. M. [YOLOv4: Optimal Speed and Accuracy of Object Detection](https://arxiv.org/abs/2004.10934). arXiv preprint, 2020.
7. Wang, C.-Y., Bochkovskiy, A., and Liao, H.-Y. M. [YOLOv7: Trainable Bag-of-Freebies Sets New State-of-the-Art for Real-Time Object Detectors](https://arxiv.org/abs/2207.02696). arXiv preprint, 2022.
8. Wang, C.-Y. et al. [YOLOv8](https://docs.ultralytics.com/models/yolov8/). Ultralytics model documentation.
9. Related PPE detection and construction safety monitoring papers on deep learning-based helmet, mask, and vest detection in workplace surveillance systems.

## Useful commands summary

```powershell
# Backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend; python app.py

# Frontend
cd frontend
npm install
npm run start

# Inference
python inference.py --source 0 --model models/best.pt --save

# Docker
docker compose up --build
```

---

If you'd like, I can expand this with platform-specific instructions (Windows vs Linux), GPU setup guides, or CI/CD steps.
