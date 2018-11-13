# -*- coding:utf-8 -*-
from functools import wraps
from flask import abort, request, session, redirect, url_for, current_app
from app.models import Auth, User, Role, Admin

# 登录控制
def login_required(f):
    # 登录装饰器
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('home.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function

# 权限控制
def permission_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果是超管直接返回
        admin = Admin.query.filter_by(id=session['user_id']).first()
        if admin is None and current_app.config['DEBUG'] == False:
            # 如果不是,获取用户权限
            # 获取登录用户权限列表
            user = User.query.join(Role).filter(
                Role.id == User.role_id,
                User.id == session['user_id'],
            ).first()
            auths = user.role.auths
            # 权限列表编码
            auths_list = list(map(lambda v: int(v), auths.split(',')))
            # 获取所有权限
            auths_all = Auth.query.all()
            # 将编码转换为url
            urls = [v1.url for v1 in auths_all for v2 in auths_list if v2 == v1.id]
            rule = request.url_rule
            '''
            方案1：[权限限制灵活]如果权限列表urls中包含当前路由rule，就允许访问
            urls:%s [u'/admin/role/add', u'/admin/role/edit']
            rule:%s /admin/role/edit/<int:id>
            '''
            can = False
            for v in urls:
                if v in str(rule):
                    can = True
                    break
            if not can:
                abort(403)
            '''方案2：[权限限制严格] 如果当前页面路由rule在权限了列表urls不存在，不允许访问
            # urls:%s [u'/admin/role/list', u'/admin/admin/add', u'/admin12/admin/list']
            # rule:%s /admin/role/list
            if str(rule) not in urls:
                abort(403)
            '''
        return f(*args, **kwargs)

    return decorated_function