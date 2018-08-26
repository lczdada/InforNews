from flask_migrate import MigrateCommand
from flask_script import Manager
from info import create_app

app = create_app('dev')  # 创建应用,传入的参数决定环境的配置

# 创建管理器
mgr = Manager(app)

# 添加迁移命令
mgr.add_command('mc', MigrateCommand)


if __name__ == '__main__':
    print(app.url_map)
    mgr.run()
