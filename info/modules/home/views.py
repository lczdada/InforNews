from flask import current_app

from info import sr
from . import home_blu


# 2.蓝图对象管理视图函数
@home_blu.route('/')
def index():
    # logging.error('发现了一个错误')
    # 以下方式显示效果更加友好
    try:
        1/0
    except BaseException as e:
        current_app.logger.error('发现了一个错误 %s' % e)
    sr.set('age', '20')
    return 'index'
