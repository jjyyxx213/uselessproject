# -*- coding:utf-8 -*-
from . import admin
from flask import render_template, url_for, redirect, flash, session, request, current_app, abort
from forms import UserForm, AuthForm, RoleForm, MscardForm, MsdetailForm, MsdetailListForm, PwdModForm
from app.models import User, Auth, Role, Oplog, Userlog, Mscard, Msdetail, Item
from werkzeug.security import generate_password_hash
from app import db
import os, stat, uuid
from datetime import datetime
from json import dumps


@admin.route("/", methods=["GET"])
def index():
    return redirect(url_for('home.index'))


@admin.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for('home.login'))


# 20180913 liuqq 修改密码
@admin.route('/user/pwd_edit',methods=['GET', 'POST'])
def pwd_edit():
    form = PwdModForm()
    if form.validate_on_submit():
        # 验证密码
        user = User.query.filter_by(id=session.get('user_id')).first()
        if user.verify_password(form.old_pwd.data) != 1:
            flash(u'旧密码输入错误', 'err')
            return redirect(url_for('admin.pwd_edit'))
        if form.new_pwd.data != form.re_pwd.data:
            flash(u'您两次输入的密码不一致!', 'err')
            return redirect(url_for('admin.pwd_edit'))
        if form.new_pwd.data == form.old_pwd.data:
            flash(u'新密码与旧密码一致！', 'err')
            return redirect(url_for('admin.pwd_edit'))
        new_pwd = generate_password_hash(form.new_pwd.data)
        user.pwd = new_pwd
        db.session.add(user)
        db.session.commit()
        flash(u'密码修改成功', 'ok')
        return redirect(url_for('home.index'))
    return render_template('admin/pwd_edit.html', form=form)


@admin.route('/auth/add', methods=['GET', 'POST'])
def auth_add():
    # 权限添加
    form = AuthForm()
    if form.validate_on_submit():
        if Auth.query.filter_by(name=form.name.data).first():
            flash(u'您输入的权限已存在', 'err')
            return redirect(url_for('admin.auth_add'))
        if Auth.query.filter_by(url=form.url.data).first():
            flash(u'您输入的路由已存在', 'err')
            return redirect(url_for('admin.auth_add'))
        auth = Auth(
            name=form.name.data,
            url=form.url.data
        )
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加权限:%s' % form.name.data
        )
        objects = [auth, oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'权限添加成功', 'ok')
        return redirect(url_for('admin.auth_add'))
    return render_template('admin/auth_add.html', form=form)


@admin.route('/auth/edit/<int:id>', methods=['GET', 'POST'])
def auth_edit(id=None):
    # 权限修改
    form = AuthForm()
    form.submit.label.text = u'修改'
    auth = Auth.query.filter_by(id=id).first_or_404()
    if form.validate_on_submit():
        if auth.name != form.name.data and Auth.query.filter_by(name=form.name.data).first():
            flash(u'您输入的权限已存在', 'err')
            return redirect(url_for('admin.auth_edit', id=auth.id))
        if auth.url != form.url.data and Auth.query.filter_by(url=form.url.data).first():
            flash(u'您输入的路由已存在', 'err')
            return redirect(url_for('admin.auth_edit', id=auth.id))
        auth.name = form.name.data
        auth.url = form.url.data
        db.session.add(auth)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改权限:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'权限修改成功', 'ok')
        return redirect(url_for('admin.auth_list'))
    return render_template('admin/auth_edit.html', form=form, auth=auth)


@admin.route('/auth/del/<int:id>', methods=['GET', 'POST'])
def auth_del(id=None):
    # 权限删除
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除权限:%s' % auth.name
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'权限删除成功', 'ok')
    return redirect(url_for('admin.auth_list'))


