# -*- coding: utf8 -*-

import logging.config
import yaml

from backup_modules_for_ai import *

from config_for_ai import config
from config_for_ai.task_config import task_list

logger = None
# 初始化 logging
def init_logger():
    global logger
    logging.config.dictConfig(yaml.load(open(config.LOG_CONFIG)))
    logger = logging.getLogger()


def main():
    init_logger()

    logger.info("准备执行备份任务！ ")
    encipher_manager = EncipherManager()
    encipher_manager.load_data_from_file(config.ENCIPHER_FILE)

    task_manager = TaskManager()

    for task in task_list:
        task_manager.add_task(task)

    task_manager.run_all_task()

    encipher_manager.save_data_to_file()
    logger.info("所有备份任务执行完毕！ ")


if __name__ == "__main__":
    main()
