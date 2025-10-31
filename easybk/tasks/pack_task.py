"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import datetime
import logging
import os

from .task import Task
from ..encipher_manager import EncipherManager


class PackTask(Task):
    """
    打包备份任务

    参数:
        task_name  任务名
        output_dir  备份输出目录
        tar_run_dir  tar 命令运行路径
        backup_list  备份列表
    """

    def __init__(self, task_name: str, output_dir: str, tar_run_dir: str, backup_list: list):
        """
        参数:
            task_name  任务名
            output_dir  备份输出目录
            tar_run_dir  tar 命令运行路径
            backup_list  备份列表
        """
        # super(PackTask, self).__init__(name)
        Task.__init__(self, task_name, output_dir)
        self.logger = logging.getLogger("PackTask")
        self.tar_run_dir = tar_run_dir
        self.backup_list = backup_list

    def do_task(self) -> bool:
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始打包.", self.task_name)

        # 临时打包文件名
        temp_file = os.path.join(
            self.output_dir, "{}_backup_temp.tgz".format(self.task_name))

        # 使用tar打包需要备份的文件
        os.system("cd {dir} && tar zcf {file} {cmd_args}"
                  .format(dir=self.tar_run_dir,
                          file=temp_file,
                          cmd_args=" ".join(self.backup_list)))
        self.logger.info(
            "Task [%s]: create temp file %s", self.task_name, temp_file)

        # 计算压缩包的md5
        md5 = EncipherManager.md5sum(temp_file)
        self.logger.info("Task [%s]: md5sum is %s", self.task_name, md5)

        # 重命名打包文件
        now = datetime.datetime.now()
        output_file_name = "{}_backup_{}_{}.tgz".format(
            self.task_name, now.strftime("%y%m%d_%H%M%S"), md5)
        self.set_output_file_name_and_full_path(output_file_name)

        os.rename(temp_file, self.output_full_path)
        self.logger.info("Task [%s]: rename file to %s",
                         self.task_name, self.output_full_path)

        self.logger.info("Task [%s]: 结束打包.", self.task_name)

        return True
