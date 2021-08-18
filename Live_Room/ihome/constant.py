# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com


# 设置图片验证码的有效时间 单位为：秒
IMAGE_REDIS_EXPIRE = 180
# 设置短信验证码的有效时间 单位为：秒
SMS_REDIS_EXPIRE = 300
# 设置短信验证码的频繁时间为60 单位为：秒
SEND_REDIS_EXPIRE = 60
# 设置手机号校验的频繁时间为5 单位为：次
LOGIN_REDIS_EXPIRE = 5
# 设置手机号校验的频繁时间为有效期 单位为：秒
SMS_IP_REDIS_EXPIRE = 600
# 设置七牛的IP地址
QINIU_IMAGE_IP = "http://qv092mxy0.hd-bkt.clouddn.com/"
# 设置地区保存的时间 单位：秒
CITY_REDIS_TIME = 4320
# 设置主页显示的页数
INDEX_NUM = 5
# 设置房屋信息的缓存时间 单位：秒
HOUSES_REDIS_TIME = 86400
