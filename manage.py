# -*- coding:utf-8 -*-
import os
from app import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

manager = Manager(app)
migrate = Migrate(app, db)

# 添加迁移脚本的命令
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()