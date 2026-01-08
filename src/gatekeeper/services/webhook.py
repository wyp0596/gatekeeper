"""
Webhook 服务模块
"""
import io
import cv2
import numpy as np
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Tuple, Optional

from ..config import WebhookConfig
from ..utils.logger import get_logger


class WebhookService:
    """
    Webhook 服务
    异步发送车牌检测通知到后端
    """

    def __init__(self, config: WebhookConfig):
        """
        初始化 Webhook 服务

        Args:
            config: Webhook 配置
        """
        self.logger = get_logger(__name__)
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.triggered_tracks: Set[int] = set()

        self.logger.info(
            f"Webhook 服务初始化完成 - url={config.url}, "
            f"timeout={config.timeout}s, retry_count={config.retry_count}"
        )

    def trigger_async(
        self,
        track_id: int,
        plate_image: np.ndarray,
        full_frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> bool:
        """
        异步触发 webhook（每个 track_id 只触发一次）

        Args:
            track_id: 追踪 ID
            plate_image: 车牌区域图片
            full_frame: 完整帧图片
            bbox: 边界框 (x1, y1, x2, y2)

        Returns:
            是否成功提交任务（不代表发送成功）
        """
        if track_id in self.triggered_tracks:
            return False

        self.triggered_tracks.add(track_id)
        self.logger.info(f"触发 Webhook - Track ID: {track_id}")
        self.executor.submit(
            self._send_webhook,
            track_id,
            plate_image.copy(),
            full_frame.copy(),
            bbox
        )
        return True

    def _send_webhook(
        self,
        track_id: int,
        plate_image: np.ndarray,
        full_frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ):
        """
        实际发送 webhook（带重试）

        Args:
            track_id: 追踪 ID
            plate_image: 车牌区域图片
            full_frame: 完整帧图片
            bbox: 边界框 (x1, y1, x2, y2)
        """
        timestamp = datetime.now().isoformat()
        x1, y1, x2, y2 = bbox

        # 编码图片为 JPEG
        _, plate_buffer = cv2.imencode('.jpg', plate_image)
        _, frame_buffer = cv2.imencode('.jpg', full_frame)

        # 构建 multipart 数据
        files = {
            'plate_image': ('plate.jpg', io.BytesIO(plate_buffer.tobytes()), 'image/jpeg'),
            'full_frame': ('frame.jpg', io.BytesIO(frame_buffer.tobytes()), 'image/jpeg'),
        }
        data = {
            'track_id': str(track_id),
            'timestamp': timestamp,
            'bbox_x1': str(x1),
            'bbox_y1': str(y1),
            'bbox_x2': str(x2),
            'bbox_y2': str(y2),
        }

        # 发送请求（带重试）
        last_error: Optional[Exception] = None
        for attempt in range(self.config.retry_count + 1):
            try:
                # 重新创建 BytesIO 对象（因为每次请求后会被消耗）
                files = {
                    'plate_image': ('plate.jpg', io.BytesIO(plate_buffer.tobytes()), 'image/jpeg'),
                    'full_frame': ('frame.jpg', io.BytesIO(frame_buffer.tobytes()), 'image/jpeg'),
                }

                response = requests.post(
                    self.config.url,
                    files=files,
                    data=data,
                    timeout=self.config.timeout
                )

                if response.status_code == 200:
                    self.logger.info(
                        f"Webhook 发送成功 - Track ID: {track_id}, "
                        f"尝试次数: {attempt + 1}"
                    )
                    return
                else:
                    self.logger.warning(
                        f"Webhook 响应错误 - Track ID: {track_id}, "
                        f"状态码: {response.status_code}, "
                        f"尝试次数: {attempt + 1}"
                    )
                    last_error = Exception(f"HTTP {response.status_code}")

            except requests.exceptions.RequestException as e:
                last_error = e
                self.logger.warning(
                    f"Webhook 发送失败 - Track ID: {track_id}, "
                    f"错误: {e}, 尝试次数: {attempt + 1}"
                )

        self.logger.error(
            f"Webhook 发送最终失败 - Track ID: {track_id}, "
            f"最后错误: {last_error}"
        )

    def is_triggered(self, track_id: int) -> bool:
        """
        检查指定 track_id 是否已触发

        Args:
            track_id: 追踪 ID

        Returns:
            是否已触发
        """
        return track_id in self.triggered_tracks

    def get_statistics(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'triggered_count': len(self.triggered_tracks),
            'url': self.config.url
        }

    def shutdown(self):
        """关闭服务"""
        self.executor.shutdown(wait=True)
        self.logger.info("Webhook 服务已关闭")
