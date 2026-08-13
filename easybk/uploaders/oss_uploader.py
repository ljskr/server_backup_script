"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-10
"""

import logging
import os
import posixpath
import uuid

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
        try:
            import oss2
        except ImportError:
            raise ImportError("oss2 is not installed, please install it first")
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
        access_id: oss 认证 ID
        access_key: oss 认证密钥
        endpoint: oss 认证端点
        bucket_name: oss 认证 bucket 名称
    """

    def __init__(self, name: str, access_id: str, access_key: str, endpoint: str,
                 bucket_name: str, use_temp_object: bool = True):
        Uploader.__init__(self, name)
        self.logger = logging.getLogger("OSSUploader")
        self.oss_bucket = OSSBucket(access_id, access_key, endpoint, bucket_name)
        self.use_temp_object = use_temp_object

    def do_upload(self, task: Task, remote_dir: str) -> bool:
        """
        执行上传任务
        参数:
            task: 备份任务
            remote_dir: 远程目录
        """
        remote_full_path = posixpath.join(remote_dir, task.get_output_file_name())
        local_full_path = task.get_output_full_path()
        self.logger.info("OSSUploader: 上传文件: [%s] -> [%s]", local_full_path, remote_full_path)
        bucket = self.oss_bucket.get_bucket()
        local_size = os.path.getsize(local_full_path)

        if not self.use_temp_object:
            bucket.put_object_from_file(remote_full_path, local_full_path)
            final_size = bucket.head_object(remote_full_path).content_length
            if final_size != local_size:
                raise IOError("OSS 上传后大小校验失败: 本地={}, 远端={}".format(
                    local_size, final_size))
        else:
            temp_remote_path = "{}.part-{}".format(remote_full_path, uuid.uuid4().hex)
            try:
                bucket.put_object_from_file(temp_remote_path, local_full_path)
                uploaded_size = bucket.head_object(temp_remote_path).content_length
                if uploaded_size != local_size:
                    raise IOError("OSS 上传后大小校验失败: 本地={}, 远端={}".format(
                        local_size, uploaded_size))
                bucket.copy_object(self.oss_bucket.bucket_name, temp_remote_path, remote_full_path)
                final_size = bucket.head_object(remote_full_path).content_length
                if final_size != local_size:
                    raise IOError("OSS 最终对象大小校验失败: 本地={}, 远端={}".format(
                        local_size, final_size))
            finally:
                try:
                    bucket.delete_object(temp_remote_path)
                except Exception:
                    self.logger.warning("OSSUploader: 清理远端临时对象失败: %s", temp_remote_path)
        self.logger.info("OSSUploader: 上传文件完成: [%s] -> [%s]", local_full_path, remote_full_path)
        return True
