"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import logging

from .encipher_manager import EncipherManager
from .tasks import Task
from .uploaders import Uploader


class TaskManager():
    """
    任务管理器
    """

    def __init__(self):
        self.logger = logging.getLogger("TaskManager")
        self.task_list = []
        self.uploader_list = []
        self.encipher_manager = EncipherManager()
        self.encipher_file = "md5_list.txt"

    def set_encipher_file(self, path: str):
        """
        加载配置文件
        """
        self.encipher_file = path

    def add_task(self, task: Task):
        """
        添加任务
        """
        if task is None:
            raise ValueError("task must have value!")
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task!")

        self.task_list.append(task)

    def add_uploader(self, uploader: Uploader):
        """
        添加上传器
        """
        if uploader is None:
            raise ValueError("uploader must have value!")
        if not isinstance(uploader, Uploader):
            raise ValueError("uploader must be an instance of Uploader!")

        self.uploader_list.append(uploader)

    def run_all_task(self):
        """
        运行所有备份任务
        """
        self.logger.info("开始执行任务！")
        # 加载 encipher 文件
        self.encipher_manager.load_data_from_file(self.encipher_file)

        self.logger.info("准备执行备份任务！ ")

        task_count = len(self.task_list)
        self.logger.info("总备份任务数: %s", task_count)

        cur_index = 1
        for task in self.task_list:
            try:
                self.logger.info(
                    "准备执行第 %s 个备份任务，[%s]", cur_index, task.get_name())
                task.run()
            except Exception:
                self.logger.exception("Task [%s]: 备份发生异常。", task.get_name())
            cur_index += 1

        self.logger.info("备份任务执行完毕！ ")

        self.logger.info("准备执行上传任务！ ")

        uploader_count = len(self.uploader_list)
        self.logger.info("上传器个数: %s。", uploader_count)
        for uploader in self.uploader_list:
            try:
                self.logger.info(
                    "Uploader [%s]: 准备执行上传任务。", uploader.get_name())
                uploader.run()
                self.logger.info(
                    "Uploader [%s]: 成功执行上传任务。", uploader.get_name())
            except Exception:
                self.logger.exception(
                    "Uploader [%s]: 上传发生异常!", uploader.get_name())

        self.logger.info("上传任务执行完毕！ ")

        # 保存 encipher 文件
        self.encipher_manager.save_data_to_file()
        self.logger.info("所有任务执行完毕！ ")
