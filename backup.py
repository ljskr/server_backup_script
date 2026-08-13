"""备份主程序及命令行入口。"""

import argparse
import logging.config
import os
import sys

from dotenv import load_dotenv

from easybk import TaskManager, UploadManager
from easybk.run_lock import RunLock
from config_parser import init_from_yaml


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVOCATION_DIR = os.getcwd()


def _absolute_path(value):
    return os.path.abspath(os.path.expanduser(value))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="执行服务器备份及上传任务")
    parser.add_argument("--config", default=os.path.join(INVOCATION_DIR, "config.yaml"),
                        type=_absolute_path, help="YAML 配置文件路径")
    parser.add_argument("--env-file", default=os.path.join(INVOCATION_DIR, ".env"),
                        type=_absolute_path, help="环境变量文件路径")
    parser.add_argument("--state-file", default=os.path.join(INVOCATION_DIR, "md5_list.txt"),
                        type=_absolute_path, help="文件变化摘要状态路径")
    parser.add_argument("--lock-file", default=os.path.join(INVOCATION_DIR, ".backup.lock"),
                        type=_absolute_path, help="单实例运行锁路径")
    parser.add_argument("--log-config", default=os.path.join(BASE_DIR, "logger.conf"),
                        type=_absolute_path, help="logging 配置文件路径")
    parser.add_argument("--validate-config", action="store_true",
                        help="仅加载并校验配置，不执行备份")
    return parser.parse_args(argv)


def init_logger(config_path):
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        )



def main(argv=None):
    """
    主入口
    """
    args = parse_args(argv)
    os.chdir(BASE_DIR)
    init_logger(args.log_config)
    logger = logging.getLogger("backup")

    try:
        load_dotenv(args.env_file, override=False)
    except Exception as exc:
        logger.error("加载 .env 失败: %s", exc)
        return 2

    try:
        with RunLock(args.lock_file):
            return _run_backup(logger, args)
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 3


def _run_backup(logger, args):
    """在已持有运行锁的情况下执行一次备份。"""

    task_manager = TaskManager()
    upload_manager = UploadManager()
    task_manager.set_encipher_file(args.state_file)
    
    if not os.path.exists(args.config):
        logger.error("未找到配置文件: %s", args.config)
        return 2
    if not init_from_yaml(task_manager, upload_manager, args.config):
        return 2

    if args.validate_config:
        logger.info("配置校验通过: %s", args.config)
        return 0
    
    backup_ok = task_manager.run_all_task()
    upload_ok = upload_manager.run_all_upload()
    if not backup_ok or not upload_ok:
        logger.error("备份执行失败")
        return 1
    task_manager.save_state()
    return 0


if __name__ == "__main__":
    sys.exit(main())
