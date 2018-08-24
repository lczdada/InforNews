from flask import request, abort, make_response

from info import sr
from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha


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
    sr.set("img_code_id_" + img_code_id, img_code_text)
    # 返回验证码图片
    response = make_response(img_code)
    response.content_type = 'image/jpeg'
    return response

