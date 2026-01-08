# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gatekeeper is a real-time license plate detection and tracking system built with YOLOv8 and SORT algorithm. It processes RTSP streams, video files, or images to detect and track license plates, automatically saving unique plates with deduplication.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run with video file
python main.py --rtsp-url video.mp4 --frame-skip 10

# Run with RTSP stream
python main.py --rtsp-url "rtsp://admin:admin@192.168.1.100:554/stream" --frame-skip 10

# Run with config file
python main.py --config config.yaml

# Run headless (no display window)
python main.py --config config.yaml --no-display

# After pip install -e ., run directly
gatekeeper --config config.yaml

# Start the FastAPI plate detection API server
python run_api.py  # Runs on http://0.0.0.0:8099
```

## Architecture

### Core Application Flow

`main.py` -> `GatekeeperApp` (app.py) orchestrates the entire detection pipeline:

1. **LicensePlateDetector** (models/detector.py) - YOLOv8-based detection returning `[x1, y1, x2, y2, confidence]`
2. **PlateTracker** (services/tracker.py) - Wraps SORT algorithm for multi-object tracking, returns `[x1, y1, x2, y2, track_id]`
3. **StreamProcessor** (services/stream_processor.py) - Handles video capture with frame skipping and display
4. **StorageManager** (services/storage.py) - Saves detected plates with deduplication based on track ID

### Key Components

- **sort/sort.py**: SORT (Simple Online and Realtime Tracking) algorithm using Kalman filters for object tracking. Uses `filterpy.kalman.KalmanFilter` internally.
- **api/plate_detection.py**: FastAPI endpoint for single-image plate detection (POST /detect)
- **WebhookService** (services/webhook.py): Optional async webhook notifications when a plate stops moving

### Configuration

Two configuration approaches:
1. **YAML config file** (see config.example.yaml) - Covers detection, tracking, stream, storage, logging, and webhook settings
2. **Command-line arguments** - Override any config option

### Webhook Feature

Optional webhook notifications when a vehicle stops (plate becomes stable):
- Uses Kalman filter velocity (`kf.x[4:6]`) from SORT to detect motion
- Triggers when velocity < threshold for N consecutive frames
- Sends multipart/form-data with plate crop + full frame images
- Async execution via ThreadPoolExecutor (doesn't block main loop)
- Each track_id triggers only once

Enable via `--webhook-enabled --webhook-url "https://..."` or in config.yaml.

### Data Flow

Detection array format: `[[x1, y1, x2, y2, confidence], ...]`
Tracking array format: `[[x1, y1, x2, y2, track_id], ...]`

The tracker maintains `saved_track_ids` set to ensure each unique plate is saved only once.

## Model Requirement

The system requires a YOLOv8 model file `license_plate_detector.pt` in the project root (or specify path via `--model`).
