"""
Author: liujun (ljskryj@163.com)
Date: 2019-10-12
"""


import abc
import logging

from ..tasks import Task


class Uploader():
    """
    上传抽象类

    参数：
        name: 本实例名称
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name: str):
        self.logger = logging.getLogger("Uploader")
        self.name = name
        self.task_list = []

    def get_name(self) -> str:
        """
        获取实例名称
        """
        return self.name

    def add_task(self, task: Task):
        """
        添加需要上传的任务
        """
        if task is None:
            raise ValueError("task must have value!")
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task!")

        self.task_list.append(task)

    def run(self):
        """
        执行上传
        """
        task_count = len(self.task_list)
        self.logger.info("Uploader [%s]: 总上传任务数: %s",
                         self.get_name(), task_count)
        cur_index = 1
        for task in self.task_list:
            try:
                if task.get_result():
                    self.logger.info(
                        "Uploader [%s]: index[%s] 准备上传任务[%s]", self.get_name(), cur_index, task.get_name())

                    self.do_upload(task)
                    self.logger.info(
                        "Uploader [%s]: index[%s] 任务[%s]上传完成", self.get_name(), cur_index, task.get_name())
                else:
                    self.logger.info("Uploader [%s]: index[%s] 任务[%s]未备份，不需要上传。", self.get_name(
                    ), cur_index, task.get_name())
            except Exception:
                self.logger.exception(
                    "Uploader [%s]: index[%s] 任务[%s]上传发生异常。", self.get_name(), cur_index, task.get_name())
            cur_index += 1
        self.logger.info("Uploader [%s]: 所有上传任务数执行完毕！",
                         self.get_name())

    @abc.abstractmethod
    def do_upload(self, task: Task) -> bool:
        """
        子类执行任务
        返回值:
            result bool 类型，代表成功或者失败。
        """
        raise NotImplementedError("Uploader.do_upload")
