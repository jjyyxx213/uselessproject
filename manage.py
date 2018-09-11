# -*- coding:utf-8 -*-
import os
from app import create_app, db
from flask_script import Manager, Command
from flask_migrate import Migrate, MigrateCommand
from app.models import Auth, Role, User
import uuid

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

manager = Manager(app)
migrate = Migrate(app, db)

# 添加迁移数据库脚本的命令
manager.add_command('db', MigrateCommand)

# 添加初始化脚本的命令
# python manage.py dbinit
# 初始化一个权限/角色/管理员用户
@manager.command
def dbinit():
    print ('dbinit')
    from werkzeug.security import generate_password_hash
    password = generate_password_hash('superadmin')
    firstauth = Auth(id=1, name=u'超级管理员权限', url='/')
    firstrole = Role(id=1, name=u'超级管理员', auths='1')
    firstuser = User(id=1, name='admin', pwd=password, phone='18888888888', uuid=uuid.uuid4().hex)
    db.session.add_all([firstauth, firstrole, firstuser])
    db.session.commit()


if __name__ == '__main__':
    manager.run()