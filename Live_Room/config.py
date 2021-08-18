# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
import redis


class Config(object):
    """配置对象"""
    SECRET_KEY = "Configure secret key"

    # 配置MySQL数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/ihome_flask'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = True

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session
    SESSION_TYPE = "redis"
    # 建立session与redis的链接
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 秘钥
    SESSION_USE_SIGNER = True
    # session的有效期
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    """开发模式的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下得配置"""
    pass


temp_data = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
