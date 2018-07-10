# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import abc

class Task(object):
    """
    备份任务抽象类
    """
    def __init__(self, task_name, remote_folder=None):
        self.task_name = task_name
        self.remote_folder = remote_folder

    def get_name(self):
        return self.task_name

    @abc.abstractmethod
    def run(self):
        """
        执行任务
        返回值:
            result bool 类型，代表成功或者失败。
        """
        raise NotImplementedError("Task.run")

    @abc.abstractmethod
    def get_output_file_name(self):
        """
        返回备份出来的文件名
        """
        raise NotImplementedError("Task.get_output_file_name")

    @abc.abstractmethod
    def get_output_full_path(self):
        """
        返回备份出来的文件的绝对路径
        """
        raise NotImplementedError("Task.get_output_full_path")

    def get_remote_folder(self):
        """
        返回运程的备份目录
        """
        return self.remote_folder
