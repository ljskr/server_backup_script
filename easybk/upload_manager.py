"""
Author: liujun (ljskryj@163.com)
Date: 2025-10-31
"""


import logging
from concurrent.futures import ThreadPoolExecutor

from .tasks import Task
from .uploaders import Uploader

class UploadTask():
    """
    上传任务类
    表示使用 uploader 对 task 进行上传

    参数:
        task: 备份任务实例
        uploader: 上传器实例
        remote_dir: 远程目录
    """

    def __init__(self, task: Task, uploader: Uploader, remote_dir: str = ""):
        """
        参数:
            task: 备份任务实例
            uploader: 上传器实例
            remote_dir: 远程目录
        """
        if task is None:
            raise ValueError("task must have value!")
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task!")
        if uploader is None:
            raise ValueError("uploader must have value!")
        if not isinstance(uploader, Uploader):
            raise ValueError("uploader must be an instance of Uploader!")

        self.logger = logging.getLogger("UploadTask")
        self.task = task
        self.uploader = uploader
        self.remote_dir = remote_dir

    def get_task(self) -> Task:
        """
        获取备份任务实例
        """
        return self.task

    def get_uploader(self) -> Uploader:
        """
        获取上传器实例
        """
        return self.uploader

    def run(self) -> bool:
        """
        执行上传任务
        使用 uploader 对 task 进行上传
        返回值:
            result bool 类型，代表成功或者失败。
        """
        try:
            if not self.task.get_result():
                self.logger.info(
                    "UploadTask [%s -> %s]: 任务[%s]未备份，不需要上传。",
                    self.task.get_name(), self.uploader.get_name(), self.task.get_name())
                return False

            self.logger.info(
                "UploadTask [%s -> %s]: 准备上传任务[%s]",
                self.task.get_name(), self.uploader.get_name(), self.task.get_name())

            result = self.uploader.do_upload(self.task, self.remote_dir)

            if result:
                self.logger.info(
                    "UploadTask [%s -> %s]: 任务[%s]上传完成",
                    self.task.get_name(), self.uploader.get_name(), self.task.get_name())
            else:
                self.logger.warning(
                    "UploadTask [%s -> %s]: 任务[%s]上传失败",
                    self.task.get_name(), self.uploader.get_name(), self.task.get_name())

            return result
        except Exception:
            self.logger.exception(
                "UploadTask [%s -> %s]: 上传发生异常",
                self.task.get_name(), self.uploader.get_name())
            return False

    def get_remote_dir(self) -> str:
        """
        获取远程目录
        """
        return self.remote_dir


class UploadManager():
    """
    上传管理器
    """

    def __init__(self):
        self.logger = logging.getLogger("UploadManager")
        self.upload_task_list = []

    def add_upload_task(self, upload_task: UploadTask):
        """
        添加上传任务
        """
        if upload_task is None:
            raise ValueError("upload_task must have value!")
        if not isinstance(upload_task, UploadTask):
            raise ValueError("upload_task must be an instance of UploadTask!")

        self.upload_task_list.append(upload_task)

    def run_all_upload(self, use_thread_pool: bool = False, max_workers: int = 3):
        """
        运行所有上传任务
        :param use_thread_pool: 是否使用线程池并发执行任务
        :param max_workers: 线程池最大并发数
        """
        self.logger.info("开始执行上传任务！")

        upload_task_count = len(self.upload_task_list)
        self.logger.info("总上传任务数: %s", upload_task_count)

        if upload_task_count == 0:
            self.logger.info("没有上传任务，跳过上传任务。")
            return

        def _run_upload_task(index, ut):
            try:
                self.logger.info("准备执行第 %s 个上传任务: [%s -> %s]", index, ut.get_task().get_name(), ut.get_uploader().get_name())
                ut.run()
                self.logger.info("上传任务 [%s]: 执行完成: [%s -> %s]", index, ut.get_task().get_name(), ut.get_uploader().get_name())
            except Exception:
                self.logger.exception("UploadTask [%s]: 执行发生异常。: [%s -> %s]", index, ut.get_task().get_name(), ut.get_uploader().get_name())

        if use_thread_pool and upload_task_count > 0:
            with ThreadPoolExecutor(max_workers=min(max_workers, upload_task_count)) as executor:
                futures = [executor.submit(_run_upload_task, idx, ut) for idx, ut in enumerate(self.upload_task_list, start=1)]
                for f in futures:
                    f.result()
        else:
            cur_index = 1
            for upload_task in self.upload_task_list:
                try:
                    self.logger.info("准备执行第 %s 个上传任务: [%s -> %s]", cur_index, upload_task.get_task().get_name(), upload_task.get_uploader().get_name())
                    upload_task.run()
                    self.logger.info("上传任务 [%s]: 执行完成: [%s -> %s]", cur_index, upload_task.get_task().get_name(), upload_task.get_uploader().get_name())
                except Exception:
                    self.logger.exception("UploadTask [%s]: 执行发生异常。: [%s -> %s]", cur_index, upload_task.get_task().get_name(), upload_task.get_uploader().get_name())
                cur_index += 1

        self.logger.info("上传任务执行完毕！")

