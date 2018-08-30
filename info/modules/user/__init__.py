from flask import Blueprint

user_blu = Blueprint('user', __name__, url_prefix='/user')

# 关联视图
from .views import *