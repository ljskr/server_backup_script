import logging.config

from easybk import TaskManager, PackTask, MysqlTask, SingleFileTask, OSSUploader, FTPUploader


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
    oss_uploader = OSSUploader("oss_uploader", "access_id", "access_key", "endpoint", "bucket_name", "myfolder")
    oss_uploader.add_task(file1_task)

    # FTP 上传示例
    ftp_uploader = FTPUploader("ftp_uploader", "host", "port", "username", "password", "myfolder")
    ftp_uploader.add_task(file1_task)

    manager.add_uploader(oss_uploader)
    manager.add_uploader(ftp_uploader)


