#!/usr/bin/env python3
"""
车牌检测 FastAPI 接口
"""
import io
import base64
import threading
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
from ultralytics import YOLO

# 配置
MODEL_PATH = "license_plate_detector.pt"
CONFIDENCE_THRESHOLD = 0.5

# 全局模型实例（线程安全）
_model: Optional[YOLO] = None
_model_lock = threading.Lock()


def get_model() -> YOLO:
    """获取或加载模型（线程安全单例）"""
    global _model
    if _model is None:
        with _model_lock:
            # 双重检查锁定
            if _model is None:
                _model = YOLO(MODEL_PATH)
    return _model


class PlateLocation(BaseModel):
    """车牌位置"""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    crop_base64: Optional[str] = None


class DetectionResponse(BaseModel):
    """检测响应"""
    has_plate: bool
    plate_count: int
    plates: list[PlateLocation]


app = FastAPI(
    title="车牌检测 API",
    description="上传图片检测车牌位置",
    version="1.0.0"
)


def detect_plates_from_image(image: np.ndarray) -> list[tuple]:
    """检测图片中的车牌"""
    model = get_model()
    results = model(image, verbose=False)
    detections = []
    
    for box in results[0].boxes:
        conf = box.conf[0].item()
        if conf >= CONFIDENCE_THRESHOLD:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            detections.append((int(x1), int(y1), int(x2), int(y2), conf))
    
    return detections


def crop_to_base64(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> str:
    """裁剪图片并转为 base64"""
    crop = image[y1:y2, x1:x2]
    _, buffer = cv2.imencode('.jpg', crop)
    return base64.b64encode(buffer).decode('utf-8')


@app.post("/detect", response_model=DetectionResponse)
async def detect_plate(
    file: UploadFile = File(..., description="上传的图片文件"),
    return_crops: bool = Query(False, description="是否返回车牌区域图片(base64)")
):
    """
    检测上传图片中的车牌
    
    - **file**: 图片文件 (支持 jpg, png 等常见格式)
    - **return_crops**: 是否返回车牌裁剪图片的 base64 编码
    """
    # 读取上传的图片
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise HTTPException(status_code=400, detail="无法解析图片文件")
    
    # 检测车牌
    detections = detect_plates_from_image(image)
    
    # 构建响应
    plates = []
    for x1, y1, x2, y2, conf in detections:
        plate = PlateLocation(
            x1=x1, y1=y1, x2=x2, y2=y2,
            confidence=round(conf, 4)
        )
        if return_crops:
            plate.crop_base64 = crop_to_base64(image, x1, y1, x2, y2)
        plates.append(plate)
    
    return DetectionResponse(
        has_plate=len(plates) > 0,
        plate_count=len(plates),
        plates=plates
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
