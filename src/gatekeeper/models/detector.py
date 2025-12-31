"""
车牌检测器模块
"""
import numpy as np
from typing import Tuple
from ultralytics import YOLO

from ..utils.logger import get_logger


class LicensePlateDetector:
    """
    基于YOLO的车牌检测器
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        初始化检测器
        
        Args:
            model_path: YOLO模型路径
            confidence_threshold: 置信度阈值
        """
        self.logger = get_logger(__name__)
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        
        # 加载模型
        self.logger.info(f"正在加载YOLO模型: {model_path}")
        try:
            self.model = YOLO(model_path)
            self.logger.info("模型加载成功")
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            raise
        
        # 统计
        self.total_detections = 0
    
    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        检测图像中的车牌
        
        Args:
            frame: 输入图像帧
            
        Returns:
            检测结果数组,格式: [[x1, y1, x2, y2, confidence], ...]
        """
        try:
            # 运行YOLO检测
            results = self.model(frame, verbose=False)
            
            # 提取检测结果
            detections = []
            result = results[0]
            boxes = result.boxes
            
            for box in boxes:
                conf = box.conf[0].item()
                
                # 按置信度过滤
                if conf >= self.confidence_threshold:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    detections.append([x1, y1, x2, y2, conf])
            
            if detections:
                self.total_detections += len(detections)
                return np.array(detections)
            else:
                return np.empty((0, 5))
                
        except Exception as e:
            self.logger.error(f"检测过程出错: {e}")
            return np.empty((0, 5))
    
    def get_statistics(self) -> dict:
        """
        获取检测器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_detections': self.total_detections,
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.total_detections = 0

