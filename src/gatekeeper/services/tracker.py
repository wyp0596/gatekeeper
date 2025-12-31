"""
车牌追踪模块
"""
import sys
import os
import numpy as np
from typing import Set

# 添加sort目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../sort'))
from sort import Sort

from ..utils.logger import get_logger


class PlateTracker:
    """
    基于SORT算法的车牌追踪器
    """
    
    def __init__(
        self, 
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3
    ):
        """
        初始化追踪器
        
        Args:
            max_age: 追踪对象未检测到时保持的最大帧数
            min_hits: 确认追踪前需要的最小检测次数
            iou_threshold: IOU匹配阈值
        """
        self.logger = get_logger(__name__)
        
        # 初始化SORT追踪器
        self.tracker = Sort(
            max_age=max_age,
            min_hits=min_hits,
            iou_threshold=iou_threshold
        )
        
        # 追踪历史 - 存储已保存的追踪ID
        self.saved_track_ids: Set[int] = set()
        
        # 统计
        self.total_tracks = 0
        self.active_tracks = 0
        
        self.logger.info(
            f"追踪器初始化完成 - max_age={max_age}, "
            f"min_hits={min_hits}, iou_threshold={iou_threshold}"
        )
    
    def update(self, detections: np.ndarray) -> np.ndarray:
        """
        更新追踪器
        
        Args:
            detections: 检测结果数组,格式: [[x1, y1, x2, y2, score], ...]
            
        Returns:
            追踪结果数组,格式: [[x1, y1, x2, y2, track_id], ...]
        """
        try:
            # 更新追踪器
            tracked_objects = self.tracker.update(detections)
            
            # 更新统计
            self.active_tracks = len(self.tracker.trackers)
            
            # 检查是否有新的追踪ID
            if len(tracked_objects) > 0:
                for obj in tracked_objects:
                    track_id = int(obj[4])
                    if track_id > self.total_tracks:
                        self.total_tracks = track_id
            
            return tracked_objects
            
        except Exception as e:
            self.logger.error(f"追踪更新出错: {e}")
            return np.empty((0, 5))
    
    def is_new_track(self, track_id: int) -> bool:
        """
        检查是否为新追踪
        
        Args:
            track_id: 追踪ID
            
        Returns:
            如果是新追踪返回True
        """
        return track_id not in self.saved_track_ids
    
    def mark_track_saved(self, track_id: int):
        """
        标记追踪ID已保存
        
        Args:
            track_id: 追踪ID
        """
        self.saved_track_ids.add(track_id)
    
    def get_statistics(self) -> dict:
        """
        获取追踪器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_tracks': self.total_tracks,
            'active_tracks': self.active_tracks,
            'saved_tracks': len(self.saved_track_ids)
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.saved_track_ids.clear()
        self.total_tracks = 0
        self.active_tracks = 0

