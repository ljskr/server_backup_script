# server_backup_script 概述

此脚本用于备份服务器数据至阿里云oss或FTP服务器。 更多备份途径待开发。

## 1. 运行方式

```bash
# 从示例创建配置并按需修改
cp config.yaml.example config.yaml
cp .env.example .env
vi config.yaml
vi .env

# 安装并执行备份任务
python3 -m pip install -e .
easybk --config ./config.yaml

# 仅校验配置和环境变量，不执行备份
easybk --config ./config.yaml --validate-config
```

也可以使用 `python3 -m pip install -r requirements.txt` 安装运行依赖后直接执行
`python3 backup.py`。

项目只使用 YAML 配置。也可以不安装命令行入口，直接运行 `python3 backup.py`。配置无效
时程序退出码为 `2`；备份或上传失败时退出码为 `1`；检测到已有实例时退出码为 `3`。

命令行支持以下路径参数：

```text
--config CONFIG          YAML 配置文件
--env-file ENV_FILE      环境变量文件
--state-file STATE_FILE  文件变化摘要状态文件
--lock-file LOCK_FILE    单实例运行锁
--log-config LOG_CONFIG  logging 配置文件
--validate-config        仅校验配置
```

建议通过环境变量提供 OSS 和 FTP 凭据，避免把真实密码提交到仓库。配置文件支持
`${ENV:VARIABLE_NAME}` 格式的环境变量引用。

启动时会自动读取项目目录中的 `.env`，但不会覆盖操作系统中已经存在的同名环境变量。
`.env` 不应提交到版本库；可以从 `.env.example` 创建本地文件。

摘要只用于检测源文件变化和标识备份文件，不用于防篡改验证。当前使用 SHA-256；在现代
OpenSSL/CPU 上通常具有硬件加速，文件摘要过程的主要开销通常是读取磁盘。旧 MD5 状态
会在首次运行时自然迁移，可能触发一次重新备份。

程序通过 `.backup.lock` 防止多个实例并行执行；检测到已有实例时退出码为 `3`。生成的
tar 归档会在正式落盘前执行完整性检查。FTP 上传先写入临时远端名称、校验对象大小，
再切换为最终名称，避免把不完整上传暴露为正式备份。

## 2. 主要框架说明

1) `TaskManager` 类。

负责执行所有备份任务。

2) `UploadManager` 类。

负责执行所有上传任务。

3) `EncipherManager` 类。

负责计算、读取和保存文件变化检测摘要。

4) `Task` 类。

备份任务类，所有任务继承自此类。

5) `UploadTask` 类。

上传任务类，把 Task 和 Uploader 绑定，调用 uploader 对 task 的文件进行上传。

6) `Uploader` 类 。

远端上传类。目前支持阿里云 OSS 上传和 FTP 上传。

## 3. 备份任务介绍

本系统目前设置了三种类型的备份任务，所有任务都继承自 `Task` 基类。

### 3.1 任务基类 `Task` 属性说明

| 属性名 | 类型 | 说明 |
|--------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| result | bool | 任务执行结果 |
| output_file_name | str | 备份输出文件名 |
| output_full_path | str | 备份输出文件的完整路径 |

### 3.2 任务子类

#### 3.2.1 `PackTask` - 文件夹打包备份任务

把某个文件夹下的所有文件打包压缩，并加上时间戳和 SHA-256 摘要。生成的文件名格式为: `{task_name}_backup_{%y%m%d_%H%M%S}_{digest}.tgz`

| 参数 | 类型 | 说明 |
|-----------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| tar_run_dir | str | tar 命令运行路径 |
| backup_list | list | 需要备份的文件/文件夹列表，填写与 tar_run_dir 的相对路径。 |

#### 3.2.2 `SingleFileTask` - 单文件备份任务

