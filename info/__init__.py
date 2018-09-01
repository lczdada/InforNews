import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, g
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config_dict


db = None  # type:SQLAlchemy
sr = None  # type:StrictRedis


# 设置日志文件(将日志信息写入到文件中 )
def setup_log(level):
    # 设置日志的记录等级
    logging.basicConfig(level=level)  # 测试debug级
    # 创建日志记录器,指明日志保持路径,每个日志的最大大小,保存日志的文件上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的路径名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象(flask app使用的) 添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_type):  # 工厂函数
    """模块中不应该有主动执行的代码,所以将应用的创建封装在函数里"""
    # 根据配置类型取出配置类
    config_class = config_dict[config_type]
    app = Flask(__name__)
    # 根据配置类加载应用配置
    app.config.from_object(config_class)
    # 声明全局变量
    global db, sr
    # 创建数据库连接对象
    db = SQLAlchemy(app)
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)  # 创建redis的连接对象
    Session(app)  # 初始化Session 存储对象,flask-session会自动讲session数据保存在指定的服务器端数据库里
    # 初始化迁移命令
    Migrate(app, db)
    # 注意循环导入,切对于只用一次的内容,可以进行局部导入,什么时候用,什么时候导入
    from info.modules.home import home_blu

    # 注册蓝图
    app.register_blueprint(home_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    # 执行日志函数
    setup_log(config_class.DEBUG_LEVEL)
    # 让模型文件和主程序建立关系
    # from info.models import *  # import * 只能在module level 使用,这里是局部作用域
    from info import models

    # 添加自定义的过滤器
    from info.common import index_convert
    app.add_template_filter(index_convert, 'index_convert')

    # 监听404错误
    from info.common import user_loggin_data

    @app.errorhandler(404)
    @user_loggin_data
    def page_not_found(e):
        user = g.user
        user = user.to_dict() if user else None
        print(e)
        return render_template('news/404.html', user=user)
    # 开启csrf保护
    CSRFProtect(app)

    return app
