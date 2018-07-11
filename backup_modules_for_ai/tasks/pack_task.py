# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import datetime
import logging
import os

from .task import Task
from ..encipher_manager import EncipherManager

class PackTask(Task):
    """
    打包备份任务
    """

    def __init__(self, name, output_dir, tar_run_dir, backup_list, remote_folder=None):
        """
        入参:
            name  任务名
            output_dir  本地备份路径
            tar_run_dir  tar 命令运行路径
            backup_list  备份列表
            remote_folder  远程备份目录
        """
        super(PackTask, self).__init__(name, remote_folder)
        self.logger = logging.getLogger("PackTask")
        self.name = name
        self.output_dir = output_dir
        self.tar_run_dir = tar_run_dir
        self.backup_list = backup_list

    def run(self):
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始打包.", self.name)

        # 创建目录
        if not os.path.exists(self.output_dir):
            self.logger.info("Task [%s]: create folder %s", self.name, self.output_dir)
            os.mkdir(self.output_dir)

        # 临时打包文件名
        temp_file = os.path.join(self.output_dir, "{}_backup_temp.tgz".format(self.name))

        # 使用tar打包需要备份的文件
        os.system("cd {dir} && tar zcf {file} {cmd_args}"
                .format(dir=self.tar_run_dir, 
                    file=temp_file,
                    cmd_args=" ".join(self.backup_list)))
        self.logger.info("Task [%s]: create temp file %s", self.name, temp_file)

        # 计算压缩包的md5
        md5 = EncipherManager.md5sum(temp_file)
        self.logger.info("Task [%s]: md5sum is %s", self.name, md5)

        # 重命名打包文件
        now = datetime.datetime.now()
        self.output_file_name = "{}_backup_{}_{}.tgz".format(self.name, now.strftime("%y%m%d_%H%M%S"), md5)
        self.output_full_path = os.path.join(self.output_dir, self.output_file_name)
        os.rename(temp_file, self.output_full_path)
        self.logger.info("Task [%s]: rename file to %s", self.name, self.output_full_path)

        self.logger.info("Task [%s]: 结束打包.", self.name)

        return True

    def get_output_file_name(self):
        return self.output_file_name

    def get_output_full_path(self):
        return self.output_full_path
