"""
YAML 配置文件解析器
支持从 config.yaml 读取配置并初始化 TaskManager 和 UploadManager
"""

import os
import datetime
import logging
import re

try:
    import yaml
except ImportError:
    yaml = None

from easybk import TaskManager, UploadManager, UploadTask
from easybk import PackTask, MysqlTask, SingleFileTask
from easybk import OSSUploader, FTPUploader


def _replace_placeholders(text: str, variables: dict) -> str:
    """
    替换字符串中的占位符
    
    支持以下格式：
    - ${VAR_NAME}: 从 variables 字典中获取变量
    - ${ENV:VAR_NAME}: 从系统环境变量中获取
    - ${ENV:VAR_NAME:default_value}: 从系统环境变量中获取，如果不存在则使用默认值
    
    参数:
        text: 包含占位符的字符串
        variables: 变量字典，键为变量名（不含 ${}），值为替换值
    
    返回:
        替换后的字符串
    """
    if not isinstance(text, str):
        return text
    
    # 匹配 ${VAR} 或 ${ENV:VAR:default} 格式的占位符
    pattern = r'\$\{([^}]+)\}'
    
    def replace_match(match):
        var_expr = match.group(1)
        
        # 处理环境变量：${ENV:VAR_NAME} 或 ${ENV:VAR_NAME:default_value}
        if var_expr.startswith("ENV:"):
            env_parts = var_expr[4:].split(":", 1)
            env_var_name = env_parts[0]
            default_value = env_parts[1] if len(env_parts) > 1 else None
            
            env_value = os.getenv(env_var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # 环境变量不存在且没有默认值，保持原样
                return match.group(0)
        
        # 处理普通变量：${VAR_NAME}
        if var_expr in variables:
            return str(variables[var_expr])
        
        # 如果变量不存在，保持原样
        return match.group(0)
    
    # 递归替换，直到没有更多占位符
    max_iterations = 10  # 防止无限循环
    iteration = 0
    result = text
    while iteration < max_iterations:
        new_result = re.sub(pattern, replace_match, result)
        if new_result == result:
            # 没有更多替换，退出
            break
        result = new_result
        iteration += 1
    
    return result


def _process_property_value(value, variables: dict):
    """
    处理单个 property 的值
    
    如果值是字符串，则替换其中的占位符
    其他类型直接返回
    
    参数:
        value: property 的值
        variables: 已解析的变量字典
    
    返回:
        处理后的值
    """
    if isinstance(value, str):
        # 字符串，替换占位符
        return _replace_placeholders(value, variables)
    else:
        # 其他类型，直接返回
        return value


def init_from_yaml(task_manager: TaskManager, upload_manager: UploadManager, config_path: str = "config.yaml"):
    """
    从 YAML 配置文件初始化任务和上传管理器
    
    参数:
        task_manager: 任务管理器
        upload_manager: 上传管理器
        config_path: YAML 配置文件路径，默认为 config.yaml
    """
    logger = logging.getLogger("config_parser")
    
    # 检查 yaml 模块是否可用
    if yaml is None:
        logger.error("PyYAML 模块未安装，无法加载 YAML 配置文件。请运行: pip install PyYAML")
        return
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        logger.warning("YAML 配置文件不存在: %s，跳过 YAML 配置加载", config_path)
        return
    
    try:
        # 读取 YAML 文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error("YAML 配置文件解析失败: %s，错误: %s", config_path, str(e))
        return
    except Exception as e:
        logger.error("读取 YAML 配置文件失败: %s，错误: %s", config_path, str(e))
        return
    
    if not config:
        logger.warning("YAML 配置文件为空: %s", config_path)
        return
    
    # 获取当前时间
    now = datetime.datetime.now()
    
    # 初始化变量字典，添加系统内置时间变量
    variables = {
        "CURRENT_DATETIME": now.strftime("%Y%m%d_%H%M%S"),  # 完整的日期+时间
        "CURRENT_DATE": now.strftime("%Y%m%d"),             # 只有日期
        "CURRENT_TIME": now.strftime("%H%M%S")              # 只有时间
    }
    
    # 解析 properties 节点
    properties = config.get("properties", {})
    
    # 统一处理所有 properties 中的变量
    # 需要多次遍历以支持变量之间的依赖关系
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        changed = False
        for key, value in properties.items():
            if key not in variables:
                # 处理该 property 的值
                processed_value = _process_property_value(value, variables)
                variables[key] = processed_value
                changed = True
            elif key in variables:
                # 如果值已存在，但可能依赖了新的变量，需要重新处理
                old_value = variables[key]
                processed_value = _process_property_value(value, variables)
                if processed_value != old_value:
                    variables[key] = processed_value
                    changed = True
        
        if not changed:
            break
        
        iteration += 1

    # 创建任务字典，用于后续上传任务关联
    task_dict = {}
    
    # 解析任务
    tasks_config = config.get("tasks", [])
    for task_config in tasks_config:
        try:
            task = _create_task_from_config(task_config, variables)
            if task:
                task_manager.add_task(task)
                task_dict[task.task_name] = task
                logger.info("添加任务: %s (类型: %s)", task.task_name, task_config.get("type", "unknown"))
        except Exception as e:
            logger.error("创建任务失败: %s，错误: %s", task_config.get("task_name", "unknown"), str(e))
            continue
    
    # 解析上传器
    uploaders_config = config.get("uploaders", [])
    uploader_dict = {}
    for uploader_config in uploaders_config:
        try:
            uploader = _create_uploader_from_config(uploader_config)
            if uploader:
                uploader_dict[uploader.name] = uploader
                logger.info("添加上传器: %s (类型: %s)", uploader.name, uploader_config.get("type", "unknown"))
        except Exception as e:
            logger.error("创建上传器失败: %s，错误: %s", uploader_config.get("name", "unknown"), str(e))
            continue
    
    # 解析上传任务
    upload_tasks_config = config.get("upload_tasks", [])
    for upload_task_config in upload_tasks_config:
        try:
            task_name = upload_task_config.get("task_name")
            uploader_name = upload_task_config.get("uploader_name")
            remote_dir = upload_task_config.get("remote_dir", "")
            
            # 替换 remote_dir 中的占位符
            remote_dir = _replace_placeholders(remote_dir, variables)
            
            # 查找对应的任务和上传器
            task = task_dict.get(task_name)
            uploader = uploader_dict.get(uploader_name)
            
            if not task:
                logger.warning("上传任务关联的任务不存在: %s，跳过", task_name)
                continue
            
            if not uploader:
                logger.warning("上传任务关联的上传器不存在: %s，跳过", uploader_name)
                continue
            
            upload_task = UploadTask(task=task, uploader=uploader, remote_dir=remote_dir)
            upload_manager.add_upload_task(upload_task)
            logger.info("添加上传任务: 任务=%s, 上传器=%s, 远程目录=%s", 
                       task_name, uploader_name, remote_dir)
        except Exception as e:
            logger.error("添加上传任务失败: %s，错误: %s", upload_task_config, str(e))
            continue
    
    logger.info("YAML 配置加载完成")


def _create_task_from_config(task_config: dict, variables: dict):
    """
    从配置字典创建任务对象
    
    参数:
        task_config: 任务配置字典
        variables: 变量字典，包含所有可用的变量
    """
    task_type = task_config.get("type")
    task_name = task_config.get("task_name")
    output_dir = task_config.get("output_dir", "")
    
    # 替换 output_dir 中的占位符
    output_dir = _replace_placeholders(output_dir, variables)
    
    if not task_name:
        raise ValueError("任务配置缺少 task_name")
    
    if not output_dir:
        raise ValueError("任务配置缺少 output_dir")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    if task_type == "pack":
        # PackTask
        tar_run_dir = task_config.get("tar_run_dir")
        backup_list = task_config.get("backup_list", [])
        
        if not tar_run_dir:
            raise ValueError("PackTask 配置缺少 tar_run_dir")
        if not backup_list:
            raise ValueError("PackTask 配置缺少 backup_list")
        
        return PackTask(
            task_name=task_name,
            output_dir=output_dir,
            tar_run_dir=tar_run_dir,
            backup_list=backup_list
        )
    
    elif task_type == "mysql":
        # MysqlTask
        dump_option = task_config.get("dump_option")
        
        if not dump_option:
            raise ValueError("MysqlTask 配置缺少 dump_option")
        
        return MysqlTask(
            task_name=task_name,
            output_dir=output_dir,
            dump_option=dump_option
        )
    
    elif task_type == "single_file":
        # SingleFileTask
        source_file = task_config.get("source_file")
        backup_on_change = task_config.get("backup_on_change", False)
        
        if not source_file:
            raise ValueError("SingleFileTask 配置缺少 source_file")
        
        return SingleFileTask(
            task_name=task_name,
            output_dir=output_dir,
            source_file=source_file,
            backup_on_change=backup_on_change
        )
    
    else:
        raise ValueError(f"不支持的任务类型: {task_type}")


def _create_uploader_from_config(uploader_config: dict):
    """
    从配置字典创建上传器对象
    
    参数:
        uploader_config: 上传器配置字典
    """
    uploader_type = uploader_config.get("type")
    name = uploader_config.get("name")
    
    if not name:
        raise ValueError("上传器配置缺少 name")
    
    if uploader_type == "oss":
        # OSSUploader
        access_id = uploader_config.get("access_id")
        access_key = uploader_config.get("access_key")
        endpoint = uploader_config.get("endpoint")
        bucket_name = uploader_config.get("bucket_name")
        
        if not all([access_id, access_key, endpoint, bucket_name]):
            raise ValueError("OSSUploader 配置缺少必需参数")
        
        return OSSUploader(
            name=name,
            access_id=access_id,
            access_key=access_key,
            endpoint=endpoint,
            bucket_name=bucket_name
        )
    
    elif uploader_type == "ftp":
        # FTPUploader
        host = uploader_config.get("host")
        port = uploader_config.get("port", 21)
        username = uploader_config.get("username")
        password = uploader_config.get("password")
        secure = uploader_config.get("secure", False)
        passive = uploader_config.get("passive", True)
        
        if not all([host, username, password]):
            raise ValueError("FTPUploader 配置缺少必需参数")
        
        return FTPUploader(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            secure=secure,
            passive=passive
        )
    
    else:
        raise ValueError(f"不支持的上传器类型: {uploader_type}")

