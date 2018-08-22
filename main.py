from datetime import timedelta

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session


class Config:
    DEBUG = True  # 开启调试模式
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/info"  # 设置数据库连接地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 是否追踪数据库变化
    REDIS_HOST = "127.0.0.1"  # redis的ip
    REDIS_PORT = 6379  # redis的端口
    SESSION_TYPE = 'redis'  # session 存储的数据类型
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT) # 设置session存储使用的连接对象
    SESSION_USE_SIGNER = True  # 对cookie中存储的sessionid进行加密, 需要使用秘钥
    SECRET_KEY = "dWkolpXDJYbfZlzk4BvAJzcKaTvCKV+qI4YGRmIWsJUZ3JCC19cVO7AS6JQ+RUFq4ZJ3mfm7JzUay8R7hPs3Ng=="  # 应用秘钥
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # 默认会进行持久化,这里只需要设置时长即可


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)  # 创建数据库连接对象
sr = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)  # 创建redis的连接对象
Session(app)  # 初始化Session 存储对象,flask-session会自动讲session数据保存在指定的服务器端数据库里




@app.route('/index')
def index():
    return 'index'


if __name__ == '__main__':
    app.run()
