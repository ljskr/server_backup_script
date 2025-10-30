"""
示例程序
"""

import logging.config

from easybk import TaskManager, PackTask, MysqlTask, SingleFileTask, OSSUploader, FTPUploader
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
    init_task(task_manager)
    task_manager.run_all_task()


if __name__ == "__main__":
    main()
