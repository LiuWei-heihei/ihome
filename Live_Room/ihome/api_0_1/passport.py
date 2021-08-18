# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com

from . import api
from flask import current_app, request, jsonify, session
from ihome.utils.response_code import RET
from ihome import redis_cache, db, constant
from ihome.models import User
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import re


# 对用户注册进行处理
@api.route("/users", methods=["POST"])
def register():
    """
    对用户进行注册
    提取参数：mobile，sms_code, password, password2
    参数格式: json
    :return:
    """
    # 提取参数
    rep_data = request.get_json()
    mobile = rep_data.get("mobile")
    sms_code = rep_data.get("sms_code")
    password = rep_data.get("password")
    password2 = rep_data.get("password2")

    # 校验参数
    # 校验数据的完整性
    if not all([mobile, sms_code, password2, password]):
        return jsonify(errno=RET.DATAERR, errmsg="数据不完整")

    # 校验手机号的格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号不正确")

    # 判断密码和确认密码
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="确认密码有误")

    # 业务处理
    # 获取redis中的短信验证码
    try:
        real_sms_code = redis_cache.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库错误")
    # 判断验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.PARAMERR, errmsg="验证码已过期")
    # 删除验证码
    try:
        redis_cache.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    # 判断短信验证码和输入的一致性
    if bytes.decode(real_sms_code) != sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg="验证码错误")
    # 判断手机号是否注册过，如果没有把数据保存到MySQL数据库中
    user = User(name=mobile, mobile=mobile)
    # 调用了property装饰器来对密码进行了加密 加密方法为sha256
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 回滚数据
        db.session.rollback()
        # 记录数据库错误
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据库错误")
    except Exception as e:
        db.session.rollback()
        current_app.logger(e)
        return jsonify(errno=RET.PARAMERR, errmsg="手机号已存在")

    # 保存登入状态session
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回
    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登入视图
# url：/api/v1.0/user
# 传入参数mobile和password password要解析
@api.route("/sessions", methods=["POST"])
def login():
    """
    登入视图
    :return: 返回json数据
    """
    # 提取参数
    rep_data = request.get_json()
    mobile = rep_data.get("mobile")
    password = rep_data.get("password")
    # 校验参数
    # 判断数据的完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="用户名或密码不能为空")

    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不对")
    # 对用户访问的次数进行判断
    # 次数保存到redis中
    # 格式为 access_nums_%请求的ip：次数 5
    ip = request.remote_addr # 获取请求的IP
    try:
        access_nuns = redis_cache.get("access_nums_%s" % ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nuns is not None and int(access_nuns) >= constant.LOGIN_REDIS_EXPIRE:
            return jsonify(errno=RET.REQERR, errmsg="请求次数过多")

    # 业务处理
    # 获取MySQL数据库的参数
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
    # 判断数据是否存在
    if user is None or not user.check_password(password):
        # 验证失败保存验证次数到redis中
        try:
            redis_cache.incr("access_nums_%s" % ip)
            redis_cache.expire("access_nums_%s" % ip, constant.SMS_IP_REDIS_EXPIRE)
        except Exception as e:
            current_app.logger(e)
        return jsonify(errno=RET.PARAMERR, errmsg="用户名或密码错误")
    # 设置session
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id
    # 返回
    return jsonify(errno=RET.OK, errmsg="登入成功")
      

# url: /api/v1.0/session
# @api.route("/sessions", methods="POST")
@api.route("/session", methods=["GET"])
def user_login():
    """
    # 显示页面的设置
    :return: 接收前端的session信息来显示不同的页面
    """
    # 获取参数
    name = session.get("name")
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="True", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登入")


# url: /api/v1.0/session
@api.route("/session", methods=["DELETE"])
def det_login():
    """
    退出登入
    :return: 清除session数据
    """
    session.clear()
    return jsonify(errno=RET.OK, errmsg="退出成功")








