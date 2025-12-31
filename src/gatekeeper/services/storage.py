"""
存储管理模块
"""
import os
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..utils.logger import get_logger


class StorageManager:
    """
    车牌图像存储管理器
    """
    
    def __init__(
        self,
        output_dir: str = "detected_plates",
        save_format: str = "jpg",
        filename_template: str = "plate_track{track_id:04d}_{timestamp}.{ext}"
    ):
        """
        初始化存储管理器
        
        Args:
            output_dir: 输出目录
            save_format: 保存格式 (jpg, png, bmp)
            filename_template: 文件名模板
        """
        self.logger = get_logger(__name__)
        self.output_dir = output_dir
        self.save_format = save_format
        self.filename_template = filename_template
        
        # 创建输出目录
        self._create_output_directory()
        
        # 统计
        self.saved_count = 0
    
    def _create_output_directory(self):
        """创建输出目录"""
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"输出目录已准备: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {e}")
            raise
    
    def save_plate(
        self,
        frame: np.ndarray,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        track_id: int
    ) -> Optional[str]:
        """
        保存车牌图像
        
        Args:
            frame: 完整帧图像
            x1, y1, x2, y2: 边界框坐标
            track_id: 追踪ID
            
        Returns:
            保存的文件路径,失败返回None
        """
        try:
            # 转换坐标为整数
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # 确保坐标在图像范围内
            h, w = frame.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            # 裁剪车牌区域
            plate_img = frame[y1:y2, x1:x2]
            
            if plate_img.size == 0:
                self.logger.warning(f"车牌区域为空,跳过保存 (Track ID: {track_id})")
                return None
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = self.filename_template.format(
                track_id=track_id,
                timestamp=timestamp,
                ext=self.save_format
            )
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存图像
            cv2.imwrite(filepath, plate_img)
            
            self.saved_count += 1
            self.logger.info(f"已保存车牌图像: {filename} (Track ID: {track_id})")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存车牌图像失败: {e}")
            return None
    
    def get_statistics(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'saved_count': self.saved_count,
            'output_dir': self.output_dir,
            'save_format': self.save_format
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.saved_count = 0

