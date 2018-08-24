import random
import re

from flask import request, abort, make_response, current_app, jsonify

from info import sr
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
        return jsonify(erron=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验手机号格式
    if not re.match('^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$', mobile):
        return jsonify(erron=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据img_code_id取出redis里的img_code_text
    try:
        real_img_code = sr.get("img_code_id_"+img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 判断验证码是否过期
    if not real_img_code:
        return jsonify(erron=RET.PARAMERR, errmsg="验证码过期")
    # 判断验证码是否一致
    if img_code.upper() != real_img_code:
        return jsonify(erron=RET.PARAMERR, errmsg="验证码错误")
    # 根据结果发送短信
    sms_code = "%04d" % random.randint(0, 9999)
    current_app.logger.info('短信验证码为:%s' % sms_code)

    # 将短信验证码存入redis
    try:
        sr.set('sms_code_id_' + mobile, sms_code, ex=60)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回结果给前端
    return jsonify(erron=RET.OK, errmsg=error_map[RET.OK])




