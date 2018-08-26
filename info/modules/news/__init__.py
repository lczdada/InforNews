from flask import Blueprint
# 创建蓝图
news_blu = Blueprint('news', __name__, url_prefix='/news')

# 关联视图
from .views import *
