"""
备份主程序
"""

import logging.config

from easybk import TaskManager, UploadManager
from config import init_task


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
    init_task(task_manager, upload_manager)
    task_manager.run_all_task()
    upload_manager.run_all_upload()


if __name__ == "__main__":
    main()
