# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from . import api
from flask import g, request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome.utils.converter import login_code
from ihome.models import House, Order
from ihome import db, redis_cache
from datetime import datetime


@api.route("/orders", methods=["POST"])
@login_code
def orders():
    """
    用户下订单模块
    前端返回的参数 ： house_id,start_date,end_date
    前端返回的格式： json
    :return:
    """
    # 回去用户的ID
    user_id = g.user_id
    # 获取参数
    resp_json = request.get_json()
    if not resp_json:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    house_id = resp_json.get("house_id")        # 房屋ID
    start_date = resp_json.get("start_date")    # 入住的起始时间
    end_date = resp_json.get("end_date")        # 入住的结束时间

    # 参数校验
    # 校验时间
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert start_date <= end_date
        # 计算入住的天数
        days = (start_date - end_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="传入的参数有误")

    # 校验房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    else:
        if not house:
            return jsonify(errno=RET.PARAMERR, errmsg="参数异常")

    # 校验用户ID与房屋ID是否相同
    if user_id == house.user_id:
        return jsonify(errno=RET.PARAMERR, errmsg="用户不能为自己刷单哦!")

    # 确保房屋在这段时间内没有用户下单
    try:
        # 防止用户订单冲突, 返回是数字
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >=
                                   start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常，请稍后")
    else:
        if count > 0:
            return jsonify(errno=RET.DATAERR, errmsg="房屋已被预订")

    # 业务处理
    # 订单的总金额
    amount = days * house.price
    # 保存数据
    order = Order(
        user_id=user_id,
        house_id=house_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.collback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    return jsonify(errno=RET.OK, errmsg="成功", data={"order_id": order.id})


@api.route("/user/orders", methods=["GET"])
@login_code
def user_order():
    """
    显示订单信息模块
    前端发送的参数来确定是否为客户订单或用户订单
    :return:
    """
    user_id = g.user_id

    # 获取参数, 前端发送的参数来确定是否为客户订单或用户订单
    role = request.args.get("role", "")

    # 查询订单数据
    try:
        if role == "landlord":
            # 以房东的身份查询订单
            # 先查询属于自己的房子有哪些
            houses = House.query.filter(House.user_id == user_id).all()
            # 获取房屋的ID
            houses_ids = [house.id for house in houses]
            # 再查询预订了自己房子的订单
            order = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        else:
            # 以用户的身份查看订单
            order = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 将订单对象转换为字典数据
    orders_dict_list = []
    if order:
        for order_list in order:
            orders_dict_list.append(order_list.to_dict())

    return jsonify(errno=RET.OK, errmsg="成功", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_code
def accept_reject_order(order_id):
    """
    完成用户接单与拒单模块
    :param order_id:
    :return:
    """
    user_id = g.user_id

    # 获取参数
    resp_data = request.get_json()
    if resp_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数异常")

    # action参数表明客户端请求的是接单还是拒单的行为
    # accept:接单     reject:拒单
    action = resp_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="未能识别操作")
    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house_id
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 确保房东只能修改属于自己房子的订单
    if not house or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="非法请求错误")

    if action == "accept":
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 拒单先要获取拒单原因
        reason = resp_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒单原因")

        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, errmsg="保存失败")

    return jsonify(errno=RET.OK, errmsg="成功")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_code
def save_order_comment(order_id):
    """保存订单评论信息"""
    user_id = g.user_id
    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")  # 评价信息

    # 校验参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态才可以
        order = Order.query.filter(Order.user_id == user_id, Order.status == "WAIT_COMMENT", Order.id == order_id)\
            .first()

        # 获取房屋ID
        house = order.house_id
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    if not order:
        return jsonify(errno=RET.DBERR, errmsg="参数异常，无法评论")

    try:
        # 将订单的状态设置为已完成
        Order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

        # 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
    try:
        redis_cache.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")