@admin.route('/auth/list', methods=['GET'])
def auth_list():
    # 权限列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Auth.query
    # 如果查询了增加查询条件
    if key:
        pagination = pagination.filter(Auth.name.ilike('%' + key + '%'))
    pagination = pagination.order_by(
        Auth.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/auth_list.html', pagination=pagination, key=key)


@admin.route('/role/add', methods=['GET', 'POST'])
def role_add():
    # 角色添加
    form = RoleForm()
    if form.validate_on_submit():
        if Role.query.filter_by(name=form.name.data).first():
            flash(u'您输入的角色已存在', 'err')
            return redirect(url_for('admin.role_add'))
        role = Role(
            name=form.name.data,
            # lambda v: str(v) 匿名函数，将v转换为字符串
            # map(f, [list])内置函数,接收一个函数 f 和一个 list，并通过把函数 f 依次作用在 list 的每个元素上，得到一个新的 list 并返回
            auths=','.join(map(lambda v: str(v), form.auths.data))
        )
        db.session.add(role)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加角色:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'角色添加成功', 'ok')
        return redirect(url_for('admin.role_add'))
    return render_template('admin/role_add.html', form=form)


@admin.route('/role/edit<int:id>', methods=['GET', 'POST'])
def role_edit(id=None):
    # 角色修改
    form = RoleForm()
    form.submit.label.text = u'修改'
    role = Role.query.get_or_404(id)
    if request.method == 'GET':
        auths = role.auths
        # get时进行赋值。应对无法模板中赋初值
        form.auths.data = list(map(lambda v: int(v), auths.split(",")))
    if form.validate_on_submit():
        if role.name != form.name.data and Role.query.filter_by(name=form.name.data).first():
            flash(u'您输入的角色已存在', 'err')
            return redirect(url_for('admin.role_edit', id=role.id))
        role.name = form.name.data
        role.auths = ','.join(map(lambda v: str(v), form.auths.data))
        db.session.add(role)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改角色:%s' % role.name
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'角色修改成功', 'ok')
        return redirect(url_for('admin.role_list'))
    return render_template('admin/role_edit.html', form=form, role=role)


@admin.route("/role/del/<int:id>/", methods=['GET', 'POST'])
def role_del(id=None):
    # 角色删除
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除角色:%s' % role.name
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'角色删除成功', 'ok')
    return redirect(url_for('admin.role_list'))


@admin.route('/role/list', methods=['GET'])
def role_list():
    # 角色列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Role.query
    # 如果查询了增加查询条件
    if key:
        pagination = pagination.filter(Role.name.ilike('%' + key + '%'))
    pagination = pagination.order_by(
        Role.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/role_list.html', pagination=pagination, key=key)


@admin.route('/user/add', methods=['GET', 'POST'])
def user_add():
    # 员工添加
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(phone=form.phone.data).first():
            flash(u'您输入的手机已存在', 'err')
            return redirect(url_for('admin.user_add'))
        if User.query.filter_by(id_card=form.id_card.data).first():
            flash(u'您输入的身份证已存在', 'err')
            return redirect(url_for('admin.user_add'))
        user = User(
            name=form.name.data,
            phone=form.phone.data,
            id_card=form.id_card.data,
            salary=form.salary.data,
            # jobs=form.jobs.data,
            pwd=generate_password_hash(form.pwd.data),
            role_id=form.role_id.data,
            frozen=int(form.frozen.data),
            uuid=uuid.uuid4().hex
        )
        db.session.add(user)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加员工:%s' % user.name
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'添加员工成功', 'ok')
        return redirect(url_for('admin.user_add'))
    return render_template('admin/user_add.html', form=form)


@admin.route('/user/edit/<int:id>', methods=['GET', 'POST'])
def user_edit(id=None):
    # 员工修改
    form = UserForm()
    form.submit.label.text = u'修改'
    user = User.query.get_or_404(id)
    if request.method == 'GET':
        # get时进行赋值。应对SelectField无法模板中赋初值
        form.role_id.data = user.role_id
        form.frozen.data = user.frozen
    if form.validate_on_submit():
        if user.phone != form.phone.data and User.query.filter_by(phone=form.phone.data).first():
            flash(u'您输入的手机已存在', 'err')
            return redirect(url_for('admin.user_edit', id=user.id))
        if user.id_card != form.id_card.data and User.query.filter_by(id_card=form.id_card.data).first():
            flash(u'您输入的身份证已存在', 'err')
            return redirect(url_for('admin.user_edit', id=user.id))

        user.name = form.name.data
        user.phone = form.phone.data
        user.id_card = form.id_card.data
        user.salary = form.salary.data
        # user.jobs=form.jobs.data
        user.pwd = generate_password_hash(form.pwd.data)
        user.role_id = form.role_id.data
        user.frozen = form.frozen.data

        db.session.add(user)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改员工:%s' % user.name
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'修改员工成功', 'ok')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_edit.html', form=form, user=user)


