# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from . import api
from flask import jsonify, json
from ihome.utils.response_code import RET
from flask import current_app
from ihome.models import Area
from ihome import constant, redis_cache


@api.route("/areas")
def get_city_areas():
    """
    设置城市地区的视图
    :return: 查找数据库返回结果
    """
    # 尝试从redis中读取数据
    try:
        resp_json = redis_cache.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            current_app.logger.info("redis-server-is-ok")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库获得地区信息
    try:
        user_city = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="查询失败")

    # 将对象转换为列表的方式发送给前端
    areas_list = []
    for city in user_city:
        areas_list.append(city.to_dict())

    # 将数据转换为json
    rep_dict = dict(errno=RET.OK, errmsg="成功", data=areas_list)
    resp_json = json.dumps(rep_dict)

    # 将数据保存到redis中
    try:
        redis_cache.setex("area_info", constant.CITY_REDIS_TIME, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}

















