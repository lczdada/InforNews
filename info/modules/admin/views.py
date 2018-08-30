from flask import request, render_template, current_app, session, url_for, redirect

from info.models import User
from info.modules.admin import admin_blu


@admin_blu.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if user_id and is_admin:  # 免密码登录
            return redirect(url_for('admin.index'))

        return render_template('admin/login.html')

    else:
        # 获取参数
        username = request.form.get('username')
        password = request.form.get('password')
        # 校验参数
        if not all([username, password]):
            return render_template('admin/login.html', errmsg='账号或密码不完整')
        # 判断超级管理员是否存在
        try:
            user = User.query.filter_by(mobile=username, is_admin=True).first()
        except BaseException as e:
            current_app.logger.error(e)
            return render_template('admin/login.html', errmsg='数据库查询失败')
        if not user:
            return render_template('admin/login.html', errmsg='该超级管理员不存在')
        # 判断密码是否正确
        if not user.check_password_hash(password):
            return render_template('admin/login.html', errmsg='密码输入错误')

        session['user_id'] = user.id
        session['is_admin'] = True

        # 跳转页面
        return redirect(url_for('admin.index'))


# 后台首页
@admin_blu.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('admin/index.html')


# 后台退出
@admin_blu.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect('/')
