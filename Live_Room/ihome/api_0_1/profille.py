# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from . import api
from flask import request, g, jsonify
from ihome.utils.response_code import RET
from ihome.utils.converter import login_code
from ihome.utils.user_image_code import storage
from flask import current_app, session
from ihome.models import User
from ihome import constant, db
import re


@api.route("/users/avatar", methods=["POST"])
@login_code
def set_user_avatar():
    """
    上传照片视图
    接收参数: 图片 files
    :return:
    """
    # 接收参数
    user_avatar = request.files.get("avatar")
    user_id = g.user_id

    # 判断照片不能为空
    if user_avatar is None:
        return jsonify(errno=RET.DATAERR, errmsg="照片不能为空")

    # 键数据转换为二进制
    user_data = user_avatar.read()

    # 调用七牛上传照片
    try:
        user_key = storage(user_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传照片失败")

    # 将照片保存到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": user_key})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库保存失败")

    # 返回给前端图片的URL
    avatar_url = constant.QINIU_IMAGE_IP + user_key
    return jsonify(errno=RET.OK, errmsg="上传图片成功", data={"avatar_url": avatar_url})


@api.route("/users/name", methods=["PUT"])
@login_code
def change_user_name():
    """
    用户名称的修改
    前端返回的数据 user_id
    :return:
    """
    req_data = request.get_json()
    user_id = g.user_id
    if req_data is None:
        return jsonify(errno=RET.LOGINERR, errmsg="数据不完整")
    name = req_data.get("name")
    if name is None:
        return jsonify(errno=RET.LOGINERR, errmsg="数据不完整")
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库错误")

    # 设置session
    session["name"] = name
    return jsonify(errno=RET.OK, errmsg="设置成功", data={"name": name})


@api.route("/user", methods=["GET"])
@login_code
def get_user_profile():
    """获取个人信息"""
    user_id = g.user_id
    # 查询数据库获取个人信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_code
def user_login_data():
    """
    对用户继续判断是否填写过
    如果填写过显示填写的内容
    :return:
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.LOGINERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.LOGINERR, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


@api.route("/users/auth", methods=["POST"])
@login_code
def set_user_auth():
    """
    设置实名验证
    前端传入：
    :return:
    """
    # 获取数据
    user_id = g.user_id
    req_data = request.get_json()
    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 数据的完整性
    if not all([real_name, id_card]):
        return jsonify(errno=RET.LOGINERR, errmsg="数据不完整")

    # 判断数据的格式 身份证号必须要18位
    if not re.match(r"\d{18}", id_card):
        return jsonify(errno=RET.LOGINERR, errmsg="请填写正确的数据")

    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None) \
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据量错误")

    return jsonify(errno=RET.OK, errmsg="保存成功")


@api.route("/user/my")
@login_code
def my_user():
    """
    显示用户名和手机号
    :return: json数据
    """
    user_id = g.user_id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库错误")
    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg="没有数据查询")

    real_name = user.real_name
    id_card = user.id_card
    return jsonify(errno=RET.OK, errmsg="显示成功", data={"real_name": real_name, "id_card": id_card})




