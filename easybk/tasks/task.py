"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import abc
import logging


class Task():
    """
    备份任务抽象类
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, task_name: str):
        self.logger = logging.getLogger("Task")
        self.task_name = task_name
        self.result = False

    def get_name(self) -> str:
        """
        获取任务名称
        """
        return self.task_name

    def get_result(self) -> bool:
        """
        获取结果
        """
        return self.result

    def run(self):
        """
        执行备份任务并上传
        """
        self.logger.info("Task [%s]: 开始执行任务。", self.task_name)
        self.result = self.do_task()

    @abc.abstractmethod
    def do_task(self) -> bool:
        """
        子类执行任务
        返回值:
            result bool 类型，代表成功或者失败。
        """
        raise NotImplementedError("Task.do_task")

    @abc.abstractmethod
    def get_output_file_name(self) -> str:
        """
        返回备份出来的文件名
        """
        raise NotImplementedError("Task.get_output_file_name")

    @abc.abstractmethod
    def get_output_full_path(self) -> str:
        """
        返回备份出来的文件的绝对路径
        """
        raise NotImplementedError("Task.get_output_full_path")
