# -*- coding: utf8 -*-

# Author: liujun
# Date: 2018-06-20
# Description:
#   备份脚本，用于备份dokuwiki文档、mysql数据库等。
#
# Modify log:
#   2018-06-20: 新建脚本文件。
#   2018-07-03: 增加上传至阿里云。

import datetime
import hashlib
import os
import sys

import oss2

# 获取当前脚本路径
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# 把当前路径加入python的path中
sys.path.append(os.path.normpath(SCRIPT_DIR))

import oss2_config as config

BASE_SAVE_DIR = "/home/ai/backups"

def upload(local_file, remote_file):
    """
    上传文件至OSS中

    入参：
        local_file: 本地文件路径
        remote_file: 运程文件名
    """
    auth = oss2.Auth(config.aliyum_access_id, config.aliyum_access_key)
    bucket = oss2.Bucket(auth, config.aliyum_endpoint, config.aliyum_bucket_name)
    
    bucket.put_object_from_file(remote_file, local_file)


def md5sum(fname):
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
    with open(fname, "rb") as fh:
        for chunk in read_chunks(fh):
            md5.update(chunk)
    return md5.hexdigest()

def backup_dokuwiki():
    """
    备份dokuwiki
    """
    dokuwiki_save_dir = os.path.join(BASE_SAVE_DIR, "dokuwiki")
    run_dir = "/var/www"

    dokuwiki_backup_list = [
        "dokuwiki/conf",
        "dokuwiki/data/attic",
        "dokuwiki/data/meta",
        "dokuwiki/data/pages",
        "dokuwiki/data/media",
        "dokuwiki/data/media_attic",
        "dokuwiki/data/media_meta"
    ]

    # 创建目录
    if not os.path.exists(dokuwiki_save_dir):
        os.mkdir(dokuwiki_save_dir)

    # 临时打包文件名
    temp_file = os.path.join(dokuwiki_save_dir, "dokuwiki_backup_temp.tgz")

    # 使用tar打包需要备份的文件
    os.system("cd {dir} && tar zcf {file} {cmd_args}"
            .format(dir=run_dir, 
                file=temp_file,
                cmd_args=" ".join(dokuwiki_backup_list)))

    # 计算压缩包的md5
    md5 = md5sum(temp_file)
    print("md5sum is {}".format(md5))
    
    # 重命名打包文件
    now = datetime.datetime.now()
    dokuwiki_backup_file_name = "dokuwiki_backup_{}_{}.tgz".format(now.strftime("%y%m%d_%H%M%S"), md5)
    full_path = os.path.join(dokuwiki_save_dir, dokuwiki_backup_file_name)
    os.rename(temp_file, full_path)

    if os.path.exists(full_path):
        print("备份成功，保存路径为: {}".format(full_path))

        print("准备上传至阿里云！")
        upload(full_path, "dokuwiki/{}".format(dokuwiki_backup_file_name))
        print("上传至阿里云完毕！")
    else:
        print("备份失败！")


def main():
    print(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S 开始备份 Dokuwiki."))
    backup_dokuwiki()
    print(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S 结束备份 Dokuwiki."))

if __name__ == '__main__':
    main()

