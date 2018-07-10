# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import logging

from .task import Task
# from . import oss_uploader

class TaskManager(object):
    """
    任务管理器
    """

    def __init__(self):
        self.logger = logging.getLogger("TaskManager")
        self.task_list = []
        self.result_list = []
    
    def add_task(self, task):
        """
        添加任务
        """
        if task is None:
            raise ValueError("task must have value!")
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task!")
        
        self.task_list.append(task)
    
    def run_all_task(self):
        """
        运行所有备份任务
        """
        for task in self.task_list:
            result = task.run()
            if result:
                self.logger.info("Task [%s]: 备份成功，加入待上传列表。", task.get_name())
                remote_folder = task.get_remote_folder()
                if remote_folder is not None:
                    remote_path = "{}/{}".format(remote_folder, task.get_output_file_name())
                else:
                    remote_path = task.get_output_file_name()
                self.result_list.append((remote_path, task.get_output_full_path()))
            else:
                self.logger.info("Task [%s]: 未备份，不需要上传。")
        print(self.result_list)
    
    def backup_to_remote(self):
        """
        上传到 oss 中。
        """
        # oss_uploader.batch_upload(self.result_list)
        pass
