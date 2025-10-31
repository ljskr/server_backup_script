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

    def get_name(self) -> str:
        """
        获取实例名称
        """
        return self.name

    @abc.abstractmethod
    def do_upload(self, task: Task, remote_dir: str) -> bool:
        """
        执行上传任务
        参数:
            task: 备份任务
            remote_dir: 远程目录
        返回值:
            result bool 类型，代表成功或者失败。
        """
        raise NotImplementedError("Uploader.do_upload")
