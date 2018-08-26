# 定义索引转换的过滤器
import functools

from flask import session, current_app, g

from info.models import User


def index_convert(index):
    index_dict = {1: 'first', 2: 'second', 3: 'third'}
    return index_dict.get(index, '')


def user_loggin_data(f):
    @functools.wraps(f)     # 让闭包函数wrapper使用f的函数信息
    def wrapper(*args, **kwargs):
        # 判断用户是否进行过登录
        user_id = session.get('user_id')
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except BaseException as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)
    return wrapper
