from loguru import logger
from collections import deque

class PanelHandler:
    def __init__(self, max_logs=100):
        self.logs = deque(maxlen=max_logs)

    def write(self, message):
        self.logs.append(message.strip())

    def __call__(self, message):
        self.write(message)

def setup_logger(log_file="grid_trading.log"):
    # 移除默认的处理器
    logger.remove()
    
    # 添加文件处理器
    logger.add(log_file, rotation="500 MB", level="INFO")
    
    # 添加控制台处理器（可选，用于调试）
    # logger.add(sys.stderr, level="INFO")
    
    # 创建并添加面板处理器
    panel_handler = PanelHandler()
    logger.add(panel_handler, level="INFO")
    
    return panel_handler

