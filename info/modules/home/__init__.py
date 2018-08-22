from flask import Blueprint
# 创建蓝图对象
home_blu = Blueprint('home', __name__)
# 管理视图函数
from .views import *
