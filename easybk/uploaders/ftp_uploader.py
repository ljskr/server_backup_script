"""
Author: liujun (ljskryj@163.com)
Date: 2025-10-30
"""


import logging
import os
import posixpath
from ftplib import FTP, FTP_TLS, error_perm

from .uploader import Uploader, Task


class FTPClient():
    """
    轻量 FTP 客户端封装，支持TLS及被动模式
    """

    def __init__(self, host: str, port: int, username: str, password: str, logger: logging.Logger, secure: bool = False, passive: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.logger = logger
        self.secure = secure
        self.passive = passive
        self._ftp = None
        self._connected = False

    def _connect(self):
        if self._ftp is not None and self._connected:
            return
        self.logger.info("FTPUploader: 正在连接 %sFTP %s:%s", ("安全" if self.secure else ""), self.host, self.port)
        if self.secure:
            ftp = FTP_TLS()
        else:
            ftp = FTP()
        ftp.connect(self.host, self.port, timeout=60)
        ftp.login(self.username, self.password)
        # TLS模式：保护数据。要在登录和cwd后调用prot_p
        if self.secure:
            try:
                ftp.prot_p()
                self.logger.info("FTPUploader: 启用TLS保护传输 (PROT P)")
            except Exception as e:
                self.logger.warning("FTPUploader: TLS保护传输失败，将以普通FTP模式继续：%s", str(e))
        # 设置被动模式
        try:
            ftp.set_pasv(self.passive)
            self.logger.info("FTPUploader: 被动模式 %s", self.passive)
        except Exception:
            self.logger.warning("FTPUploader: 设置被动模式失败。")
        self._ftp = ftp
        self._connected = True
        self.logger.info("FTPUploader: FTP 连接完成")

    def _ensure_dir(self, remote_dir: str):
        """
        确保远程目录存在（逐级创建）。
        """
        if not remote_dir or remote_dir in ("/", "."):
            return
        # 使用 POSIX 分隔符，避免 Windows 反斜杠
        parts = [p for p in remote_dir.split('/') if p and p != '.']
        if not parts:
            return
        cwd_backup = self._ftp.pwd()
        try:
            # 从根或当前目录开始逐级进入/创建
            for part in parts:
                try:
                    self._ftp.cwd(part)
                except error_perm:
                    self._ftp.mkd(part)
                    self._ftp.cwd(part)
        finally:
            # 回到原目录
            self._ftp.cwd(cwd_backup)

    def put_file(self, remote_path: str, local_path: str, retry: int = 3):
        """
        将本地文件上传到远程路径（包含文件名），失败重试3次。
        """
        for t in range(retry):
            try:
                self._connect()
                if not os.path.isfile(local_path):
                    raise FileNotFoundError(local_path)

                # 归一化远程路径为 POSIX 路径
                remote_path = remote_path.replace('\\', '/')
                remote_dir = posixpath.dirname(remote_path)
                remote_name = posixpath.basename(remote_path)

                if remote_dir and remote_dir not in ("/", "."):
                    # 切换到根目录，逐级创建
                    try:
                        self._ftp.cwd('/')
                    except Exception:
                        # 某些服务器不支持，忽略
                        pass
                    self._ensure_dir(remote_dir)

                # 进入目标目录（如果有）
                if remote_dir and remote_dir not in ("/", "."):
                    for part in [p for p in remote_dir.split('/') if p and p != '.']:
                        self._ftp.cwd(part)

                with open(local_path, 'rb') as f:
                    self._ftp.storbinary(f'STOR {remote_name}', f)

                self.logger.info("FTPUploader: 文件 %s 上传完成", local_path)
                # 上传后回到根
                self._ftp.cwd("/")
                return  # 成功
            except Exception as e:
                if t < retry - 1:
                    self.logger.warning("FTPUploader: 上传失败，第%d次重试: %s", t+1, str(e))
                    # 断线重连
                    self._ftp = None
                    self._connected = False
                else:
                    self.logger.error("FTPUploader: 上传失败已重试%d次，放弃：%s", retry, str(e))
                    raise


class FTPUploader(Uploader):
    """
    FTP 上传器

    参数：
        name: 本实例名称
        host: FTP 主机
        port: FTP 端口
        username: FTP 用户名
        password: FTP 密码
        secure: 是否启用FTP_TLS
        passive: 是否使用被动模式
    """

    def __init__(self, name: str, host: str, port: int, username: str, password: str, secure: bool = False, passive: bool = True):
        Uploader.__init__(self, name)
        self.logger = logging.getLogger("FTPUploader")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.secure = secure
        self.passive = passive
        self.ftp_client = FTPClient(host, port, username, password, self.logger, secure=secure, passive=passive)

    def do_upload(self, task: Task, remote_dir: str) -> bool:
        """
        执行上传任务
        参数:
            task: 备份任务
            remote_dir: 远程目录
        """
        remote_full_path = os.path.join(remote_dir, task.get_output_file_name())
        local_full_path = task.get_output_full_path()
        self.logger.info("FTPUploader: 上传文件: [%s] -> [%s]", local_full_path, remote_full_path)
        self.ftp_client.put_file(
            remote_full_path, local_full_path, retry=3)
        self.logger.info("FTPUploader: 上传文件完成: [%s] -> [%s]", local_full_path, remote_full_path)
        return True
