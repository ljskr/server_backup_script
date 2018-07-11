# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import logging

from .tasks import Task
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
        task_count = len(self.task_list)
        self.logger.info("总备份任务数: %s", task_count)

        cur_index = 1
        for task in self.task_list:
            try:
                self.logger.info("准备执行第 %s 个备份任务，[%s]", cur_index, task.get_name())
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
                    self.logger.info("Task [%s]: 未备份，不需要上传。", task.get_name())
            except Exception:
                self.logger.exception("Task [%s]: 备份发生异常。", task.get_name())
            cur_index += 1

        upload_count = len(self.result_list)
        self.logger.info("总待上传任务数: %s", upload_count)
        try:
            self.logger.info("准备执行上传任务。")
            self.backup_to_remote()
            self.logger.info("成功执行上传任务。")
        except Exception:
            self.logger.exception("执行上传任务发生异常!")

    def backup_to_remote(self):
        """
        上传到 oss 中。
        """
        # oss_uploader.batch_upload(self.result_list)
        pass
