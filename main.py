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

if __name__ == '__main__':
    # print(app.url_map)
    mgr.run()
