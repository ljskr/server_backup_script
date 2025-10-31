"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-11
"""


import datetime
import logging
import os

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

    def __init__(self, task_name: str, output_dir: str, dump_option: str):
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

        # 导出 mysql
        temp_sql_file = "{}_backup.sql".format(self.task_name)
        os.system("mysqldump {cmd_args} > {output_file}"
                  .format(cmd_args=self.dump_option,
                          output_file=os.path.join(self.output_dir, temp_sql_file)))

        # 临时打包文件名
        temp_file = os.path.join(
            self.output_dir, "{}_backup_temp.tgz".format(self.task_name))

        # 使用tar打包需要备份的文件
        os.system("cd {dir} && tar zcf {file} {cmd_args} --remove-files"
                  .format(dir=self.output_dir,
                          file=temp_file,
                          cmd_args=temp_sql_file))
        self.logger.info(
            "Task [%s]: create temp file %s", self.task_name, temp_file)

        # 计算压缩包的md5
        md5 = EncipherManager.md5sum(temp_file)
        self.logger.info("Task [%s]: md5sum is %s", self.task_name, md5)

        # 重命名打包文件
        now = datetime.datetime.now()
        output_file_name = "{}_backup.sql.{}_{}.tgz".format(
            self.task_name, now.strftime("%y%m%d_%H%M%S"), md5)
        self.set_output_file_name_and_full_path(output_file_name)

        os.rename(temp_file, self.output_full_path)
        self.logger.info("Task [%s]: rename file to %s",
                         self.task_name, self.output_full_path)

        self.logger.info("Task [%s]: 结束备份Mysql.", self.task_name)

        return True