@admin.route('/user/list', methods=['GET'])
def user_list():
    # 用户列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = User.query
    # 如果查询了增加查询条件
    if key:
        pagination = pagination.filter(User.name.ilike('%' + key + '%'))
    pagination = pagination.join(Role).filter(
        Role.id == User.role_id
    ).order_by(
        User.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/user_list.html', pagination=pagination, key=key)


@admin.route('/user/frozen')
def user_frozen():
    # 员工冻结
    uid = request.args.get('uid', '')
    user = User.query.filter_by(id=uid).first_or_404()
    user.frozen = 1
    db.session.add(user)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'冻结员工:%s' % user.name
    )
    db.session.add(oplog)
    db.session.commit()
    data = {"frozen": 1}
    return dumps(data)


# @admin.route('/user/unfrozen')
# def user_unfrozen():
#     # 员工解冻
#     uid = request.args.get('uid', '')
#     user = User.query.filter_by(id=uid).first_or_404()
#     user.frozen = 0
#     db.session.add(user)
#     oplog = Oplog(
#         user_id=session['user_id'],
#         ip=request.remote_addr,
#         reason=u'解冻员工:%s' % user.name
#     )
#     db.session.add(oplog)
#     db.session.commit()
#     data = {"unfrozen": 1}
#     return dumps(data)

@admin.route('/oplog/list', methods=['GET'])
def oplog_list():
    # 操作日志
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '')
    pagination = Oplog.query.join(User).filter(Oplog.user_id == User.id)
    # 如果查询了增加查询条件
    if key:
        print key
        pagination = pagination.filter(User.name.ilike('%' + key + '%'))
    pagination = pagination.order_by(
        Oplog.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/oplog_list.html', pagination=pagination, key=key)


@admin.route('/userloginlog/list', methods=['GET'])
def userloginlog_list():
    # 员工登录日志列表
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '')
    pagination = Userlog.query.join(User).filter(
        Userlog.user_id == User.id
    )
    # 如果查询了增加查询条件
    if key:
        pagination = pagination.filter(User.name.ilike('%' + key + '%'))
    pagination = pagination.order_by(
        Userlog.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/userloginlog_list.html', pagination=pagination, key=key)


@admin.route('/mscard/list', methods=['GET'])
def mscard_list():
    # 会员卡列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Mscard.query
    # 如果查询了增加查询条件
    if key:
        pagination = pagination.filter(Mscard.name.ilike('%' + key + '%'))
    pagination = pagination.order_by(
        Mscard.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/mscard_list.html', pagination=pagination, key=key)


@admin.route('/mscard/add', methods=['GET', 'POST'])
def mscard_add():
    # 添加会员卡
    form = MscardForm()
    if form.validate_on_submit():
        if Mscard.query.filter_by(name=form.name.data).first():
            flash(u'您输入的会员卡已存在', 'err')
            return redirect(url_for('admin.mscard_add'))
        mscard = Mscard(
            name=form.name.data,
            payment=float(form.payment.data),
            interval=float(form.interval.data),
            scorerule=float(form.scorerule.data),
            scorelimit=float(form.scorelimit.data),
            valid=int(form.valid.data),
        )
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加会员卡:%s' % form.name.data
        )
        objects = [mscard, oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'会员卡添加成功', 'ok')
        return redirect(url_for('admin.mscard_add'))
    return render_template('admin/mscard_add.html', form=form)


@admin.route('/mscard/edit/<int:id>', methods=['GET', 'POST'])
def mscard_edit(id=None):
    # 修改会员卡
    form = MscardForm()
    form.submit.label.text = u'修改'
    mscard = Mscard.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        # get时进行赋值。应对RadioField无法模板中赋初值
        form.valid.data = mscard.valid
    if form.validate_on_submit():
        if mscard.name != form.name.data and Mscard.query.filter_by(name=form.name.data).first():
            flash(u'您输入的会员卡已存在', 'err')
            return redirect(url_for('admin.mscard_edit', id=mscard.id))
        mscard.name = form.name.data
        mscard.payment = form.payment.data
        mscard.interval = form.interval.data
        mscard.scorerule = form.scorerule.data
        mscard.scorelimit = form.scorelimit.data
        mscard.valid = form.valid.data
        db.session.add(mscard)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改会员卡:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'会员卡修改成功', 'ok')
        return redirect(url_for('admin.mscard_list'))
    return render_template('admin/mscard_edit.html', form=form, mscard=mscard)


