#!/bin/bash
# Gatekeeper 运行示例脚本

echo "======================================"
echo "Gatekeeper - 车牌检测与追踪系统"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python -c "import ultralytics, cv2, numpy, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 检查模型文件
if [ ! -f "license_plate_detector.pt" ]; then
    echo "警告: 未找到模型文件 license_plate_detector.pt"
fi

# 创建配置文件(如果不存在)
if [ ! -f "config.yaml" ]; then
    echo "创建配置文件..."
    cp config.example.yaml config.yaml
    echo "已创建 config.yaml,请编辑后再运行"
    exit 0
fi

# 运行程序
echo "启动 Gatekeeper..."
echo ""
python main.py --config config.yaml

echo ""
echo "程序已退出"

