import random
import re
from datetime import datetime

from flask import request, abort, make_response, current_app, jsonify, session

from info import sr, db
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha
from info.utils.response_code import RET, error_map


@passport_blu.route('/get_img_code')  # 蓝图管理
def get_img_code():
    """获取图片验证码"""
    # 获取参数
    img_code_id = request.args.get('img_code_id')
    # 校验参数
    if not img_code_id:
        return abort(403)

    # 生成图片验证码
    img_code_name, img_code_text, img_code = captcha.generate_captcha()
    # 将图片key和验证码文字存入redis
    try:
        sr.set("img_code_id_" + img_code_id, img_code_text, ex=180)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)
    # 返回验证码图片
    response = make_response(img_code)
    response.content_type = 'image/jpeg'
    return response


@passport_blu.route('/get_sms_code', methods=['POST'])
def get_sms_code():
    """获取短信验证码"""
    # 获取参数
    img_code_id = request.json.get('img_code_id')
    mobile = request.json.get('mobile')
    img_code = request.json.get('img_code')
    # 校验参数
    if not all([img_code_id, mobile, img_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验手机号格式
    if not re.match('^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据img_code_id取出redis里的img_code_text
    try:
        real_img_code = sr.get("img_code_id_"+img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 判断验证码是否过期
    if not real_img_code:
        return jsonify(errno=RET.PARAMERR, errmsg="验证码过期")
    # 判断验证码是否一致
    if img_code.upper() != real_img_code:
        return jsonify(errno=RET.PARAMERR, errmsg="验证码错误")
    # 检验 手机号是否已存在
    user = User.query.filter_by(mobile=mobile).first()
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg=error_map[RET.DATAEXIST])
    # 根据结果发送短信
    sms_code = "%04d" % random.randint(0, 9999)
    current_app.logger.info('短信验证码为:%s' % sms_code)
    # 注意： 测试的短信模板编号为1
    # CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # 将短信验证码存入redis
    try:
        sr.set('sms_code_id_' + mobile, sms_code, ex=60)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回结果给前端
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@passport_blu.route('/register', methods=['POST'])
def register():
    """注册功能"""
    # 获取参数 mobile password sms_code
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    sms_code = request.json.get('sms_code')
    # 校验参数
    if not all([mobile, password, sms_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验手机格式
    if not re.match('^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 检查验证码是否过期
    real_sms_code = sr.get("sms_code_id_" + mobile)
    if not real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码已过期')
    # 检验sms_code正确
    if sms_code != real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码错误')
    # 保存数据到数据库
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@passport_blu.route('/login', methods=['POST'])
def login():
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 判断手机号格式是否正确
    if not re.match('^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据手机号取出用户模型
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.USERERR, errmsg=error_map[RET.USERERR])
    # 对密码进行比对
    if not user.check_password_hash(password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])
    # 记录最后的登录时间
    user.last_login = datetime.now()
    # 状态保存
    session['user_id'] = user.id
    # 给前端返回登录结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@passport_blu.route('/logout')
def logout():
    session.pop("user_id", None)
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