@admin.route('/mscard/block')
def mscard_block():
    # 会员卡停用
    msid = request.args.get('msid', '')
    mscard = Mscard.query.filter_by(id=msid).first_or_404()
    mscard.valid = 0
    db.session.add(mscard)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'停用会员卡:%s' % mscard.name
    )
    db.session.add(oplog)
    db.session.commit()
    data = {"valid": 0}
    return dumps(data)


@admin.route('/mscard/msdetail/edit/<int:id>', methods=['GET', 'POST'])
def msdetail_edit(id=None):
    # 编辑会员卡套餐明细
    form = MsdetailForm()
    mscard = Mscard.query.filter_by(id=id).first_or_404()
    msdetails = Msdetail.query.filter_by(mscard_id=id).order_by(Msdetail.item_id.asc()).all()
    if request.method == 'GET' and msdetails:
        # 先把空行去除
        while len(form.inputrows) > 0:
            form.inputrows.pop_entry()
        # 对FormField赋值，要使用append_entry方法
        for detail in msdetails:
            listform = MsdetailListForm()
            listform.item_id = detail.item_id
            listform.item_name = detail.item.name
            listform.salesprice = detail.item.salesprice
            listform.discountprice = detail.discountprice
            listform.quantity = detail.quantity
            listform.interval = detail.interval
            form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    if form.validate_on_submit():
        # 删除所有明细
        for iter_del in msdetails:
            db.session.delete(iter_del)
        # 新增明细
        for iter_add in form.inputrows:
            msdetail = Msdetail(
                mscard_id=mscard.id,
                item_id=iter_add.item_id.data,
                discountprice=iter_add.discountprice.data,
                quantity=iter_add.quantity.data,
                interval=iter_add.interval.data,
            )
            db.session.add(msdetail)
        db.session.commit()
        flash(u'套餐明细保存成功', 'ok')
        return redirect(url_for('admin.mscard_list'))
    return render_template('admin/msdetail_edit.html', form=form, form_count=form_count, mscard=mscard)


@admin.route('/item/get', methods=['GET', 'POST'])
def item_get():
    # 获取产品分页清单
    # items = Item.query.order_by(Item.id.asc()).all()
    # data = []
    # for item in items:
    #     data.append(item.to_json())
    if request.method == 'POST':
        params = request.form.to_dict()
        page = int(params['curPage']) if (params.has_key('curPage')) else 1
        key = params['selectInput'] if (params.has_key('selectInput')) else ''

        pagination = Item.query
        # 如果查询了增加查询条件
        if key:
            pagination = pagination.filter(Item.name.ilike('%' + key + '%'))
        pagination = pagination.order_by(
            Item.id.asc()
        ).paginate(page=page,
                   per_page=current_app.config['POSTS_PER_PAGE'],
                   error_out=False)

        # 返回的数据格式为
        # {
        # "pages": 1,
        # "data": [
        #         {"id": "1",
        #         "name": "xx"}
        #         ]
        # }
        data = []
        for v in pagination.items:
            data.append(
                {
                    "id": v.id,
                    "name": v.name
                }
            )
        res = {
            "pages": pagination.pages,
            "data": data,
        }
    return dumps(res)
