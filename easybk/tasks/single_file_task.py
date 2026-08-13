"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import datetime
import logging
import os
import shutil

from .task import Task
from ..encipher_manager import EncipherManager


class SingleFileTask(Task):
    """
    单文件备份任务。

    参数:
        task_name  任务名
        output_dir  备份输出目录
        source_file  需要备份的文件
        backup_on_change 是否在只有变更的时候才进行备份
    """

    def __init__(self, task_name: str, output_dir: str, source_file: str, backup_on_change: bool = False):
        """
        参数:
            task_name  任务名
            output_dir  备份输出目录
            source_file  需要备份的文件
            backup_on_change  是否在只有变更的时候才进行备份
        """
        # super(SingleFileTask, self).__init__(name)
        Task.__init__(self, task_name, output_dir)
        self.logger = logging.getLogger("SingleFileTask")
        self.backup_file = source_file
        self.encipher_manager = EncipherManager()
        self.backup_on_change = backup_on_change


    def do_task(self) -> bool:
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始备份单文件.", self.task_name)

        # 计算用于变化检测的 SHA-256 摘要
        digest = EncipherManager.digest(self.backup_file)
        self.logger.info("Task [%s]: SHA-256 is %s", self.task_name, digest)

        should_backup = False
        digest_changed = self.encipher_manager.check_if_has_changed(self.backup_file, digest)

        if self.backup_on_change:
            if digest_changed:
                self.logger.info("Task [%s]: 文件摘要已变化", self.task_name)
                should_backup = True
            else:
                self.logger.info(
                    "Task [%s]: 文件摘要未变化，跳过任务。", self.task_name)
                should_backup = False
        else:
            # 直接备份
            should_backup = True

        if should_backup:
            # 重命名文件
            now = datetime.datetime.now()
            output_file_name = "{}.{}_{}".format(
                self.task_name, now.strftime("%y%m%d_%H%M%S"), digest)
            self.set_output_file_name_and_full_path(output_file_name)

            self.logger.info("Task [%s]: copy file from %s to %s",
                             self.task_name, self.backup_file, self.output_full_path)
            shutil.copyfile(self.backup_file, self.output_full_path)

            if digest_changed:
                self.encipher_manager.set_value(self.backup_file, digest)

            result = True
        else:
            result = False

        self.logger.info("Task [%s]: 结束备份.", self.task_name)
        return result
