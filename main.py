from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

class Config:
    DEBUG = True  # 开启调试模式
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/info"  # 设置数据库连接地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 是否追踪数据库变化
    REDIS_HOST = "127.0.0.1"  # redis的ip
    REDIS_PORT = 6379  # redis的端口

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)  # 创建数据库连接对象
sr = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)  # 创建redis的连接对象


@app.route('/index')
def index():
    return 'index'


if __name__ == '__main__':
    app.run()
