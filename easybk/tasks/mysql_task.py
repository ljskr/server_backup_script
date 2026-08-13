"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-11
"""


import datetime
import logging
import os
import shlex
import subprocess
import tempfile

from .task import Task
from ..encipher_manager import EncipherManager


class MysqlTask(Task):
    """
    Mysql 数据库备份任务

    参数:
        task_name  任务名
        output_dir  备份输出目录
        dump_option  运行 mysqldump 所需参数
    """

    def __init__(self, task_name: str, output_dir: str, dump_option):
        """
        参数:
            task_name  任务名
            output_dir  备份输出目录
            dump_option  运行 mysqldump 所需参数
        """
        # super(MysqlTask, self).__init__(name)
        Task.__init__(self, task_name, output_dir)
        self.logger = logging.getLogger("MysqlTask")
        self.dump_option = dump_option

    def do_task(self) -> bool:
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始备份Mysql.", self.task_name)

        dump_options = (self.dump_option if isinstance(self.dump_option, list)
                        else shlex.split(self.dump_option))
        sql_fd, sql_path = tempfile.mkstemp(
            prefix="{}_backup_".format(self.task_name), suffix=".sql", dir=self.output_dir)
        os.close(sql_fd)
        archive_fd, archive_path = tempfile.mkstemp(
            prefix="{}_backup_".format(self.task_name), suffix=".tgz", dir=self.output_dir)
        os.close(archive_fd)

        try:
            with open(sql_path, "wb") as output_file:
                subprocess.run(["mysqldump", *dump_options], stdout=output_file, check=True)

            subprocess.run(
                ["tar", "zcf", archive_path, os.path.basename(sql_path)],
                cwd=self.output_dir,
                check=True,
            )
            subprocess.run(["tar", "tzf", archive_path], check=True,
                           stdout=subprocess.DEVNULL)
            self.logger.info("Task [%s]: create temp file %s", self.task_name, archive_path)

            digest = EncipherManager.digest(archive_path)
            self.logger.info("Task [%s]: SHA-256 is %s", self.task_name, digest)

            now = datetime.datetime.now()
            output_file_name = "{}_backup.sql.{}_{}.tgz".format(
                self.task_name, now.strftime("%y%m%d_%H%M%S"), digest)
            self.set_output_file_name_and_full_path(output_file_name)
            os.replace(archive_path, self.output_full_path)
            self.logger.info("Task [%s]: rename file to %s",
                             self.task_name, self.output_full_path)
        finally:
            for temp_path in (sql_path, archive_path):
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        self.logger.info("Task [%s]: 结束备份Mysql.", self.task_name)

        return True
