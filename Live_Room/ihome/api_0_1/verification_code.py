# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_cache
from ihome.constant import IMAGE_REDIS_EXPIRE, SMS_REDIS_EXPIRE, SEND_REDIS_EXPIRE
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
import random
from ihome.libs.yuntongxun.SendTemplateSMS import CCP


# 对图片验证进行处理
# 127.0.0.1:5000/api/v1.0/image_code/<image_code_id>
# <image_code_id>为前端传入的编号
@api.route("/image_codes/<image_code_id>")
def image_code(image_code_id):
    """
    对图片进行验证
    :param image_code_id: 编号
    :return: 图片
    """
    # 业务处理
    # 1:生成图片 name为姓名，text为真实文本，image_data为图片数据
    name, text, image_data = captcha.generate_captcha()
    # 2: 将编号和真实文本保存到redis中
    # 通过经验以string类型保存到redis中
    try:
        redis_cache.set("image_code_%s" % image_code_id, text)
        # 设置redis的有效时间 单位为：秒
        redis_cache.expire("image_code_%s" % image_code_id, IMAGE_REDIS_EXPIRE)
    except Exception as s:
        # 把异常记录到log日志上
        current_app.logger.error(s)
        # 在返回json数据errno为状态码，errmsg为内容
        return jsonify(errno=RET.DBERR, errmsg="SERVER IMAGE REDIS AS ERROR")

    # 返回图片
    # 设置响应头
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# 发送短信
# url:127.0.0.1:5000/api/v1.0/sms_codes?image_code&image_code_id
# GET方式请求 <re(r'.*'):page>
# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def sms_code(mobile):
    """
    短信验证
    :param mobile: 接收手机号
    :return:
    """
    # 提取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")
    # 校验
    # 判断完整性
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 业务处理
    # 从redis中获取真实的图片验证码
    try:
        image_id = redis_cache.get("image_code_%s" % image_code_id)
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库错误")
    # 判断图片验证码是否过期 过期返回值为：None
    if image_id is None:
        # 图片验证码过期
        return jsonify(errno=RET.NODATA, errmsg="没有图片验证码")

    # 删除图片验证码
    try:
        redis_cache.delete("image_code_%s" % image_code_id)
    except Exception as s:
        current_app.logger.error(s)

    # 与用户填写的值进行对比
    # 由于数据库发送的是bytes类型 所有要转换类型为str
    if bytes.decode(image_id.lower()) != str(image_code.lower()):
        # 用户输入的图片验证码错误
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

    # 对短信发送频繁进行处理
    try:
        send_code = redis_cache.get("send_code_%s" % mobile)
    except Exception as s:
        current_app.logger.error(s)
    else:
        if send_code is not None:
            # 判断用户是否在60秒之后再发送短信
            return jsonify(errno=RET.REQERR, errmsg="短信发送频率繁忙")
    # 判断手机号是否存在
    # 进行数据库的查询
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as s:
        current_app.logger.error(s)
    else:
        if user is not None:
            # 手机号已存在
            return jsonify(errno=RET.DATAERR, errmsg="手机号已存在")
    # 如果不存在，则生成验证码
    # 生成6位数字的验证码
    sms_code_id = "%06d" % random.randint(0,999999)
    # 保存真实的验证码
    try:
        redis_cache.set("sms_code_%s" % mobile, sms_code_id)
        redis_cache.expire("image_code_%s" % mobile, SMS_REDIS_EXPIRE)
        # 对短信发送频繁进行处理
        redis_cache.setex("send_code_%s" % mobile, SEND_REDIS_EXPIRE, 1)
    except Exception as s:
        current_app.logger.error(s)
        return jsonify(errno=RET.DBERR, errmsg="数据错误")
    # 发送短信
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code_id, SMS_REDIS_EXPIRE/60], 1)
    except Exception as s:
        current_app.logger.error(s)
    # 返回
    else:
        if result == 0:
            # 发送成功
            return jsonify(errno=RET.OK, errmsg="发送成功")
        else:
            return jsonify(errno=RET.THIRDERR, errmsg="发送失败")






















