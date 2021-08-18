# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com

from flask import Blueprint

# 创建蓝图
api = Blueprint("api_0_1", __name__)


from . import mode, verification_code, passport, profille, city_code, house
