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
        name  任务名
        output_dir  本地备份路径
        source_file  需要备份的文件
        backup_on_change 是否在只有变更的时候才进行备份
    """

    def __init__(self, name: str, output_dir: str, source_file: str, backup_on_change: bool = False):
        """
        参数:
            name  任务名
            output_dir  本地备份路径
            source_file  需要备份的文件
        """
        # super(SingleFileTask, self).__init__(name)
        Task.__init__(self, name)
        self.logger = logging.getLogger("SingleFileTask")
        self.name = name
        self.output_dir = output_dir
        self.backup_file = source_file
        self.encipher_manager = EncipherManager()
        self.backup_on_change = backup_on_change


    def do_task(self) -> bool:
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始备份单文件.", self.name)

        # 创建目录
        if not os.path.exists(self.output_dir):
            self.logger.info("Task [%s]: create folder %s",
                             self.name, self.output_dir)
            os.mkdir(self.output_dir)

        # 计算需要备份的文件的md5
        md5 = EncipherManager.md5sum(self.backup_file)
        self.logger.info("Task [%s]: md5sum is %s", self.name, md5)

        should_backup = False
        # 判断 md5 是否有变更。
        md5_changed = self.encipher_manager.check_if_has_changed(self.backup_file, md5)

        if self.backup_on_change:
            if md5_changed:
                self.logger.info("Task [%s]: md5 has changed", self.name)
                should_backup = True
            else:
                self.logger.info(
                    "Task [%s]: md5 does not change, skip this task.", self.name)
                should_backup = False
        else:
            # 直接备份
            should_backup = True

        if should_backup:
            # 重命名文件
            now = datetime.datetime.now()
            self.output_file_name = "{}.{}_{}".format(
                self.name, now.strftime("%y%m%d_%H%M%S"), md5)
            self.output_full_path = os.path.join(
                self.output_dir, self.output_file_name)

            self.logger.info("Task [%s]: copy file from %s to %s",
                             self.name, self.backup_file, self.output_full_path)
            shutil.copyfile(self.backup_file, self.output_full_path)

            if md5_changed:
                self.encipher_manager.set_value(self.backup_file, md5)

            result = True
        else:
            result = False

        self.logger.info("Task [%s]: 结束备份.", self.name)
        return result

    def get_output_file_name(self) -> str:
        return self.output_file_name

    def get_output_full_path(self) -> str:
        return self.output_full_path
