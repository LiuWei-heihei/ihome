# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from . import api
from flask import request, g, jsonify, json, session
from ihome.utils.response_code import RET
from ihome.utils.converter import login_code
from flask import current_app
from ihome.models import  Area, House, Facility, HouseImage, User, Order
from ihome import constant, db, redis_cache
from ihome.utils.user_image_code import storage
from datetime import datetime


@api.route("/houses/info", methods=["POST"])
@login_code
def save_house_info():
    """保存房屋的基本信息
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    """
    # 获取数
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    # 判断数据的完整性
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 判断金额是否为int型
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="金额不能为字符串")
    # 判断地区的id
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if area is None:
            return jsonify(errno=RET.PARAMERR, errmsg="地区id错误")
    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 处理房屋的设施信息
    facility_ids = house_data.get("facility")
    # 如果用户勾选了设施信息，再保存数据库
    if facility_ids:
        try:
            print("*" * 15, facility_ids)
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            print("*"*15, facilities)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="数据库错误")

        if facilities:
            # 表示有合法的设施数据
            # 保存设施数据
            house.facilities = facilities

    # 保存数据成功
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库错误")

    # 返回数据
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"house_id": house.id})



@api.route("/houses/image", methods=["POST"])
@login_code
def save_house_image():
    """保存房屋的图片
    参数 图片 房屋的id
    """
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    # 校验参数
    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 判断house_id的正确性
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据库错误")
    else:
        if house is None:
            return jsonify(errnp=RET.PARAMERR, errmsg="参数错误")

    # 业务处理
    # 将图片转换为二进制
    image_data = image_file.read()
    # 调用七牛来上传照片
    try:
        image = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 将照片保存到HouseImage数据库中
    house_image = HouseImage(house_id=house_id, url=image)
    db.session.add(house_image)

    # 将照片保存到House数据库中
    if house.index_image_url is None:
        house.index_image_url = image
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库异常")

    image_url = constant.QINIU_IMAGE_IP + image
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_code
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    # 根据user_id来查询对应的房屋信息
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库错误")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="成功", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_cache.get("house_data")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if ret is not None:
            current_app.logger.info("redis is OK")
            return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    # 从数据库中尝试获取数据
    try:
        # 查询数据库，返回房屋订单数目最多的5条数据
        houses = House.query.order_by(House.order_count.desc()).limit(constant.INDEX_NUM)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库异常")
    else:
        if houses is None:
            return jsonify(errno=RET.DATAERR, errmsg="数据库没有数据")


    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    # 将数据保存到redis缓存中
    # 转换为json数据
    json_houses = json.dumps(houses_list)

    try:
        redis_cache.setex("house_data", constant.HOUSES_REDIS_TIME, json_houses)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数确实")

    # 先从redis缓存中获取信息
    try:
        ret = redis_cache.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_cache.setex("house_info_%s" % house_id, constant.HOUSES_REDIS_TIME, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}
    return resp


# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """获取房屋的列表信息（搜索页面）"""
    start_date = request.args.get("sd", "")  # 用户想要的起始时间
    end_date = request.args.get("en", "")   # 用户想要的结束时间
    area_id = request.args.get("aid", "")    # 区域编号
    sort_key = request.args.get("sk", "new")  # 排序关键字
    page = request.args.get("p")  # 页数

    # 校验参数
    # 校验时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="地区ID异常")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 获取redis数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_cache.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}

    # 过滤条件的参数列表容器
    filter_params = []
    # 填充过滤参数
    # 时间条件
    conflict_orders = None
    try:
        if start_date and end_date:
            # 查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders:
        # 从订单中获取冲突的房屋id
        conflict_house_ids = [Order.house_id for order in conflict_orders]

        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件
    if sort_key == "booking": # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:  # 新旧
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 分页处理
    try:
        page_obj = house_query.paginate(page=page, per_page=3, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # house_query返回的是字典形式的数据
    # 把字典遍历
    house_list = page_obj.itmets
    houses = []
    for house in house_list:
        houses.append(house.to_basic_dict())

    # page_obj中有个pages方法来获取总页数
    total_page = page_obj.pages
    # return jsonify(errno=RET.OK, errmsg="成功", data={"total_page": total_page, "houses": houses, "page": page})
    # 设置redis参数
    resp_dict = dict(errno=RET.OK, errmsg="成功", data={"total_page": total_page, "houses": houses, "page": page})
    # 把字典转化为json数据
    resp_json = json.dumps(resp_dict)
    if page <= total_page:
        # 设置数据库
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        # 设置哈希类型的数据
        try:
            # 创建redis管道对象，可以一次执行多个语句
            pipeline = redis_cache.pipeline()

            # 开启多个语句的记录
            pipeline.multi()

            # 设置redis
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, 3000)

            # 执行语句
            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}

















