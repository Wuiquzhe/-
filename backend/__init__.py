# backend包初始化文件

# 导出主要模块和函数
from .data_manager import DataManager
from .task_manager import TaskManager
from .utils import *

__version__ = "0.1.0"
__all__ = ["DataManager", "TaskManager"]