把某个单文件进行备份，常见的为单个配置文件。此类任务可以做到有变更才进行备份。当设置了在文件变更时才备份，则会在每次执行时计算文件摘要，若摘要发生改变，则执行备份。摘要保存在状态文件中。生成的文件名格式为: `{task_name}.{%y%m%d_%H%M%S}_{digest}`

| 参数 | 类型 | 说明 |
|-----------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| source_file | str | 需要备份的源文件路径 |
| backup_on_change | bool | 是否仅在文件变更时才备份（默认 False） |

#### 3.2.3 `MysqlTask` - MySQL 数据库备份任务

导出 MySQL 中的数据，打包压缩并加上时间戳和 SHA-256 摘要。生成的文件名格式为: `{task_name}_backup.sql.{%y%m%d_%H%M%S}_{digest}.tgz`

| 参数 | 类型 | 说明 |
|-----------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| dump_option | str | mysqldump 命令参数 |

## 4. 上传任务介绍

本系统目前支持两种类型的上传器，所有上传器都继承自 `Uploader` 基类。上传任务通过 `UploadTask` 类将备份任务和上传器绑定。

### 4.1 上传任务类 `UploadTask` 属性说明

| 属性名 | 类型 | 说明 |
|--------|------|------|
| task | Task | 上传任务实例 |
| uploader | Uploader | 上传器实例 |
| remote_dir | str | 远端目录(文件名使用备份任务生成的文件名)。 |

### 4.2 上传器基类 `Uploader` 属性说明

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | str | 上传器实例名称 |


### 4.3 上传器子类

#### 4.3.1 `OSSUploader` - 阿里云 OSS 上传器

将备份文件上传到阿里云 OSS 存储。

| 参数 | 类型 | 说明 |
|-----------|------|------|
| name | str | 上传器实例名称 |
| access_id | str | OSS AccessKey ID |
| access_key | str | OSS AccessKey Secret |
| endpoint | str | OSS 服务端点 |
| bucket_name | str | OSS Bucket 名称 |
| use_temp_object | bool | 是否先上传临时对象并复制为最终对象，默认 `true` |

OSS 有两种上传策略：

- `use_temp_object: true`：先上传随机临时 key，校验大小，再调用 OSS 服务端复制生成最终
  key，最后删除临时对象。最终 key 不会暴露未完成内容，但会增加复制、删除请求，并在
  操作期间短暂占用双份存储。不同 OSS 运营商是否对复制流量、请求或临时存储收费，应以
  其计费规则为准。
- `use_temp_object: false`：直接上传最终 key，随后校验对象大小。只上传一次且不执行复制
  和删除，费用行为更简单；但覆盖同名对象时，无法提供临时 key 切换带来的隔离保障。


#### 4.3.2 `FTPUploader` - FTP 上传器

将备份文件上传到 FTP 服务器。

| 参数 | 类型 | 说明 |
|-----------|------|------|
| name | str | 上传器实例名称 |
| host | str | FTP 服务器主机地址 |
| port | int | FTP 服务器端口 |
| username | str | FTP 用户名 |
| password | str | FTP 密码 |
| secure | bool | 是否启用 FTP_TLS（默认 False） |
| passive | bool | 是否使用被动模式（默认 True） |

## 5. 恢复与验证

本地恢复前先验证归档，再解压：

```bash
tar -tzf /path/to/backup.tgz
mkdir -p /tmp/easybk-restore
tar -xzf /path/to/backup.tgz -C /tmp/easybk-restore
```

MySQL 备份解压后使用测试数据库先行恢复，不要直接覆盖生产库：

```bash
mysql --user=root --database=restore_test < /tmp/easybk-restore/backup.sql
```

建议定期从 OSS/FTP 下载备份到独立主机，核对文件大小、执行 `tar -tzf`，并完成一次测试
恢复。上传成功和归档可读并不能替代真实恢复演练。

## 6. 开发与持续集成

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
python3 -m compileall -q backup.py config_parser.py easybk tests
```

GitHub Actions 会在 Linux 的 Python 3.9、3.12 环境中执行测试和编译检查。

