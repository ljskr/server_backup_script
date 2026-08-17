"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import datetime
import logging
import os
import subprocess
import tempfile

from .task import Task
from ..encipher_manager import EncipherManager


STDERR_LOG_TAIL_BYTES = 64 * 1024


def _read_stderr_tail(file_path: str) -> str:
    """读取 stderr 日志尾部，避免错误日志过大时占用过多内存。"""
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as error_file:
        if file_size > STDERR_LOG_TAIL_BYTES:
            error_file.seek(-STDERR_LOG_TAIL_BYTES, os.SEEK_END)
        content = error_file.read().decode("utf-8", errors="replace").strip()
    if file_size > STDERR_LOG_TAIL_BYTES:
        return "<stderr 过长，仅显示最后 64 KiB>\n{}".format(content)
    return content


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

        fd, temp_file = tempfile.mkstemp(
            prefix="{}_backup_".format(self.task_name), suffix=".tgz", dir=self.output_dir)
        os.close(fd)
        stderr_fd, stderr_path = tempfile.mkstemp(
            prefix="{}_tar_".format(self.task_name), suffix=".stderr.log",
            dir=self.output_dir)
        try:
            with os.fdopen(stderr_fd, "wb") as stderr_file:
                try:
                    subprocess.run(
                        ["tar", "zcf", temp_file, *self.backup_list],
                        cwd=self.tar_run_dir,
                        check=True,
                        stderr=stderr_file,
                    )
                except subprocess.CalledProcessError as exc:
                    stderr_file.flush()
                    tar_error = _read_stderr_tail(stderr_path)
                    self.logger.error(
                        "Task [%s]: tar 失败，退出码=%s，stderr=%s",
                        self.task_name, exc.returncode,
                        tar_error or "<无错误输出>")
                    raise
            subprocess.run(["tar", "tzf", temp_file], check=True,
                           stdout=subprocess.DEVNULL)
            self.logger.info("Task [%s]: create temp file %s", self.task_name, temp_file)

            digest = EncipherManager.digest(temp_file)
            self.logger.info("Task [%s]: SHA-256 is %s", self.task_name, digest)

            now = datetime.datetime.now()
            output_file_name = "{}_backup_{}_{}.tgz".format(
                self.task_name, now.strftime("%y%m%d_%H%M%S"), digest)
            self.set_output_file_name_and_full_path(output_file_name)
            os.replace(temp_file, self.output_full_path)
            self.logger.info("Task [%s]: rename file to %s",
                             self.task_name, self.output_full_path)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(stderr_path):
                os.remove(stderr_path)

        self.logger.info("Task [%s]: 结束打包.", self.task_name)

        return True
