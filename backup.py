"""
示例程序
"""

import logging.config

from easybk import TaskManager, PackTask, MysqlTask, SingleFileTask
from easybk.uploaders.oss_uploader import OSSBucket, OSSUploader


def init_logger():
    """
    初始化 logging
    """
    logging.config.fileConfig("./logger.conf")


def init_task(manager: TaskManager):
    """
    配置任务信息
    """

    # PackTask 示例
    dokuwiki_task = PackTask(name="dokuwiki", output_dir="/root/backup/data/dokuwiki",
                             tar_run_dir="/var/www",
                             backup_list=["dokuwiki/conf",
                                          "dokuwiki/data/attic",
                                          "dokuwiki/data/meta",
                                          "dokuwiki/data/pages",
                                          "dokuwiki/data/media",
                                          "dokuwiki/data/media_attic",
                                          "dokuwiki/data/media_meta"])#,
                             #remote_folder="dokuwiki")

    # MysqlTask 示例
    db1_task = MysqlTask(name="db1", output_dir="/root/backup/data/mydb",
                         dump_option="-u root --databases mydb")#, remote_folder="mydb")

    # SingleFileTask 示例
    file1_task = SingleFileTask(name="file1", output_dir="/root/backup/data/myfile",
                                source_file="/etc/profile")#, remote_folder="myfile")

    manager.add_task(dokuwiki_task)
    manager.add_task(db1_task)
    manager.add_task(file1_task)

    # OSS 上传示例
    oss_bucket = OSSBucket("access_id", "access_key", "endpoint", "bucket_name")
    oss_uploader = OSSUploader("oss_uploader", oss_bucket, "myfolder")
    oss_uploader.add_task(file1_task)

    manager.add_uploader(oss_uploader)


def main():
    """
    主入口
    """
    init_logger()

    task_manager = TaskManager()
    init_task(task_manager)
    task_manager.run_all_task()


if __name__ == "__main__":
    main()
