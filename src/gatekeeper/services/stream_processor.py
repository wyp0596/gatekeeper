"""
视频流处理模块
"""
import cv2
import time
import numpy as np
from typing import Optional, Callable

from ..utils.logger import get_logger


class StreamProcessor:
    """
    视频流处理器
    """
    
    def __init__(
        self,
        rtsp_url: str,
        frame_skip: int = 10,
        display: bool = True,
        display_window_name: str = "License Plate Tracking"
    ):
        """
        初始化流处理器
        
        Args:
            rtsp_url: RTSP流URL或视频文件路径
            frame_skip: 帧采样间隔
            display: 是否显示窗口
            display_window_name: 显示窗口名称
        """
        self.logger = get_logger(__name__)
        self.rtsp_url = rtsp_url
        self.frame_skip = frame_skip
        self.display = display
        self.display_window_name = display_window_name
        
        # 视频捕获对象
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 统计
        self.total_frames = 0
        self.processed_frames = 0
        self.start_time = 0
        self.is_running = False
    
    def open(self) -> bool:
        """
        打开视频流
        
        Returns:
            成功返回True,失败返回False
        """
        try:
            self.logger.info(f"正在打开视频流: {self.rtsp_url}")
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            if not self.cap.isOpened():
                self.logger.error("无法打开视频流")
                return False
            
            self.logger.info("视频流打开成功")
            self.start_time = time.time()
            self.is_running = True
            return True
            
        except Exception as e:
            self.logger.error(f"打开视频流出错: {e}")
            return False
    
    def close(self):
        """关闭视频流"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        if self.display:
            cv2.destroyAllWindows()
        
        self.is_running = False
        self.logger.info("视频流已关闭")
    
    def process(
        self,
        frame_callback: Callable[[np.ndarray, int], Optional[np.ndarray]]
    ) -> dict:
        """
        处理视频流
        
        Args:
            frame_callback: 帧处理回调函数
                          接收参数: (frame, frame_number)
                          返回值: 处理后的帧(用于显示),或None(不显示)
                          
        Returns:
            处理统计信息
        """
        if not self.is_running or self.cap is None:
            self.logger.error("视频流未打开")
            return {}
        
        self.logger.info(f"开始处理视频流 (帧采样间隔: {self.frame_skip})")
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                
                if not ret:
                    self.logger.info("视频流结束或读取错误")
                    break
                
                self.total_frames += 1
                
                # 帧采样 - 每N帧处理一次
                if self.total_frames % self.frame_skip != 0:
                    continue
                
                self.processed_frames += 1
                
                # 调用回调函数处理帧
                display_frame = frame_callback(frame, self.total_frames)
                
                # 显示帧
                if self.display and display_frame is not None:
                    cv2.imshow(self.display_window_name, display_frame)
                    
                    # 检查退出键
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.logger.info("用户请求退出")
                        break
                
                # 定期打印进度
                if self.processed_frames % 100 == 0:
                    self._log_progress()
        
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号")
        except Exception as e:
            self.logger.error(f"处理视频流出错: {e}")
        finally:
            self.close()
        
        return self.get_statistics()
    
    def _log_progress(self):
        """记录处理进度"""
        elapsed = time.time() - self.start_time
        fps = self.processed_frames / elapsed if elapsed > 0 else 0
        self.logger.info(
            f"已处理: {self.processed_frames} 帧, "
            f"总帧数: {self.total_frames}, "
            f"处理速度: {fps:.2f} FPS"
        )
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        elapsed = time.time() - self.start_time if self.start_time > 0 else 0
        fps = self.processed_frames / elapsed if elapsed > 0 else 0
        
        return {
            'total_frames': self.total_frames,
            'processed_frames': self.processed_frames,
            'elapsed_time': elapsed,
            'fps': fps
        }
    
    def stop(self):
        """停止处理"""
        self.is_running = False

