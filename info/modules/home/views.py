from flask import render_template, current_app

from . import home_blu


# 2.蓝图对象管理视图函数
@home_blu.route('/')
def index():
    return render_template('index.html')


@home_blu.route('/favicon.ico')  # favicon.ico图标
def favicon():
    return current_app.send_static_file('news/favicon.ico')
