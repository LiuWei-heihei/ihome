# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from . import api
from ihome import models


@api.route("/index")
def index():
    return "python"
