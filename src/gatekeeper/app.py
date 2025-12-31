"""
主应用程序模块
"""
import cv2
import numpy as np
from typing import Optional

from .config import Config
from .models import LicensePlateDetector
from .services import PlateTracker, StorageManager, StreamProcessor
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
        
        # 处理视频流
        stats = self.stream_processor.process(self._process_frame)
        
        # 打印最终统计
        self._print_final_statistics(stats)
    
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
            
            # 3. 处理追踪对象
            self._process_tracked_objects(frame, tracked_objects)
            
            # 4. 绘制结果
            display_frame = self._draw_results(frame.copy(), tracked_objects)
            
            # 5. 绘制统计信息
            self._draw_statistics(display_frame)
            
            return display_frame
            
        except Exception as e:
            self.logger.error(f"处理帧出错: {e}")
            return frame
    
    def _process_tracked_objects(self, frame: np.ndarray, tracked_objects: np.ndarray):
        """
        处理追踪对象
        
        Args:
            frame: 当前帧
            tracked_objects: 追踪对象数组
        """
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            track_id = int(track_id)
            
            # 检查是否为新追踪
            if self.tracker.is_new_track(track_id):
                # 保存车牌图像
                filepath = self.storage.save_plate(frame, x1, y1, x2, y2, track_id)
                
                if filepath:
                    # 标记为已保存
                    self.tracker.mark_track_saved(track_id)
                    self.logger.info(
                        f"新车牌已保存! Track ID: {track_id}, "
                        f"总计: {len(self.tracker.saved_track_ids)}"
                    )
    
    def _draw_results(self, frame: np.ndarray, tracked_objects: np.ndarray) -> np.ndarray:
        """
        在帧上绘制结果
        
        Args:
            frame: 输入帧
            tracked_objects: 追踪对象
            
        Returns:
            绘制后的帧
        """
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)
            
            # 根据是否保存选择颜色
            if not self.tracker.is_new_track(track_id):
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
        
        return frame
    
    def _draw_statistics(self, frame: np.ndarray):
        """
        在帧上绘制统计信息
        
        Args:
            frame: 输入帧
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
        
        # 创建半透明背景
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        padding = 10
        line_height = 30
        bg_height = padding * 2 + len(stats_lines) * line_height
        bg_width = 380
        
        cv2.rectangle(
            overlay,
            (padding, padding),
            (bg_width, bg_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
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
        
        self.logger.info("="*60)

