# Gatekeeper - 车牌检测与追踪系统

<div align="center">

[English](README.md) | [简体中文](README_CN.md)

</div>

🚗 基于 YOLOv8 和 SORT 算法的实时车牌检测与追踪系统

## ✨ 特性

- 🎯 **高精度检测**: 基于 YOLOv8 的车牌检测
- 🔍 **智能追踪**: SORT 算法实现车牌去重与追踪
- 📹 **多源支持**: 支持 RTSP 流、视频文件、图片
- 💾 **自动保存**: 自动保存检测到的唯一车牌图像
- 📊 **实时统计**: 实时显示检测和追踪统计信息
- ⚙️ **灵活配置**: 支持 YAML 配置文件和命令行参数
- 📝 **完善日志**: 彩色日志输出,支持文件记录

## 📁 项目结构

```
gatekeeper/
├── src/
│   └── gatekeeper/
│       ├── __init__.py
│       ├── app.py                 # 主应用程序
│       ├── config/                # 配置管理
│       │   ├── __init__.py
│       │   └── config.py
│       ├── models/                # 检测模型
│       │   ├── __init__.py
│       │   └── detector.py
│       ├── services/              # 核心服务
│       │   ├── __init__.py
│       │   ├── tracker.py         # 追踪服务
│       │   ├── storage.py         # 存储管理
│       │   └── stream_processor.py # 流处理
│       └── utils/                 # 工具模块
│           ├── __init__.py
│           └── logger.py          # 日志管理
├── sort/                          # SORT追踪算法
│   └── sort.py
├── main.py                        # 程序入口
├── config.example.yaml            # 配置文件示例
├── requirements.txt               # 依赖包
├── setup.py                       # 安装脚本
└── README.md                      # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备模型

确保 `license_plate_detector.pt` 模型文件在项目根目录

### 3. 运行程序

#### 方式一: 使用命令行参数

```bash
# 处理视频文件
python main.py --rtsp-url 25fps_smaller.mp4 --frame-skip 10

# 连接 RTSP 流
python main.py --rtsp-url "rtsp://admin:admin@192.168.6.136:554/11" --frame-skip 10

# 自定义参数
python main.py \
  --rtsp-url video.mp4 \
  --model license_plate_detector.pt \
  --confidence 0.5 \
  --frame-skip 10 \
  --output-dir detected_plates \
  --log-level INFO
```

#### 方式二: 使用配置文件

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑配置文件
vim config.yaml

# 使用配置文件运行
python main.py --config config.yaml
```

#### 方式三: 安装后使用

```bash
# 安装到系统
pip install -e .

# 直接运行
gatekeeper --config config.yaml
```

## ⚙️ 配置说明

### 配置文件示例 (config.yaml)

```yaml
# 检测配置
detection:
  model_path: "license_plate_detector.pt"
  confidence_threshold: 0.5

# 追踪配置
tracking:
  max_age: 30          # 追踪对象未检测到时保持的最大帧数
  min_hits: 3          # 确认追踪前需要的最小检测次数
  iou_threshold: 0.3   # IOU匹配阈值

# 视频流配置
stream:
  rtsp_url: "25fps_smaller.mp4"
  frame_skip: 10       # 每N帧处理一次
  display: true
  display_window_name: "License Plate Tracking"

# 存储配置
storage:
  output_dir: "detected_plates"
  save_format: "jpg"
  filename_template: "plate_track{track_id:04d}_{timestamp}.{ext}"

# 日志配置
log:
  log_level: "INFO"
  log_file: null       # 可设置为 "logs/gatekeeper.log"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 命令行参数

```bash
视频流配置:
  --rtsp-url URL              RTSP流URL或视频文件路径
  --frame-skip N              帧采样间隔 (默认: 10)
  --no-display                不显示视频窗口

检测配置:
  --model PATH                YOLO模型路径 (默认: license_plate_detector.pt)
  --confidence FLOAT          置信度阈值 (默认: 0.5)

追踪配置:
  --max-age N                 最大追踪年龄 (默认: 30)
  --min-hits N                最小命中次数 (默认: 3)
  --iou-threshold FLOAT       IOU阈值 (默认: 0.3)

存储配置:
  --output-dir DIR            输出目录 (默认: detected_plates)
  --save-format FORMAT        保存格式: jpg/png/bmp (默认: jpg)

日志配置:
  --log-level LEVEL           日志级别 (默认: INFO)
  --log-file PATH             日志文件路径

其他:
  --config PATH               配置文件路径
  --save-config PATH          保存当前配置到文件
  -h, --help                  显示帮助信息
```

## 📊 功能说明

### 1. 车牌检测

- 使用 YOLOv8 模型进行车牌检测
- 可配置置信度阈值
- 自动统计检测数量

### 2. 车牌追踪

- 基于 SORT 算法的多目标追踪
- 自动去重,确保每个车牌只保存一次
- 支持配置追踪参数

### 3. 帧采样

- 可配置帧采样间隔,提高处理速度
- 适用于实时流和视频文件

### 4. 自动保存

- 检测到新车牌自动保存图像
- 文件名包含追踪ID和时间戳
- 支持多种图像格式

### 5. 实时显示

- 实时显示检测和追踪结果
- 彩色边界框区分已保存/追踪中状态
- 实时统计信息叠加显示

### 6. 日志记录

- 彩色终端日志输出
- 可选文件日志记录
- 多级别日志支持

## 🔧 高级用法

### 开发模式安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/gatekeeper.git
cd gatekeeper

# 安装为开发模式
pip install -e .

# 运行测试 (如果有)
pytest tests/
```

### 生成配置文件

```bash
# 从命令行参数生成配置文件
python main.py \
  --rtsp-url video.mp4 \
  --confidence 0.6 \
  --frame-skip 5 \
  --save-config my_config.yaml
```

### 无显示模式运行

```bash
# 适用于服务器环境
python main.py --config config.yaml --no-display
```

## 📝 使用示例

### 示例 1: 处理视频文件

```bash
python main.py \
  --rtsp-url my_video.mp4 \
  --frame-skip 10 \
  --output-dir output/plates
```

### 示例 2: 连接监控摄像头

```bash
python main.py \
  --rtsp-url "rtsp://admin:password@192.168.1.100:554/stream" \
  --frame-skip 5 \
  --confidence 0.6
```

### 示例 3: 批量处理

```bash
# 创建批处理脚本
for video in videos/*.mp4; do
  python main.py --rtsp-url "$video" --no-display
done
```

## 🐛 故障排除

### 问题 1: 模型文件找不到

```bash
# 确保模型文件在正确位置
ls -l license_plate_detector.pt

# 或使用绝对路径
python main.py --model /path/to/license_plate_detector.pt
```

### 问题 2: RTSP 连接失败

- 检查 RTSP URL 格式
- 确认网络连接
- 验证用户名和密码
- 尝试使用 VLC 等工具测试 RTSP 流

### 问题 3: 检测率低

- 降低置信度阈值: `--confidence 0.3`
- 减少帧跳过: `--frame-skip 1`
- 检查视频质量和光照条件

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📧 联系方式

如有问题或建议,请通过以下方式联系:

- Email: your.email@example.com
- GitHub Issues: https://github.com/yourusername/gatekeeper/issues

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [SORT: Simple Online and Realtime Tracking](https://github.com/abewley/sort)
- [OpenCV](https://opencv.org/)

---

⭐ 如果这个项目对你有帮助,请给它一个星标!

