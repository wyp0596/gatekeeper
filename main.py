#!/usr/bin/env python3
"""
Gatekeeper - 车牌检测与追踪系统
主入口文件
"""
import argparse
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from gatekeeper import GatekeeperApp
from gatekeeper.config import Config, DetectionConfig, TrackingConfig, StreamConfig, StorageConfig, LogConfig


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Gatekeeper - 车牌检测与追踪系统",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 配置文件
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径 (YAML格式)'
    )
    
    # 视频流配置
    stream_group = parser.add_argument_group('视频流配置')
    stream_group.add_argument(
        '--rtsp-url',
        type=str,
        help='RTSP流URL或视频文件路径'
    )
    stream_group.add_argument(
        '--frame-skip',
        type=int,
        default=10,
        help='帧采样间隔 (每N帧处理一次)'
    )
    stream_group.add_argument(
        '--no-display',
        action='store_true',
        help='不显示视频窗口'
    )
    
    # 检测配置
    detection_group = parser.add_argument_group('检测配置')
    detection_group.add_argument(
        '--model',
        type=str,
        default='license_plate_detector.pt',
        help='YOLO模型路径'
    )
    detection_group.add_argument(
        '--confidence',
        type=float,
        default=0.5,
        help='置信度阈值'
    )
    
    # 追踪配置
    tracking_group = parser.add_argument_group('追踪配置')
    tracking_group.add_argument(
        '--max-age',
        type=int,
        default=30,
        help='追踪对象未检测到时保持的最大帧数'
    )
    tracking_group.add_argument(
        '--min-hits',
        type=int,
        default=3,
        help='确认追踪前需要的最小检测次数'
    )
    tracking_group.add_argument(
        '--iou-threshold',
        type=float,
        default=0.3,
        help='IOU匹配阈值'
    )
    
    # 存储配置
    storage_group = parser.add_argument_group('存储配置')
    storage_group.add_argument(
        '--output-dir',
        type=str,
        default='detected_plates',
        help='输出目录'
    )
    storage_group.add_argument(
        '--save-format',
        type=str,
        default='jpg',
        choices=['jpg', 'png', 'bmp'],
        help='保存格式'
    )
    
    # 日志配置
    log_group = parser.add_argument_group('日志配置')
    log_group.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别'
    )
    log_group.add_argument(
        '--log-file',
        type=str,
        help='日志文件路径'
    )
    
    # 其他
    parser.add_argument(
        '--save-config',
        type=str,
        help='保存当前配置到YAML文件'
    )
    
    return parser.parse_args()


def create_config_from_args(args) -> Config:
    """从命令行参数创建配置"""
    
    # 如果指定了配置文件,从文件加载
    if args.config:
        print(f"从配置文件加载: {args.config}")
        return Config.from_yaml(args.config)
    
    # 检查必需参数
    if not args.rtsp_url:
        print("错误: 必须指定 --rtsp-url 或 --config")
        sys.exit(1)
    
    # 从命令行参数创建配置
    config = Config(
        detection=DetectionConfig(
            model_path=args.model,
            confidence_threshold=args.confidence
        ),
        tracking=TrackingConfig(
            max_age=args.max_age,
            min_hits=args.min_hits,
            iou_threshold=args.iou_threshold
        ),
        stream=StreamConfig(
            rtsp_url=args.rtsp_url,
            frame_skip=args.frame_skip,
            display=not args.no_display
        ),
        storage=StorageConfig(
            output_dir=args.output_dir,
            save_format=args.save_format
        ),
        log=LogConfig(
            log_level=args.log_level,
            log_file=args.log_file
        )
    )
    
    return config


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()
    
    # 创建配置
    config = create_config_from_args(args)
    
    # 保存配置(如果需要)
    if args.save_config:
        config.to_yaml(args.save_config)
        print(f"配置已保存到: {args.save_config}")
    
    try:
        # 创建并运行应用
        app = GatekeeperApp(config)
        app.run()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

