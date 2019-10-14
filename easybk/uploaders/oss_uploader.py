"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""


import logging
import oss2

from .uploader import Uploader, Task


class OSSBucket():
    """
    阿里云 oss bucket
    """

    def __init__(self, access_id: str, access_key: str, endpoint: str, bucket_name: str):
        self.access_id = access_id
        self.access_key = access_key
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        self.has_connect = False
        self.auth = None
        self.bucket = None

    def connect(self):
        """
        连接
        """
        self.auth = oss2.Auth(self.access_id, self.access_key)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        self.has_connect = True

    def get_auth(self):
        """
        获取 auth
        """
        if not self.has_connect:
            self.connect()
        return self.auth

    def get_bucket(self):
        """
        获取 bucket
        """
        if not self.has_connect:
            self.connect()
        return self.bucket


class OSSUploader(Uploader):
    """
    阿里云 OSS 上传器

    参数：
        name: 本实例名称
        oss_bucket: oss 认证实例
        folder: oss 远程目录
    """

    def __init__(self, name: str, oss_bucket: OSSBucket, folder: str = None):
        Uploader.__init__(self, name)
        self.logger = logging.getLogger("OSSUploader")
        self.oss_bucket = oss_bucket
        self.folder = folder

    def do_upload(self, task: Task) -> bool:
        """
        执行上传任务
        """
        remote_folder = self.get_folder()
        if remote_folder is not None:
            remote_file = "{}/{}".format(remote_folder,
                                         task.get_output_file_name())
        else:
            remote_file = task.get_output_file_name()
        self.oss_bucket.get_bucket().put_object_from_file(
            remote_file, task.get_output_full_path())
        return True

    def get_folder(self) -> str:
        """
        获取远程目录
        """
        return self.folder
