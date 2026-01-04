#!/usr/bin/env python3
"""
启动车牌检测 API 服务
"""
import uvicorn
from api.plate_detection import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
