from flask import Blueprint
# 创建蓝图对象
admin_blu = Blueprint('admin', __name__, url_prefix='/admin')


# 后台登录控制
@admin_blu.before_request
def check_superuser():
    # 判断是否登录管理员
    is_admin = session.get('is_admin')
    # 如果没有后台登录, 且不是访问后台登录页面
    if not is_admin and not request.url.endswith('admin/login'):
        return redirect('/')


# 管理视图函数
from .views import *
