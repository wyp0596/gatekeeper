"""
车牌追踪模块
"""
import sys
import os
import math
import numpy as np
from typing import Set, Dict, Optional

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

        # 稳定性追踪 - track_id -> 连续稳定帧数
        self.stable_frame_counts: Dict[int, int] = {}

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
        self.stable_frame_counts.clear()
        self.total_tracks = 0
        self.active_tracks = 0

    def _get_kalman_tracker(self, track_id: int):
        """
        获取指定 track_id 对应的 KalmanBoxTracker

        Args:
            track_id: 追踪 ID (SORT 返回的 id+1)

        Returns:
            KalmanBoxTracker 对象，未找到返回 None
        """
        # SORT 内部 id 是从 0 开始，返回时 +1
        # 所以 track_id=1 对应内部 id=0
        internal_id = track_id - 1
        for trk in self.tracker.trackers:
            if trk.id == internal_id:
                return trk
        return None

    def get_track_velocity(self, track_id: int) -> Optional[float]:
        """
        获取指定 track 的当前速度

        Args:
            track_id: 追踪 ID

        Returns:
            速度（像素/帧），未找到返回 None
        """
        trk = self._get_kalman_tracker(track_id)
        if trk is None:
            return None

        # Kalman 滤波器状态: [x, y, s, r, vx, vy, vs]
        # vx, vy 是 x, y 方向的速度
        vx = trk.kf.x[4, 0]
        vy = trk.kf.x[5, 0]
        velocity = math.sqrt(vx ** 2 + vy ** 2)
        return velocity

    def update_stability(self, track_id: int, velocity_threshold: float) -> int:
        """
        更新指定 track 的稳定性计数

        Args:
            track_id: 追踪 ID
            velocity_threshold: 速度阈值（像素/帧）

        Returns:
            当前连续稳定帧数
        """
        velocity = self.get_track_velocity(track_id)
        if velocity is None:
            return 0

        if velocity < velocity_threshold:
            # 速度低于阈值，增加稳定计数
            self.stable_frame_counts[track_id] = self.stable_frame_counts.get(track_id, 0) + 1
        else:
            # 速度超过阈值，重置计数
            self.stable_frame_counts[track_id] = 0

        return self.stable_frame_counts[track_id]

    def is_track_stable(
        self,
        track_id: int,
        velocity_threshold: float,
        stable_frames: int
    ) -> bool:
        """
        判断 track 是否稳定（停稳）

        Args:
            track_id: 追踪 ID
            velocity_threshold: 速度阈值（像素/帧）
            stable_frames: 需要持续稳定的帧数

        Returns:
            是否稳定
        """
        # 更新稳定性计数并获取当前值
        current_stable_frames = self.update_stability(track_id, velocity_threshold)
        return current_stable_frames >= stable_frames

