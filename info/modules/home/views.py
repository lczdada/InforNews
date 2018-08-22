from . import home_blu


# 2.蓝图对象管理视图函数
@home_blu.route('/index')
def index():
    return 'index'
