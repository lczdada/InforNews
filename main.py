from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/info"  # 设置数据库连接地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 是否追踪数据库变化


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)  # 创建数据库连接对象


@app.route('/index')
def index():
    return 'index'


if __name__ == '__main__':
    app.run()
