# Gatekeeper - License Plate Detection and Tracking System

<div align="center">

[English](README.md) | [简体中文](README_CN.md)

</div>

🚗 Real-time license plate detection and tracking system based on YOLOv8 and SORT algorithm

## ✨ Features

- 🎯 **High-Precision Detection**: License plate detection based on YOLOv8
- 🔍 **Intelligent Tracking**: SORT algorithm for plate deduplication and tracking
- 📹 **Multi-Source Support**: Support RTSP streams, video files, and images
- 💾 **Auto-Save**: Automatically save unique detected license plate images
- 📊 **Real-Time Statistics**: Display detection and tracking statistics in real-time
- ⚙️ **Flexible Configuration**: Support YAML configuration files and command-line arguments
- 📝 **Comprehensive Logging**: Colored log output with file recording support

## 📁 Project Structure

```
gatekeeper/
├── src/
│   └── gatekeeper/
│       ├── __init__.py
│       ├── app.py                 # Main application
│       ├── config/                # Configuration management
│       │   ├── __init__.py
│       │   └── config.py
│       ├── models/                # Detection models
│       │   ├── __init__.py
│       │   └── detector.py
│       ├── services/              # Core services
│       │   ├── __init__.py
│       │   ├── tracker.py         # Tracking service
│       │   ├── storage.py         # Storage management
│       │   └── stream_processor.py # Stream processing
│       └── utils/                 # Utility modules
│           ├── __init__.py
│           └── logger.py          # Logging management
├── sort/                          # SORT tracking algorithm
│   └── sort.py
├── main.py                        # Program entry point
├── config.example.yaml            # Configuration file example
├── requirements.txt               # Dependencies
├── setup.py                       # Installation script
└── README.md                      # Project documentation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Model

Ensure the `license_plate_detector.pt` model file is in the project root directory

### 3. Run the Program

#### Method 1: Using Command-Line Arguments

```bash
# Process video file
python main.py --rtsp-url 25fps_smaller.mp4 --frame-skip 10

# Connect to RTSP stream
python main.py --rtsp-url "rtsp://admin:admin@192.168.6.136:554/11" --frame-skip 10

# Custom parameters
python main.py \
  --rtsp-url video.mp4 \
  --model license_plate_detector.pt \
  --confidence 0.5 \
  --frame-skip 10 \
  --output-dir detected_plates \
  --log-level INFO
```

#### Method 2: Using Configuration File

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration file
vim config.yaml

# Run with configuration file
python main.py --config config.yaml
```

#### Method 3: Install and Use

```bash
# Install to system
pip install -e .

# Run directly
gatekeeper --config config.yaml
```

## ⚙️ Configuration

### Configuration File Example (config.yaml)

```yaml
# Detection configuration
detection:
  model_path: "license_plate_detector.pt"
  confidence_threshold: 0.5

# Tracking configuration
tracking:
  max_age: 30 # Maximum frames to keep track alive without detections
  min_hits: 3 # Minimum detections before track is confirmed
  iou_threshold: 0.3 # IOU threshold for matching

# Video stream configuration
stream:
  rtsp_url: "25fps_smaller.mp4"
  frame_skip: 10 # Process every N frames
  display: true
  display_window_name: "License Plate Tracking"

# Storage configuration
storage:
  output_dir: "detected_plates"
  save_format: "jpg"
  filename_template: "plate_track{track_id:04d}_{timestamp}.{ext}"

# Logging configuration
log:
  log_level: "INFO"
  log_file: null # Can be set to "logs/gatekeeper.log"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Command-Line Arguments

```bash
Video stream configuration:
  --rtsp-url URL              RTSP stream URL or video file path
  --frame-skip N              Frame sampling interval (default: 10)
  --no-display                Don't display video window

Detection configuration:
  --model PATH                YOLO model path (default: license_plate_detector.pt)
  --confidence FLOAT          Confidence threshold (default: 0.5)

Tracking configuration:
  --max-age N                 Maximum tracking age (default: 30)
  --min-hits N                Minimum hits count (default: 3)
  --iou-threshold FLOAT       IOU threshold (default: 0.3)

Storage configuration:
  --output-dir DIR            Output directory (default: detected_plates)
  --save-format FORMAT        Save format: jpg/png/bmp (default: jpg)

Logging configuration:
  --log-level LEVEL           Log level (default: INFO)
  --log-file PATH             Log file path

Other:
  --config PATH               Configuration file path
  --save-config PATH          Save current configuration to file
  -h, --help                  Show help information
```

## 📊 Features Description

### 1. License Plate Detection

- Uses YOLOv8 model for license plate detection
- Configurable confidence threshold
- Automatic detection count statistics

### 2. License Plate Tracking

- Multi-object tracking based on SORT algorithm
- Automatic deduplication, ensures each plate is saved only once
- Supports configurable tracking parameters

### 3. Frame Sampling

- Configurable frame sampling interval to improve processing speed
- Suitable for real-time streams and video files

### 4. Auto-Save

- Automatically save images when new plates are detected
- Filename includes tracking ID and timestamp
- Support multiple image formats

### 5. Real-Time Display

- Real-time display of detection and tracking results
- Color-coded bounding boxes for saved/tracking status
- Real-time statistics overlay on display

### 6. Logging

- Colored terminal log output
- Optional file log recording
- Multi-level log support

## 🔧 Advanced Usage

### Development Mode Installation

```bash
# Clone repository
git clone https://github.com/yourusername/gatekeeper.git
cd gatekeeper

# Install in development mode
pip install -e .

# Run tests (if available)
pytest tests/
```

### Generate Configuration File

```bash
# Generate configuration file from command-line arguments
python main.py \
  --rtsp-url video.mp4 \
  --confidence 0.6 \
  --frame-skip 5 \
  --save-config my_config.yaml
```

### Headless Mode

```bash
# Suitable for server environments
python main.py --config config.yaml --no-display
```

## 📝 Usage Examples

### Example 1: Process Video File

```bash
python main.py \
  --rtsp-url my_video.mp4 \
  --frame-skip 10 \
  --output-dir output/plates
```

### Example 2: Connect to Security Camera

```bash
python main.py \
  --rtsp-url "rtsp://admin:password@192.168.1.100:554/stream" \
  --frame-skip 5 \
  --confidence 0.6
```

### Example 3: Batch Processing

```bash
# Create batch processing script
for video in videos/*.mp4; do
  python main.py --rtsp-url "$video" --no-display
done
```

## 🐛 Troubleshooting

### Issue 1: Model File Not Found

```bash
# Ensure model file is in correct location
ls -l license_plate_detector.pt

# Or use absolute path
python main.py --model /path/to/license_plate_detector.pt
```

### Issue 2: RTSP Connection Failed

- Check RTSP URL format
- Confirm network connection
- Verify username and password
- Try testing RTSP stream with tools like VLC

### Issue 3: Low Detection Rate

- Lower confidence threshold: `--confidence 0.3`
- Reduce frame skip: `--frame-skip 1`
- Check video quality and lighting conditions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📧 Contact

For questions or suggestions, please contact:

- Email: your.email@example.com
- GitHub Issues: https://github.com/yourusername/gatekeeper/issues

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [SORT: Simple Online and Realtime Tracking](https://github.com/abewley/sort)
- [OpenCV](https://opencv.org/)

## 🌐 Documentation

- **[README_CN.md](README_CN.md)** - 中文文档 (Chinese Documentation)

---

⭐ If this project helps you, please give it a star!
