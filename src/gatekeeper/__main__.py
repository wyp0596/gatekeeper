"""
Gatekeeper包的主入口
允许使用 python -m gatekeeper 运行
"""
import sys
from pathlib import Path

# 确保主目录在路径中
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 导入并运行main函数
from main import main

if __name__ == "__main__":
    main()

