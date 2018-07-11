# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-07-11

import hashlib
import logging

from .singleton import Singleton

class EncipherManager(Singleton):
    """
    文件摘要管理器。 单例。
    """

    def __init__(self):
        if not hasattr(self, '_has_init'):
            self.file_dict = {}
            self.changed = False
            self.file_name = None
            self.logger = logging.getLogger("EncipherManager")
            self._has_init = True

    def load_data_from_file(self, file_name):
        """
        从文件加载摘要列表
        """
        with open(file_name, "r") as fh:
            lines = fh.readlines()
            for line in lines:
                cols = line.split()
                self.file_dict[cols[1]] = cols[0]
        self.changed = False
        self.file_name = file_name
        self.logger.info("已加载 %s 条数据", len(self.file_dict))

    def save_data_to_file(self, file_name = None, force = False):
        """
        保存摘要列表到文件中。

        inputs:
            file_name: 保存的文件名。若为 None ，则保存到读取的源文件中。
            force: 是否强制写入。若数据无变更，默认不会重新保存。设置此字段可强制重新保存。
        """
        if force or self.changed:
            if file_name is None:
                file_name = self.file_name
            print(self.file_name, file_name)
            with open(file_name, "w") as fh:
                for (k, v) in self.file_dict.items():
                    fh.write("{} {}\n".format(v, k))

    def check_if_has_changed(self, name, value):
        """
        通过摘要判断文件是否有变更。如果有变更返回 True，否则返回 False。
        """
        if name in self.file_dict:
            return self.file_dict[name] != value
        else:
            return True

    def set_value(self, name, value):
        """
        设置文件名和摘要
        """
        self.file_dict[name] = value
        self.changed = True

    @staticmethod
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
