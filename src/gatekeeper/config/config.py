"""
Configuration classes for the Gatekeeper system
"""
import os
import yaml
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class DetectionConfig:
    """检测相关配置"""
    model_path: str = "license_plate_detector.pt"
    confidence_threshold: float = 0.5
    
    def validate(self):
        """验证配置"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        if not 0 < self.confidence_threshold <= 1:
            raise ValueError("confidence_threshold 必须在 0 到 1 之间")


@dataclass
class TrackingConfig:
    """追踪相关配置"""
    max_age: int = 30
    min_hits: int = 3
    iou_threshold: float = 0.3
    
    def validate(self):
        """验证配置"""
        if self.max_age < 1:
            raise ValueError("max_age 必须大于 0")
        if self.min_hits < 1:
            raise ValueError("min_hits 必须大于 0")
        if not 0 < self.iou_threshold <= 1:
            raise ValueError("iou_threshold 必须在 0 到 1 之间")


@dataclass
class StreamConfig:
    """视频流相关配置"""
    rtsp_url: str
    frame_skip: int = 10
    display: bool = True
    display_window_name: str = "License Plate Tracking"
    
    def validate(self):
        """验证配置"""
        if not self.rtsp_url:
            raise ValueError("rtsp_url 不能为空")
        if self.frame_skip < 1:
            raise ValueError("frame_skip 必须大于 0")


@dataclass
class StorageConfig:
    """存储相关配置"""
    output_dir: str = "detected_plates"
    save_format: str = "jpg"
    filename_template: str = "plate_track{track_id:04d}_{timestamp}.{ext}"
    
    def validate(self):
        """验证配置"""
        if self.save_format not in ['jpg', 'png', 'bmp']:
            raise ValueError(f"不支持的格式: {self.save_format}")


@dataclass
class LogConfig:
    """日志相关配置"""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def validate(self):
        """验证配置"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"log_level 必须是: {valid_levels}")


@dataclass
class WebhookConfig:
    """Webhook 相关配置"""
    enabled: bool = False
    url: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    velocity_threshold: float = 2.0
    stable_frames: int = 5

    def validate(self):
        """验证配置"""
        if self.enabled and not self.url:
            raise ValueError("webhook 启用时 url 不能为空")
        if not 0 < self.timeout <= 300:
            raise ValueError("timeout 必须在 1 到 300 秒之间")
        if self.retry_count < 0:
            raise ValueError("retry_count 不能为负数")
        if self.velocity_threshold < 0:
            raise ValueError("velocity_threshold 不能为负数")
        if self.stable_frames < 1:
            raise ValueError("stable_frames 必须大于 0")


@dataclass
class Config:
    """主配置类"""
    detection: DetectionConfig
    tracking: TrackingConfig
    stream: StreamConfig
    storage: StorageConfig
    log: LogConfig
    webhook: WebhookConfig = None

    def __post_init__(self):
        if self.webhook is None:
            self.webhook = WebhookConfig()

    def validate(self):
        """验证所有配置"""
        self.detection.validate()
        self.tracking.validate()
        self.stream.validate()
        self.storage.validate()
        self.log.validate()
        self.webhook.validate()

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Config':
        """从字典创建配置"""
        return cls(
            detection=DetectionConfig(**config_dict.get('detection', {})),
            tracking=TrackingConfig(**config_dict.get('tracking', {})),
            stream=StreamConfig(**config_dict.get('stream', {})),
            storage=StorageConfig(**config_dict.get('storage', {})),
            log=LogConfig(**config_dict.get('log', {})),
            webhook=WebhookConfig(**config_dict.get('webhook', {}))
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Config':
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'detection': asdict(self.detection),
            'tracking': asdict(self.tracking),
            'stream': asdict(self.stream),
            'storage': asdict(self.storage),
            'log': asdict(self.log),
            'webhook': asdict(self.webhook)
        }

    def to_yaml(self, yaml_path: str):
        """保存为YAML文件"""
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def default(cls) -> 'Config':
        """创建默认配置"""
        return cls(
            detection=DetectionConfig(),
            tracking=TrackingConfig(),
            stream=StreamConfig(rtsp_url=""),
            storage=StorageConfig(),
            log=LogConfig(),
            webhook=WebhookConfig()
        )

