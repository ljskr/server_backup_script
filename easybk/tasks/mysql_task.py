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
        name  任务名
        output_dir  本地备份路径
        dump_option  运行 mysqldump 所需参数
    """

    def __init__(self, name: str, output_dir: str, dump_option: str):
        """
        参数:
            name  任务名
            output_dir  本地备份路径
            dump_option  运行 mysqldump 所需参数
        """
        # super(MysqlTask, self).__init__(name)
        Task.__init__(self, name)
        self.logger = logging.getLogger("PackTask")
        self.name = name
        self.output_dir = output_dir
        self.dump_option = dump_option

    def do_task(self) -> bool:
        """
        执行任务
        返回最终打包好的文件名和文件路径。
        """
        self.logger.info("Task [%s]: 开始备份Mysql.", self.name)

        # 创建目录
        if not os.path.exists(self.output_dir):
            self.logger.info("Task [%s]: create folder %s",
                             self.name, self.output_dir)
            os.mkdir(self.output_dir)

        # 导出 mysql
        temp_sql_file = "{}_backup.sql".format(self.name)
        os.system("mysqldump {cmd_args} > {output_file}"
                  .format(cmd_args=self.dump_option,
                          output_file=os.path.join(self.output_dir, temp_sql_file)))

        # 临时打包文件名
        temp_file = os.path.join(
            self.output_dir, "{}_backup_temp.tgz".format(self.name))

        # 使用tar打包需要备份的文件
        os.system("cd {dir} && tar zcf {file} {cmd_args} --remove-files"
                  .format(dir=self.output_dir,
                          file=temp_file,
                          cmd_args=temp_sql_file))
        self.logger.info(
            "Task [%s]: create temp file %s", self.name, temp_file)

        # 计算压缩包的md5
        md5 = EncipherManager.md5sum(temp_file)
        self.logger.info("Task [%s]: md5sum is %s", self.name, md5)

        # 重命名打包文件
        now = datetime.datetime.now()
        self.output_file_name = "{}_backup.sql.{}_{}.tgz".format(
            self.name, now.strftime("%y%m%d_%H%M%S"), md5)
        self.output_full_path = os.path.join(
            self.output_dir, self.output_file_name)
        os.rename(temp_file, self.output_full_path)
        self.logger.info("Task [%s]: rename file to %s",
                         self.name, self.output_full_path)

        self.logger.info("Task [%s]: 结束备份Mysql.", self.name)

        return True

    def get_output_file_name(self) -> str:
        return self.output_file_name

    def get_output_full_path(self) -> str:
        return self.output_full_path
