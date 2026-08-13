"""
Author: liujun (ljskryj@163.com)
Date: 2018-07-11
"""


import hashlib
import logging
import os
import tempfile

from .singleton import Singleton


class EncipherManager(Singleton):
    """
    文件摘要管理器。 单例。
    """

    def __init__(self):
        self.logger = logging.getLogger("EncipherManager")
        self.file_dict = {}
        self.changed = False
        self.file_name = None

    def load_data_from_file(self, file_name):
        """
        从文件加载摘要列表
        """
        self.file_dict = {}
        self.changed = False
        self.file_name = file_name

        if not os.path.exists(file_name):
            self.logger.info("摘要状态文件不存在，将创建新文件: %s", file_name)
            return

        with open(file_name, "r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                cols = line.split(" ", 1)
                if len(cols) != 2 or not cols[0] or not cols[1]:
                    raise ValueError("摘要状态文件第 {} 行格式错误".format(line_number))
                self.file_dict[cols[1]] = cols[0]
        self.logger.info("已加载 %s 条数据", len(self.file_dict))

    def save_data_to_file(self, file_name=None, force=False):
        """
        保存摘要列表到文件中。

        inputs:
            file_name: 保存的文件名。若为 None ，则保存到读取的源文件中。
            force: 是否强制写入。若数据无变更，默认不会重新保存。设置此字段可强制重新保存。
        """
        if force or self.changed:
            if file_name is None:
                file_name = self.file_name
            if not file_name:
                raise ValueError("未指定摘要状态文件")
            target = os.path.abspath(file_name)
            target_dir = os.path.dirname(target)
            os.makedirs(target_dir, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix=".digest-", dir=target_dir, text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    for key, value in sorted(self.file_dict.items()):
                        fh.write("{} {}\n".format(value, key))
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(temp_path, target)
                self.changed = False
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    def check_if_has_changed(self, name, value) -> bool:
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
    def digest(file_name) -> str:
        """
        使用 SHA-256 计算文件摘要，仅用于变化检测和备份标识。

        参数： 文件名
        返回值：SHA-256 十六进制摘要
        """
        def read_chunks(fh):
            while True:
                chunk = fh.read(1024 * 1024)
                if chunk:
                    yield chunk
                else:
                    break

        digest = hashlib.sha256()
        with open(file_name, "rb") as fh:
            for chunk in read_chunks(fh):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def md5sum(file_name) -> str:
        """兼容旧调用；新实现返回 SHA-256 摘要。"""
        return EncipherManager.digest(file_name)
