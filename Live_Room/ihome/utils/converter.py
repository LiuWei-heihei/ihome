# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com

from werkzeug.routing import BaseConverter
from flask import session, g, jsonify
from ihome.utils.response_code import RET
import functools


class Converter(BaseConverter):
    """自定义转换器"""
    def __init__(self, url_map, temp):
        super(Converter, self).__init__(url_map)
        self.temp = temp


def login_code(view_func):

    @functools.wraps(view_func)
    def user_code(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登入")

    return user_code
