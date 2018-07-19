# server_backup_script 概述

此脚本用于备份服务器数据至阿里云oss。 更多备份途径待开发。

## 1. 配置文件 

### config_for_ai/config.py

主要是修改 aliyun id

配置文件中的 ENCIPHER_FILE 指定一个保存文件 md5 值的 txt 文件，默认是 config_for_ai/md5_list.txt 。 请不要手动修改该文件。

### config_for_ai/task_config.py

配置任务。

本系统目前设置了三种类型的任务：

1) 文件夹打包备份任务。

把某个文件夹下的所有文件打包，并加上时间戳和md5。

2) 单文件备份任务。

把某个单文件进行备份，常见的为单个配置文件。此类任务可以做到有变更才进行备份。做法为每次执行时计算一个该文件的 md5 值，若 md5 值发生改变，则说明文件有变更。 md5 值保存在 ENCIPHER_FILE 指定的文件中。

3) mysql 备份任务。

导出 mysql 中的数据，并加上时间戳和md5。

每种任务都附了一个简单的示例。

## 2. 运行方式

```bash
python3 backup.py
```

## 3. 主要框架说明

1) Task 类。

所有任务继承自此类。

2) EncipherManager 类。

负责计算、读取和保存 md5 值。

3) oss_uploader 。

上传文件至阿里云 oss 。后续考虑提取一个 Uploader 父类，并增加更多备份途径。

4) TaskManager 类。

负责执行所有备份任务，并上传。
