"""
备份主程序
"""

import logging.config
import os

from easybk import TaskManager, UploadManager
from config_parser import init_from_yaml


def init_logger():
    """
    初始化 logging
    """
    logging.config.fileConfig("./logger.conf")



def main():
    """
    主入口
    """
    init_logger()

    task_manager = TaskManager()
    upload_manager = UploadManager()
    
    # 从 YAML 配置文件加载（如果存在）
    if os.path.exists("config.yaml"):
        init_from_yaml(task_manager, upload_manager, "config.yaml")
    
    # 从 Python 配置文件加载（如果存在）
    if os.path.exists("config.py"):
        from config import init_task
        init_task(task_manager, upload_manager)
    
    task_manager.run_all_task()
    upload_manager.run_all_upload()


if __name__ == "__main__":
    main()
