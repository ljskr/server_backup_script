"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import logging
from concurrent.futures import ThreadPoolExecutor

from .encipher_manager import EncipherManager
from .tasks import Task


class TaskManager():
    """
    任务管理器
    """

    def __init__(self):
        self.logger = logging.getLogger("TaskManager")
        self.task_list = []
        self.encipher_manager = EncipherManager()
        self.encipher_file = "md5_list.txt"

    def set_encipher_file(self, path: str):
        """
        加载配置文件
        """
        self.encipher_file = path

    def add_task(self, task: Task):
        """
        添加任务
        """
        if task is None:
            raise ValueError("task must have value!")
        if not isinstance(task, Task):
            raise ValueError("task must be an instance of Task!")

        self.task_list.append(task)


    def run_all_task(self, use_thread_pool: bool = True, max_workers: int = 3):
        """
        运行所有备份任务
        :param use_thread_pool: 是否使用线程池并发执行任务
        :param max_workers: 线程池最大并发数
        """
        self.logger.info("开始执行任务！")
        # 加载 encipher 文件
        self.encipher_manager.load_data_from_file(self.encipher_file)

        self.logger.info("准备执行备份任务！ ")

        task_count = len(self.task_list)
        self.logger.info("总备份任务数: %s", task_count)

        def _run_task(index, tsk):
            try:
                self.logger.info("准备执行第 %s 个备份任务，[%s]", index, tsk.get_name())
                tsk.run()
            except Exception:
                self.logger.exception("Task [%s]: 备份发生异常。", tsk.get_name())

        if use_thread_pool and task_count > 0:
            with ThreadPoolExecutor(max_workers=min(max_workers, task_count)) as executor:
                futures = [executor.submit(_run_task, idx, t) for idx, t in enumerate(self.task_list, start=1)]
                for f in futures:
                    f.result()
        else:
            cur_index = 1
            for task in self.task_list:
                try:
                    self.logger.info(
                        "准备执行第 %s 个备份任务，[%s]", cur_index, task.get_name())
                    task.run()
                except Exception:
                    self.logger.exception("Task [%s]: 备份发生异常。", task.get_name())
                cur_index += 1

        # 保存 encipher 文件
        self.encipher_manager.save_data_to_file()
        self.logger.info("备份任务执行完毕！ ")

