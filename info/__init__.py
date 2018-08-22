from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from config import config_dict
from info.modules.home import home_blu


def create_app(config_type):  # 工厂函数
    """模块中不应该有主动执行的代码,所以将应用的创建封装在函数里"""
    # 根据配置类型取出配置类
    config_class = config_dict[config_type]
    app = Flask(__name__)
    # 根据配置类加载应用配置
    app.config.from_object(config_class)
    # 创建数据库连接对象
    db = SQLAlchemy(app)
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)  # 创建redis的连接对象
    Session(app)  # 初始化Session 存储对象,flask-session会自动讲session数据保存在指定的服务器端数据库里
    # 初始化迁移命令
    Migrate(app, db)
    # 注册蓝图
    app.register_blueprint(home_blu)
    return app
