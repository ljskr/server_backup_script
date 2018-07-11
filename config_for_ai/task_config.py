# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-11

# 定义任务，所有任务的定义在此文件中定义。
# 后续可以考虑做成配置文件的方式，动态生成任务类。

from backup_modules_for_ai.tasks import *

def get_task_list():
    task_list = []

    # PackTask 示例
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

    task_list.append(dokuwiki_task)

    return task_list

