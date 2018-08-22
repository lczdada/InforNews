from datetime import timedelta

from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session

from config import DevelopConfig

app = Flask(__name__)
app.config.from_object(DevelopConfig)
db = SQLAlchemy(app)  # 创建数据库连接对象
sr = StrictRedis(host=DevelopConfig.REDIS_HOST, port=DevelopConfig.REDIS_PORT)  # 创建redis的连接对象
Session(app)  # 初始化Session 存储对象,flask-session会自动讲session数据保存在指定的服务器端数据库里

# 创建管理器
mgr = Manager(app)
# 初始化迁移命令
Migrate(app, db)
# 添加迁移命令
mgr.add_command('mc', MigrateCommand)


@app.route('/index')
def index():
    return 'index'


if __name__ == '__main__':
    mgr.run()
