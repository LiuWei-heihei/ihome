# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
# flake8: noqa
from qiniu import Auth, put_data
# import qiniu.config
# 需要填写你的 Access Key 和 Secret Key
access_key = '-thwZhisu_KiOgUs7j52YfwT2d5A5d0XaMVD-NTS'
secret_key = 'sIxms67r3NZRYr4zu9squL9yiZBwcbAI9xjNfSxY'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'liuwei-python-flask'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)
    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        return ret.get("key")
    else:
        raise Exception("七牛上传失败")


