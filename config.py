import os
import datetime
import logging.config

from easybk import TaskManager, UploadManager, UploadTask
from easybk import PackTask, MysqlTask, SingleFileTask, OSSUploader, FTPUploader


def init_task(task_manager: TaskManager, upload_manager: UploadManager):
    """
    配置任务信息
    """

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    output_base_dir = os.path.join("/root/backup/data", date_str)
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)

    # PackTask 示例
    dokuwiki_task = PackTask(name="dokuwiki", output_dir=os.path.join(output_base_dir, "dokuwiki"),
                             tar_run_dir="/var/www",
                             backup_list=["dokuwiki/conf",
                                          "dokuwiki/data/attic",
                                          "dokuwiki/data/meta",
                                          "dokuwiki/data/pages",
                                          "dokuwiki/data/media",
                                          "dokuwiki/data/media_attic",
                                          "dokuwiki/data/media_meta"])

    # MysqlTask 示例
    db1_task = MysqlTask(name="db1", output_dir=os.path.join(output_base_dir, "mydb"),
                         dump_option="-u root --databases mydb")#, remote_sub_dir="mydb")

    # SingleFileTask 示例
    file1_task = SingleFileTask(name="file1", output_dir=os.path.join(output_base_dir, "myfile"),
                                source_file="/etc/profile")#, remote_sub_dir="myfile")

    task_manager.add_task(dokuwiki_task)
    task_manager.add_task(db1_task)
    task_manager.add_task(file1_task)

    # 定义上传器
    oss_uploader = OSSUploader("oss_uploader", "access_id", "access_key", "endpoint", "bucket_name")
    ftp_uploader = FTPUploader("ftp_uploader", "host", 21, "username", "password")

    # OSS 上传示例
    oss_upload_task = UploadTask(task=dokuwiki_task, uploader=oss_uploader, remote_dir=os.path.join(date_str, "dokuwiki"))
    upload_manager.add_upload_task(oss_upload_task)

    # FTP 上传示例
    ftp_upload_task = UploadTask(task=dokuwiki_task, uploader=ftp_uploader, remote_dir=os.path.join(date_str, "dokuwiki"))
    upload_manager.add_upload_task(ftp_upload_task)



