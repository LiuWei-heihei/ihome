# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from flask import Flask
from config import temp_data
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from logging.handlers import RotatingFileHandler
import redis
import logging
from ihome.utils.converter import Converter

# 建立数据库的链接 还没有与flask链接
db = SQLAlchemy()

# 建立redis对象
redis_cache = None

# 配置日志信息
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级


# flask官方推荐的工厂模式
def creat_config(test_name):
    """
    配置app的对象
    :param test_name: str 用来接收配置信息 (development, production)
    :return: 返回的对象
    """

    app = Flask(__name__)
    # 根据传入的值来判断为什么模式(development, production)
    test_config = temp_data.get(test_name)
    app.config.from_object(test_config)

    # 通过db.init_app来链接flask
    db.init_app(app)

    # 建立redis的缓存
    global redis_cache
    redis_cache = redis.StrictRedis(host=test_config.REDIS_HOST, port=test_config.REDIS_PORT)

    # 配置session
    Session(app)

    # flask的scrf防护
    CSRFProtect(app)

    # 自定义转换器
    app.url_map.converters["re"] = Converter

    # 注册蓝图
    from ihome import api_0_1
    app.register_blueprint(api_0_1.api, url_prefix="/api/v1.0")
    # 注册静态页面蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    return app
