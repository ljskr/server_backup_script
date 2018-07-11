# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import datetime
import logging
import os
import shutil

from .task import Task
from ..encipher_manager import EncipherManager

class SingleFileTask(Task):
    """
    单文件备份任务。只在有变更的情况下进行备份。
    """

    def __init__(self, name, output_dir, source_file, remote_folder=None):
        """
        入参:
            name  任务名
            output_dir  本地备份路径
            source_file  需要备份的文件
            remote_folder  远程备份目录
        """
        super(SingleFileTask, self).__init__(name, remote_folder)
        self.logger = logging.getLogger("SingleFileTask")
        self.name = name
        self.output_dir = output_dir
        self.backup_file = source_file
        self.encipher_manager = EncipherManager()

    def run(self):
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始备份单文件.", self.name)

        # 创建目录
        if not os.path.exists(self.output_dir):
            self.logger.info("Task [%s]: create folder %s", self.name, self.output_dir)
            os.mkdir(self.output_dir)

        # 计算需要备份的文件的md5
        md5 = EncipherManager.md5sum(self.backup_file)
        self.logger.info("Task [%s]: md5sum is %s", self.name, md5)

        if self.encipher_manager.check_if_has_changed(self.backup_file, md5):
            self.logger.info("Task [%s]: md5 has changed", self.name)

            # 重命名文件
            now = datetime.datetime.now()
            self.output_file_name = "{}.{}_{}".format(self.name, now.strftime("%y%m%d_%H%M%S"), md5)
            self.output_full_path = os.path.join(self.output_dir, self.output_file_name)

            self.logger.info("Task [%s]: copy file from %s to %s", self.name, self.backup_file, self.output_full_path)
            shutil.copyfile(self.backup_file, self.output_full_path)

            self.encipher_manager.set_value(self.backup_file, md5)

            result =  True
        else:
            self.logger.info("Task [%s]: md5 does not change, skip this task.", self.name)
            result = False

        self.logger.info("Task [%s]: 结束备份.", self.name)
        return result

    def get_output_file_name(self):
        return self.output_file_name

    def get_output_full_path(self):
        return self.output_full_path
