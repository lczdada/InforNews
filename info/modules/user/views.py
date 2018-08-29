from info import db
from info.common import user_loggin_data
from info.models import User
from info.modules.user import user_blu
from flask import render_template, jsonify, g, abort, redirect, request, current_app

from info.utils.image_storage import upload_img
from info.utils.response_code import RET, error_map


@user_blu.route('/user_info')
@user_loggin_data
def user_info():
    user = g.user
    if not user:
        return redirect('/')
    user = user.to_dict()
    return render_template('news/user.html', user=user)


@user_blu.route('/base_info', methods=['GET', 'POST'])
@user_loggin_data
def base_info():
    user =g.user   # type:User
    if not user:
        return abort(404)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    else:
        # 获取参数
        signature = request.json.get('signature')
        nick_name = request.json.get('nick_name')
        gender = request.json.get('gender')
        # 校验参数
        if not all([signature, nick_name, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        if gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        # 替换数据
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender

        return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@user_blu.route('/pic_info', methods=['GET', 'POST'])
@user_loggin_data
def pic_info():
    # 判断是否登录
    user = g.user
    if not user:
        return abort(404)
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user.to_dict())
    else:
        # 获取图片
        try:
            img_bytes = request.files.get('avatar').read()
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        # 上传至第三方服务器
        try:
            file_name = upload_img(img_bytes)
            print(file_name)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

        # 修改用户的头像url
        user.avatar_url = file_name
        return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=user.to_dict())
