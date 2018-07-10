# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-10

import hashlib

def md5sum(file_name):
    """
    计算文件md5值
 
    参数： 文件名
    返回值： md5
    """
    def read_chunks(fh):
        fh.seek(0)
        chunk = fh.read(8096)
        while chunk:
            yield chunk
            chunk = fh.read(8096)
        else:
            fh.seek(0)  # 最后重置游标

    md5 = hashlib.md5()
    with open(file_name, "rb") as fh:
        for chunk in read_chunks(fh):
            md5.update(chunk)
    return md5.hexdigest()
