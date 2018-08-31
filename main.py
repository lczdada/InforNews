import datetime
import random

from flask import current_app
from flask_migrate import MigrateCommand
from flask_script import Manager
from info import create_app


app = create_app('dev')  # 创建应用,传入的参数决定环境的配置

# 创建管理器
mgr = Manager(app)

# 添加迁移命令
mgr.add_command('mc', MigrateCommand)

# 生成超级管理员
@mgr.option('-u', dest='username')
@mgr.option('-p', dest='password')
def create_superuser(username, password):
    if not all([username, password]):
        print('账号/密码不完整')
        return
    from info import db
    from info.models import User
    user = User()
    user.mobile = username
    user.password = password
    user.nick_name = username
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        print('生成失败')

    print('生成管理员成功')


def add_test_users():
    from info import db
    from info.models import User
    users = []
    print(1)
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.nick_name = '%011d' % num
            user.mobile = '%011d' % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            user.last_login = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            user.create_time = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)
            print(user.mobile)

        except BaseException as e:
            print(e)
    db.session.add_all(users)
    db.session.commit()
    print('OK')


if __name__ == '__main__':
    # print(app.url_map)
    mgr.run()
    # add_test_users()