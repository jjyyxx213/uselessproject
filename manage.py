# -*- coding:utf-8 -*-
import os
from app import create_app, db
from flask_script import Manager, Command
from flask_migrate import Migrate, MigrateCommand
from app.models import Auth, Role, User, Kvp
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
    objects = []
    objects.append(Auth(id=1, name=u'超级管理员权限', url='/'))
    objects.append(Role(id=1, name=u'超级管理员', auths='1'))
    objects.append(User(id=1, name='admin', pwd=password, phone='18888888888', uuid=uuid.uuid4().hex))
    # key-value pairs init
    objects.append(Kvp(type='unit', value=u'套'))
    objects.append(Kvp(type='unit', value=u'张'))
    objects.append(Kvp(type='unit', value=u'辆'))
    objects.append(Kvp(type='unit', value=u'个'))
    objects.append(Kvp(type='unit', value=u'立方'))
    objects.append(Kvp(type='unit', value=u'毫米'))
    objects.append(Kvp(type='unit', value=u'块'))
    objects.append(Kvp(type='unit', value=u'副'))
    objects.append(Kvp(type='unit', value=u'台'))
    objects.append(Kvp(type='unit', value=u'米'))
    objects.append(Kvp(type='unit', value=u'桶'))
    objects.append(Kvp(type='unit', value=u'瓶'))
    objects.append(Kvp(type='unit', value=u'支'))
    objects.append(Kvp(type='unit', value=u'升'))
    objects.append(Kvp(type='unit', value=u'公斤'))
    objects.append(Kvp(type='unit', value=u'卷'))
    objects.append(Kvp(type='unit', value=u'壶'))
    objects.append(Kvp(type='unit', value=u'盒'))
    objects.append(Kvp(type='unit', value=u'条'))
    objects.append(Kvp(type='unit', value=u'片'))
    objects.append(Kvp(type='unit', value=u'袋'))
    objects.append(Kvp(type='unit', value=u'件'))
    objects.append(Kvp(type='unit', value=u'箱'))
    db.session.add_all(objects)
    db.session.commit()


if __name__ == '__main__':
    manager.run()