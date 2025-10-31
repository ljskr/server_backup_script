"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import abc
import logging
import os


class Task():
    """
    备份任务抽象类
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, task_name: str, output_dir: str):
        """
        参数:
            task_name: 任务名称
            output_dir: 备份输出目录
        """
        self.logger = logging.getLogger("Task")
        self.task_name = task_name
        self.result = False
        self.output_dir = output_dir
        self.output_file_name = None
        self.output_full_path = None


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

        # 创建目录
        if not os.path.exists(self.output_dir):
            self.logger.info("Task [%s]: create folder %s",
                             self.task_name, self.output_dir)
            os.makedirs(self.output_dir)

        self.result = self.do_task()

    @abc.abstractmethod
    def do_task(self) -> bool:
        """
        子类执行任务
        返回值:
            result bool 类型，代表成功或者失败。
        """
        raise NotImplementedError("Task.do_task")

    def set_output_file_name_and_full_path(self, output_file_name: str):
        """
        设置备份出来的文件名
        参数:
            output_file_name: 备份出来的文件名
        """
        self.output_file_name = output_file_name
        self.output_full_path = os.path.join(self.output_dir, self.output_file_name)

    def get_output_file_name(self) -> str:
        """
        返回备份出来的文件名
        """
        return self.output_file_name

    def get_output_full_path(self) -> str:
        """
        返回备份出来的文件的绝对路径
        """
        return self.output_full_path
