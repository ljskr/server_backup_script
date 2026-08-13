import os


class RunLock:
    """使用原子创建的 PID 文件防止多个备份实例并行运行。"""

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self._acquired = False

    def acquire(self):
        return self._acquire(allow_stale_cleanup=True)

    def _acquire(self, allow_stale_cleanup):
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            try:
                with open(self.path, "r", encoding="ascii") as fh:
                    owner = fh.read().strip() or "未知"
            except OSError:
                owner = "未知"
            if allow_stale_cleanup and owner.isdigit() and not self._pid_exists(int(owner)):
                try:
                    os.remove(self.path)
                except FileNotFoundError:
                    pass
                return self._acquire(allow_stale_cleanup=False)
            raise RuntimeError("已有备份实例正在运行（PID: {}）".format(owner)) from exc
        with os.fdopen(fd, "w", encoding="ascii") as fh:
            fh.write(str(os.getpid()))
            fh.flush()
            os.fsync(fh.fileno())
        self._acquired = True
        return self

    @staticmethod
    def _pid_exists(pid):
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return True
        return True

    def release(self):
        if self._acquired:
            try:
                os.remove(self.path)
            except FileNotFoundError:
                pass
            self._acquired = False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
