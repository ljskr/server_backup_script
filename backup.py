# -*- coding: utf8 -*-

import logging.config
import yaml

from backup_modules_for_ai.task_manager import TaskManager
from backup_modules_for_ai.pack_task import PackTask

logger = None
# 初始化 logging
def init_logger():
    global logger
    logging.config.dictConfig(yaml.load(open("./log.conf")))
    logger = logging.getLogger()

if __name__ == "__main__":
    init_logger()

    logger.info("准备执行备份任务！ ")
    task_manager = TaskManager()

    # dokuwiki_task = PackTask("dokuwiki", "/home/liujun/test/dokuwiki", "/home/liujun/Pictures/", ["Screenshot_2018-05-31_10-31-10.png", "Screenshot_2018-06-01_16-09-53.png"], "dokuwiki")
    dokuwiki_task = PackTask(name = "dokuwiki", output_dir = "/home/ai/backups/dokuwiki", 
                            tar_run_dir = "/var/www", 
                            backup_list = [ "dokuwiki/conf",
                                            "dokuwiki/data/attic",
                                            "dokuwiki/data/meta",
                                            "dokuwiki/data/pages",
                                            "dokuwiki/data/media",
                                            "dokuwiki/data/media_attic",
                                            "dokuwiki/data/media_meta"], 
                            remote_folder = "dokuwiki")
    task_manager.add_task(dokuwiki_task)

    task_manager.run_all_task()

    logger.info("所有备份任务执行完毕！ ")

