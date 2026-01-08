"""
主应用程序模块
"""
import cv2
import numpy as np
from typing import Optional, List, Tuple

from .config import Config
from .models import LicensePlateDetector
from .services import PlateTracker, StorageManager, StreamProcessor, WebhookService
from .utils import setup_logger, get_logger


class GatekeeperApp:
    """
    Gatekeeper主应用程序
    车牌检测与追踪系统
    """
    
    def __init__(self, config: Config):
        """
        初始化应用程序
        
        Args:
            config: 配置对象
        """
        # 验证配置
        config.validate()
        self.config = config
        
        # 设置日志
        self.logger = setup_logger(
            name="gatekeeper",
            level=config.log.log_level,
            log_file=config.log.log_file,
            log_format=config.log.log_format
        )
        
        self.logger.info("="*60)
        self.logger.info("Gatekeeper - 车牌检测与追踪系统")
        self.logger.info("="*60)
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化各个组件"""
        try:
            # 检测器
            self.detector = LicensePlateDetector(
                model_path=self.config.detection.model_path,
                confidence_threshold=self.config.detection.confidence_threshold
            )
            
            # 追踪器
            self.tracker = PlateTracker(
                max_age=self.config.tracking.max_age,
                min_hits=self.config.tracking.min_hits,
                iou_threshold=self.config.tracking.iou_threshold
            )
            
            # 存储管理器
            self.storage = StorageManager(
                output_dir=self.config.storage.output_dir,
                save_format=self.config.storage.save_format,
                filename_template=self.config.storage.filename_template
            )
            
            # 流处理器
            self.stream_processor = StreamProcessor(
                rtsp_url=self.config.stream.rtsp_url,
                frame_skip=self.config.stream.frame_skip,
                display=self.config.stream.display,
                display_window_name=self.config.stream.display_window_name
            )

            # Webhook 服务（可选）
            self.webhook_service: Optional[WebhookService] = None
            if self.config.webhook.enabled:
                self.webhook_service = WebhookService(self.config.webhook)
                self.logger.info("Webhook 服务已启用")

            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def run(self):
        """运行应用程序"""
        self.logger.info("开始运行应用程序")

        # 打开视频流
        if not self.stream_processor.open():
            self.logger.error("无法打开视频流,程序退出")
            return

        try:
            # 处理视频流
            stats = self.stream_processor.process(self._process_frame)

            # 打印最终统计
            self._print_final_statistics(stats)
        finally:
            # 关闭存储管理器（等待异步写入完成）
            self.storage.shutdown()
            # 关闭 webhook 服务
            if self.webhook_service is not None:
                self.webhook_service.shutdown()
    
    def _process_frame(self, frame: np.ndarray, frame_number: int) -> Optional[np.ndarray]:
        """
        处理单帧

        Args:
            frame: 输入帧
            frame_number: 帧编号

        Returns:
            处理后的帧(用于显示)
        """
        try:
            # 1. 检测车牌
            detections = self.detector.detect(frame)

            # 2. 更新追踪器
            tracked_objects = self.tracker.update(detections)

            # 3. 处理追踪对象，同时获取处理后的追踪信息（避免重复计算）
            processed_tracks = self._process_tracked_objects(frame, tracked_objects)

            # 4. 只在需要显示时才复制和绘制
            if self.config.stream.display:
                display_frame = frame.copy()
                self._draw_results(display_frame, processed_tracks)
                self._draw_statistics(display_frame)
                return display_frame

            return frame

        except Exception as e:
            self.logger.error(f"处理帧出错: {e}")
            return frame
    
    def _process_tracked_objects(
        self, frame: np.ndarray, tracked_objects: np.ndarray
    ) -> List[Tuple[int, int, int, int, int, bool]]:
        """
        处理追踪对象

        Args:
            frame: 当前帧
            tracked_objects: 追踪对象数组

        Returns:
            处理后的追踪列表: [(x1, y1, x2, y2, track_id, is_saved), ...]
        """
        processed_tracks = []

        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            # 一次性转换坐标（避免重复转换）
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)

            # 一次性检查是否为新追踪（避免重复调用）
            is_new = self.tracker.is_new_track(track_id)

            # 检查是否为新追踪，需要保存
            if is_new:
                # 保存车牌图像
                filepath = self.storage.save_plate(frame, x1, y1, x2, y2, track_id)

                if filepath:
                    # 标记为已保存
                    self.tracker.mark_track_saved(track_id)
                    is_new = False  # 更新状态
                    self.logger.info(
                        f"新车牌已保存! Track ID: {track_id}, "
                        f"总计: {len(self.tracker.saved_track_ids)}"
                    )

            # Webhook 触发逻辑：检查是否稳定
            if self.webhook_service is not None:
                # 检查是否已触发过
                if not self.webhook_service.is_triggered(track_id):
                    # 检查是否稳定
                    if self.tracker.is_track_stable(
                        track_id,
                        self.config.webhook.velocity_threshold,
                        self.config.webhook.stable_frames
                    ):
                        # 裁剪车牌图片
                        plate_image = frame[y1:y2, x1:x2]
                        # 异步触发 webhook
                        self.webhook_service.trigger_async(
                            track_id,
                            plate_image,
                            frame,
                            (x1, y1, x2, y2)
                        )

            # 存储处理后的信息: is_saved = not is_new
            processed_tracks.append((x1, y1, x2, y2, track_id, not is_new))

        return processed_tracks
    
    def _draw_results(
        self, frame: np.ndarray, processed_tracks: List[Tuple[int, int, int, int, int, bool]]
    ) -> None:
        """
        在帧上绘制结果（直接修改 frame）

        Args:
            frame: 输入帧（会被直接修改）
            processed_tracks: 处理后的追踪列表 [(x1, y1, x2, y2, track_id, is_saved), ...]
        """
        for x1, y1, x2, y2, track_id, is_saved in processed_tracks:
            # 根据是否保存选择颜色（直接使用已计算的 is_saved）
            if is_saved:
                color = (0, 255, 0)  # 绿色 - 已保存
                status = "saved"
            else:
                color = (0, 165, 255)  # 橙色 - 追踪中
                status = "tracking"

            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 绘制标签
            label = f"ID:{track_id} [{status}]"
            cv2.putText(
                frame, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
    
    def _draw_statistics(self, frame: np.ndarray) -> None:
        """
        在帧上绘制统计信息（直接修改 frame）

        Args:
            frame: 输入帧（会被直接修改）
        """
        # 获取统计信息
        stream_stats = self.stream_processor.get_statistics()
        detector_stats = self.detector.get_statistics()
        tracker_stats = self.tracker.get_statistics()
        storage_stats = self.storage.get_statistics()

        # 准备统计文本
        stats_lines = [
            f"total frames: {stream_stats.get('total_frames', 0)}",
            f"processed frames: {stream_stats.get('processed_frames', 0)}",
            f"total detections: {detector_stats.get('total_detections', 0)}",
            f"unique plates: {storage_stats.get('saved_count', 0)}",
            f"active tracks: {tracker_stats.get('active_tracks', 0)}",
            f"FPS: {stream_stats.get('fps', 0):.2f}"
        ]

        # 计算背景尺寸
        padding = 10
        line_height = 30
        bg_height = padding * 2 + len(stats_lines) * line_height
        bg_width = 380

        # 只复制需要半透明处理的 ROI 区域（而非整帧）
        roi = frame[padding:bg_height, padding:bg_width].copy()
        cv2.rectangle(roi, (0, 0), (bg_width - padding, bg_height - padding), (0, 0, 0), -1)
        cv2.addWeighted(roi, 0.6, frame[padding:bg_height, padding:bg_width], 0.4, 0,
                        frame[padding:bg_height, padding:bg_width])

        # 绘制文本
        for i, line in enumerate(stats_lines):
            y = padding + 25 + i * line_height
            cv2.putText(
                frame, line, (padding + 10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
    
    def _print_final_statistics(self, stats: dict):
        """
        打印最终统计信息
        
        Args:
            stats: 统计信息字典
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("处理完成 - 最终统计")
        self.logger.info("="*60)
        
        # 流处理统计
        self.logger.info(f"总帧数: {stats.get('total_frames', 0)}")
        self.logger.info(f"已处理帧数: {stats.get('processed_frames', 0)}")
        self.logger.info(f"处理时间: {stats.get('elapsed_time', 0):.2f} 秒")
        self.logger.info(f"平均FPS: {stats.get('fps', 0):.2f}")
        
        # 检测统计
        detector_stats = self.detector.get_statistics()
        self.logger.info(f"总检测数: {detector_stats['total_detections']}")
        
        # 追踪统计
        tracker_stats = self.tracker.get_statistics()
        self.logger.info(f"总追踪数: {tracker_stats['total_tracks']}")
        self.logger.info(f"已保存追踪: {tracker_stats['saved_tracks']}")
        
        # 存储统计
        storage_stats = self.storage.get_statistics()
        self.logger.info(f"已保存图像: {storage_stats['saved_count']}")
        self.logger.info(f"输出目录: {storage_stats['output_dir']}")

        # Webhook 统计
        if self.webhook_service is not None:
            webhook_stats = self.webhook_service.get_statistics()
            self.logger.info(f"Webhook 触发次数: {webhook_stats['triggered_count']}")

        self.logger.info("="*60)

