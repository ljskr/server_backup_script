# server_backup_script 概述

此脚本用于备份服务器数据至阿里云oss或FTP服务器。 更多备份途径待开发。

## 1. 运行方式

```bash
# 修改任务配置
vi config.py

# 执行备份任务
python3 backup.py
```

## 2. 主要框架说明

1) `TaskManager` 类。

负责执行所有备份任务。

2) `UploadManager` 类。

负责执行所有上传任务。

3) `EncipherManager` 类。

负责计算、读取和保存 md5 值。

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

把某个文件夹下的所有文件打包压缩，并加上时间戳和md5。生成的文件名格式为: `{task_name}_backup_{%y%m%d_%H%M%S}_{md5}.tgz`

| 参数 | 类型 | 说明 |
|-----------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| tar_run_dir | str | tar 命令运行路径 |
| backup_list | list | 需要备份的文件/文件夹列表，填写与 tar_run_dir 的相对路径。 |

#### 3.2.2 `SingleFileTask` - 单文件备份任务

把某个单文件进行备份，常见的为单个配置文件。此类任务可以做到有变更才进行备份。当设置了在文件变更时才备份，则会在每次执行时计算该文件的 md5 值，若 md5 值发生改变，则执行备份。 md5 值保存在 ENCIPHER_FILE 指定的文件中。 生成的文件名格式为: `{task_name}.{%y%m%d_%H%M%S}_{md5}`

| 参数 | 类型 | 说明 |
|-----------|------|------|
| task_name | str | 任务名称 |
| output_dir | str | 备份输出目录 |
| source_file | str | 需要备份的源文件路径 |
| backup_on_change | bool | 是否仅在文件变更时才备份（默认 False） |

#### 3.2.3 `MysqlTask` - MySQL 数据库备份任务

导出 MySQL 中的数据，打包压缩并加上时间戳和md5。生成的文件名格式为: `{task_name}_backup.sql.{%y%m%d_%H%M%S}_{md5}.tgz`

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

