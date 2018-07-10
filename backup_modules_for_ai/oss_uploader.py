# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import logging
import oss2

import oss2_config as config

logger = logging.getLogger("oss_uploader")

def upload(local_file, remote_file):
    """
    上传文件至OSS中

    入参：
        local_file: 本地文件路径
        remote_file: 运程文件名
    """
    auth = oss2.Auth(config.aliyum_access_id, config.aliyum_access_key)
    bucket = oss2.Bucket(auth, config.aliyum_endpoint, config.aliyum_bucket_name)
    
    bucket.put_object_from_file(remote_file, local_file)


def batch_upload(file_lists):
    """
    批量上传

    入参：
        file_lists: 一个列表，列表的元素是一个 tuple ， tuple 格式为 (remote_key, local_file)

    """
    if file_lists is None:
        raise ValueError('file_lists must be defined.')
    elif not isinstance(file_lists, list):
        raise ValueError('file_lists must be a list.')
    elif len(file_lists) == 0:
        return

    auth = oss2.Auth(config.aliyum_access_id, config.aliyum_access_key)
    bucket = oss2.Bucket(auth, config.aliyum_endpoint, config.aliyum_bucket_name)

    for element in file_lists:
        if not isinstance(element, tuple):
            logger.error("file list 中的元素不是一个 tuple. element=%s", element)
            continue

        bucket.put_object_from_file(element[0], element[1])
