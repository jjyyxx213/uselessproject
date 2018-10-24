# -*- coding:utf-8 -*-
from . import admin
from flask import render_template, url_for, redirect, flash, session, request, current_app, abort
from forms import UserForm, AuthForm, RoleForm, MscardForm, MsdetailForm, MsdetailListForm, CategoryForm, ItemForm, SupplierForm
from app.models import User, Auth, Role, Oplog, Userlog, Mscard, Msdetail, Item, Customer, Category, Supplier, Kvp
from werkzeug.security import generate_password_hash
from app import db
import os, stat, uuid, xlrd, xlwt, collections
from datetime import datetime
from json import dumps
from sqlalchemy import or_
from xlrd import open_workbook

# 上下文处理器获取用户信息
@admin.app_context_processor
def inject_admininfo():
    try:
        user = User.query.filter_by(id=int(session['user_id'])).first()
    except:
        user = None
    context = {
        'user': user,
        'online_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return context

@admin.route("/", methods=["GET"])
def index():
    return redirect(url_for('home.index'))


@admin.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for('home.login'))


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
    # 员工列表
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


@admin.route('/user/frozen', methods=['GET'])
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
        return redirect(url_for('admin.mscard_list'))
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


@admin.route('/mscard/block', methods=['GET'])
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
    msdetails = Msdetail.query.filter_by(mscard_id=id).order_by(Msdetail.id.asc()).all()
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


@admin.route('/customer/list', methods=['GET'])
def customer_list():
    # 客户列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Customer.query
    # 如果查询了增加查询条件
    if key:
        # 姓名/手机/邮箱/车牌号查询
        pagination = pagination.filter(
            or_(Customer.name.ilike('%' + key + '%'),
                Customer.phone.ilike('%' + key + '%'),
                Customer.email.ilike('%' + key + '%'),
                Customer.pnumber.ilike('%' + key + '%'))
        )
    pagination = pagination.join(User).filter(
        User.id == Customer.user_id
    ).order_by(
        Customer.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/customer_list.html', pagination=pagination, key=key)


@admin.route('/category/list/<int:type>', methods=['GET'])
def category_list(type=0):
    # 商品/服务分类列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    # type 0: item; 1: service
    pagination = Category.query.filter_by(type=type)
    # 如果查询了增加查询条件
    if key:
        # 名称查询
        pagination = pagination.filter(
            Category.name.ilike('%' + key + '%')
        )
    pagination = pagination.order_by(
        Category.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/category_list.html', type=type, pagination=pagination, key=key)

@admin.route('/category/add/<int:type>', methods=['GET', 'POST'])
def category_add(type=0):
    # 商品/服务分类添加
    form = CategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data, type=type).first():
            flash(u'您输入的分类已存在', 'err')
            return redirect(url_for('admin.category_add', type=type))
        category = Category(
            name=form.name.data,
            remarks=form.remarks.data,
            type=type
        )
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加商品/服务项目分类:%s' % form.name.data
        )
        objects = [category, oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'分类添加成功', 'ok')
        return redirect(url_for('admin.category_add', type=type))
    return render_template('admin/category_add.html', form=form, type=type)

@admin.route('/category/edit/<int:type>/<int:id>/<string:name>', methods=['GET', 'POST'])
def category_edit(type=0, id=None, name=None):
    # 商品/服务分类修改
    form = CategoryForm()
    form.submit.label.text = u'修改'
    category = Category.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        form.name.data = category.name
        form.remarks.data = category.remarks
    if form.validate_on_submit():
        if category.name != form.name.data and Item.query.filter_by(cate=name).first():
            flash(u'您选择的分类已被商品/服务项目使用，不能修改名称', 'err')
            return redirect(url_for('admin.category_edit', type=type, id=category.id, name=category.name))
        if category.name != form.name.data and Category.query.filter_by(name=form.name.data).first():
            flash(u'您输入的分类已存在，名称不能重复', 'err')
            return redirect(url_for('admin.category_edit', type=type, id=category.id, name=category.name))
        category.name = form.name.data
        category.remarks = form.remarks.data
        db.session.add(category)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改商品/服务项目分类:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'分类修改成功', 'ok')
        return redirect(url_for('admin.category_list', type=type))
    return render_template('admin/category_edit.html', form=form, type=type)

@admin.route('/category/del/<int:type>/<int:id>/<string:name>', methods=['GET', 'POST'])
def category_del(type=0, id=None, name=None):
    # 商品/服务分类删除
    if Item.query.filter_by(cate=name).first():
        flash(u'您选择的分类已使用，不能删除', 'err')
        return redirect(url_for('admin.category_list', type=type))
    category = Category.query.filter_by(id=id).first_or_404()
    db.session.delete(category)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除商品/服务项目分类:%s' % category.name
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'分类删除成功', 'ok')
    return redirect(url_for('admin.category_list', type=type))

@admin.route('/item/list/<int:type>', methods=['GET'])
def item_list(type=0):
    # 商品/服务列表高级权限
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    # type 0: item; 1: service
    pagination = Item.query.filter_by(type=type)
    # 如果查询了增加查询条件
    if key:
        # 名称查询
        pagination = pagination.filter(
            or_(Item.name.ilike('%' + key + '%'),
                Item.standard.ilike('%' + key + '%'),
                Item.remarks.ilike('%' + key + '%'))
        )
    pagination = pagination.order_by(
        Item.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/item_list.html', type=type, pagination=pagination, key=key)

@admin.route('/item/add/<int:type>', methods=['GET', 'POST'])
def item_add(type=0):
    # 商品/服务添加
    form = ItemForm(type=type)
    if form.validate_on_submit():
        # 不对名称做校验了
        #if Item.query.filter_by(name=form.name.data, type=type).first():
        #    flash(u'您输入的名称已存在', 'err')
        #    return redirect(url_for('admin.item_add', type=type))
        item = Item(
            name=form.name.data,
            cate=form.cate.data,
            type=type,
            salesprice=float(form.salesprice.data),
            rewardprice=float(form.rewardprice.data),
            costprice=float(form.costprice.data),
            unit=form.unit.data,
            standard=form.standard.data,
            valid=form.valid.data,
            remarks=form.remarks.data,
        )
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加商品/服务项目:%s' % form.name.data
        )
        objects = [item, oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'添加成功', 'ok')
        return redirect(url_for('admin.item_add', type=type))
    return render_template('admin/item_add.html', form=form, type=type)

@admin.route('/item/edit/<int:type>/<int:id>', methods=['GET', 'POST'])
def item_edit(type=0, id=None):
    # 商品/服务修改
    form = ItemForm(type=type)
    form.submit.label.text = u'修改'
    item = Item.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        form.name.data = item.name
        form.cate.data = item.cate
        form.salesprice.data = item.salesprice
        form.rewardprice.data = item.rewardprice
        form.costprice.data = item.costprice
        form.unit.data = item.unit
        form.standard.data = item.standard
        form.valid.data = item.valid
        form.remarks.data = item.remarks
    if form.validate_on_submit():
        # 不对名称做校验了
        #if item.name != form.name.data and Item.query.filter_by(name=form.name.data, type=type).first():
        #    flash(u'您输入的商品已存在', 'err')
        #    return redirect(url_for('admin.item_edit', type=type, id=item.id))
        item.name = form.name.data
        item.cate = form.cate.data
        item.salesprice = form.salesprice.data
        item.rewardprice = form.rewardprice.data
        item.costprice = form.costprice.data
        item.unit = form.unit.data
        item.standard = form.standard.data
        item.valid = form.valid.data
        item.remarks = form.remarks.data
        db.session.add(item)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改商品/服务项目:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'修改成功', 'ok')
        return redirect(url_for('admin.item_list', type=type))
    return render_template('admin/item_edit.html', form=form, type=type)

@admin.route('/item/block', methods=['POST'])
def item_block():
    # 商品/服务项目停用
    if request.method == 'POST':
        params = request.form.to_dict()
        id = int(params['itemid']) if (params.has_key('itemid')) else None
        type = int(params['type']) if (params.has_key('type')) else 0
    item = Item.query.filter_by(id=id, type=type).first_or_404()
    item.valid = 0
    db.session.add(item)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'停用商品/服务项目:%s' % item.name
    )
    db.session.add(oplog)
    db.session.commit()
    data = {"valid": 0}
    return dumps(data)

@admin.route('/supplier/list', methods=['GET'])
def supplier_list():
    # 供应商列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Supplier.query
    # 条件查询
    if key:
        # 名称/联系人/手机/电话/QQ/备注
        pagination = pagination.filter(
            or_(Supplier.name.ilike('%' + key + '%'),
                Supplier.contact.ilike('%' + key + '%'),
                Supplier.phone.ilike('%' + key + '%'),
                Supplier.tel.ilike('%' + key + '%'),
                Supplier.qq.ilike('%' + key + '%'),
                Supplier.remarks.ilike('%' + key + '%'))
        )
    pagination = pagination.order_by(
        Supplier.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/supplier_list.html', type=type, pagination=pagination, key=key)

@admin.route('/supplier/add', methods=['GET', 'POST'])
def supplier_add():
    # 供应商添加
    form = SupplierForm()
    if form.validate_on_submit():
        if Supplier.query.filter_by(name=form.name.data).first():
            flash(u'您输入的名称已存在', 'err')
            return redirect(url_for('admin.supplier_add'))
        supplier = Supplier(
            name=form.name.data,
            contact=form.contact.data,
            phone=form.phone.data,
            tel=form.tel.data,
            qq=form.qq.data,
            address=form.address.data,
            valid=form.valid.data,
            remarks=form.remarks.data,
        )
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加供应商:%s' % form.name.data
        )
        objects = [supplier, oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'添加成功', 'ok')
        return redirect(url_for('admin.supplier_add'))
    return render_template('admin/supplier_add.html', form=form)

@admin.route('/supplier/edit/<int:id>', methods=['GET', 'POST'])
def supplier_edit(id=None):
    # 供应商修改
    form = SupplierForm()
    form.submit.label.text = u'修改'
    supplier = Supplier.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        form.name.data = supplier.name
        form.contact.data = supplier.contact
        form.phone.data = supplier.phone
        form.tel.data = supplier.tel
        form.qq.data = supplier.qq
        form.address.data = supplier.address
        form.valid.data = supplier.valid
        form.remarks.data = supplier.remarks
    if form.validate_on_submit():
        if supplier.name != form.name.data and Supplier.query.filter_by(name=form.name.data).first():
            flash(u'您输入的供应商已存在', 'err')
            return redirect(url_for('admin.supplier_edit', id=supplier.id))
        supplier.name = form.name.data
        supplier.contact = form.contact.data
        supplier.phone = form.phone.data
        supplier.tel = form.tel.data
        supplier.qq = form.qq.data
        supplier.address = form.address.data
        supplier.valid = form.valid.data
        supplier.remarks = form.remarks.data
        db.session.add(supplier)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改供应商:%s' % form.name.data
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'供应商修改成功', 'ok')
        return redirect(url_for('admin.supplier_list'))
    return render_template('admin/supplier_edit.html', form=form)

@admin.route('/supplier/block', methods=['POST'])
def supplier_block():
    # 供应商停用
    if request.method == 'POST':
        params = request.form.to_dict()
        id = int(params['supid']) if (params.has_key('supid')) else None
    supplier = Supplier.query.filter_by(id=id).first_or_404()
    supplier.valid = 0
    db.session.add(supplier)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'停用供应商:%s' % supplier.name
    )
    db.session.add(oplog)
    db.session.commit()
    data = {"valid": 0}
    return dumps(data)


# 20181023 liuqq 获取供应商信息
@admin.route('/supplier/get', methods=['GET', 'POST'])
def supplier_get():
    # 获取供应商信息
    if request.method == 'POST':
        # 获取json数据
        obj_suppliers = Supplier.query.order_by(Supplier.id)
        if obj_suppliers:
            s_json = []
            valid = ''
            for v in obj_suppliers:
                dic = collections.OrderedDict()
                if v.valid == 1:
                    valid = '有效'
                else:
                    valid = '无效'
                dic[u"编号"] = v.id
                dic[u"名称"] = v.name
                dic[u"联络人"] = v.contact
                dic[u"手机"] = v.phone
                dic[u"联系电话"] = v.tel
                dic[u"QQ"] = v.qq
                dic[u"地址"] = v.address
                dic[u"状态"] = valid
                dic[u"备注"] = v.remarks
                dic[u"添加时间"] = str(v.addtime)
                s_json.append(dic)
            return (dumps(s_json))
        else:
            return (None)


# liuqq Excel打开
def open_excel(file='file.xls'):
    try:
        data = xlrd.open_workbook(file)
        return data
    except Exception as e:
        print (str(e))


# liuqq 根据索引获取Excel表格中的数据   参数:file：Excel文件路径 colnameindex：表头列名所在行的索引，by_index：页夹的索引
def excel_table_byindex(file='file.xls', colnameindex=0, by_index=0):
    data = open_excel(file)
    table = data.sheets()[by_index]
    nrows = table.nrows #行数
    ncols = table.ncols #列数
    colnames =  table.row_values(colnameindex) #某一行数据,默认为第一行
    list =[];
    for rownum in range(1, nrows):
        row = table.row_values(rownum)
        if row:
            list.append(row)
    return colnames, list

# liuqq
@admin.route('/download/<path:filename>', methods=['GET'])
def file_download(filename):
    pass
    #return send_from_directory(dirpath, '1.jpg', as_attachment=True)  # as_attachment=True 一定要写，不然会变成打开，而不是下载


# liuqq 保存导入数据
@admin.route('/item/import/<int:type>', methods=['GET', 'POST'])
def item_import(type=0):
    if request.method == 'GET':
        return render_template('admin/item_import.html', type=type)
    if request.method == 'POST':
        datas = request.get_json()
        try:
            for data in datas:
                item = Item(
                    name=data.get('name'),
                    cate=data.get('cate'),
                    type=type,
                    salesprice=float(data.get('salesprice')),
                    rewardprice=float(data.get('rewardprice')),
                    costprice=float(data.get('costprice')),
                    unit=data.get('unit'),
                    standard=data.get('standard'),
                    valid=1,
                    remarks=data.get('remarks')
                )
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'添加商品/服务项目:%s' % data.get('name')
                )
                objects = [item, oplog]
                db.session.add_all(objects)
            db.session.commit()
            res = {
                "success": True,
            }
            flash(u'导入成功', 'ok')
            return (dumps(res))
        except Exception, e:
            res = {
                "success": False,
            }
            return (dumps(res))


# 20181010 liuqq 商品导入
@admin.route('/item/import_get/<int:type>', methods=['GET', 'POST'])
def item_improt_get(type=0):
    # 获取产品分页清单
    if request.method == 'POST':
        file_path = current_app.config['UPLOAD_DIR']
        re_success = True
        re_messgae = ''
        file = request.files['excelFile']
        fileinfo = file.filename
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]

        #file.save(os.path.join('.\\app\\static', filename))
        #ex_table = excel_table_byindex(file='.\\app\\static\\' + filename)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            os.chmod(file_path, stat.S_IRWXU)

        file.save(os.path.join(file_path, filename))
        ex_table = excel_table_byindex(file=file_path + filename)

        ex_header = ex_table[0]
        ex_content = ex_table[1]

        # 判断表头是否正确
        if u'名称' not in ex_header or \
                u'商品类别' not in ex_header or \
                u'销售价' not in ex_header or \
                u'成本价' not in ex_header or \
                u'提成' not in ex_header or \
                u'单位' not in ex_header or \
                u'规格' not in ex_header or \
                u'备注' not in ex_header:
            re_success = False
            re_messgae = u'(Excel表格式不正确)'
            res = {
                "success": re_success,
                "message": re_messgae
            }
            return (dumps(res))

        s_json = [];
        for row in ex_content:
            err = ''
            if row[0] == '':
                err = err + u'#名称不能为空.'
            if row[1] == '':
                err = err + u'#商品类别不能为空.'
            else:
                item = Category.query.filter_by(name=row[1], type=type).first()
                if item is None:
                    err = err + u'#商品类别不存在.'
            if row[2] == '':
                err = err + u'#销售价不能为空.'
            else:
                if not isinstance(row[2], float):
                    err = err + u'#销售价必须为数字.'
            if row[3] == '':
                err = err + u'#成本价不能为空.'
            else:
                if not isinstance(row[3], float):
                    err = err + u'#成本价必须为数字.'
            if row[4] == '':
                err = err + u'#提成不能为空.'
            else:
                if not isinstance(row[4], float):
                    err = err + u'#提成必须为数字.'
            if row[5] == '':
                err = err + u'#单位不能为空.'
            else:
                unit = Kvp.query.filter_by(value=row[5], type='unit').first()
                if unit is None:
                    err = err + u'#单位不存在.'

            if err != '':
                re_success = False
                re_messgae = u'存在错误信息'

            str_json = {'err': err,
                        'name': row[0],
                        'cate': row[1],
                        'salesprice': row[2],
                        'costprice': row[3],
                        'rewardprice': row[4],
                        'unit': row[5],
                        'standard': row[6],
                        'remarks': row[7]
                        }
            s_json.append(str_json)

        res = {
            "success": re_success,
            "content": s_json,
            "message": re_messgae
        }

        return (dumps(res))

@admin.route('/modal/service', methods=['GET'])
def modal_service():
    # 获取服务弹出框数据
    key = request.args.get('key', '')
    items = Item.query.filter(Item.valid == 1, Item.type == 1)
    # 条件查询
    if key:
        # 库房/零件名称/类别/规格
        items = items.filter(
            or_(Item.name.ilike('%' + key + '%'),
                Item.cate.ilike('%' + key + '%'),
                Item.standard.ilike('%' + key + '%'),
                )
        )
    items = items.order_by(Item.name.asc()).limit(current_app.config['POSTS_PER_PAGE']).all()
    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for v in items:
        data.append(
            {
                "item_id": v.id,
                "item_name": v.name,
                "item_standard": v.standard,
                "item_unit": v.unit,
                "item_costprice": v.costprice,
                "item_salesprice": v.salesprice,
                "item_cate": v.cate,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@admin.route('/modal/item', methods=['GET'])
def modal_item():
    # 获取商品弹出框数据
    key = request.args.get('key', '')
    items = Item.query.filter(Item.valid == 1, Item.type == 0)
    # 条件查询
    if key:
        # 库房/零件名称/类别/规格
        items = items.filter(
            or_(Item.name.ilike('%' + key + '%'),
                Item.cate.ilike('%' + key + '%'),
                Item.standard.ilike('%' + key + '%'),
                )
        )
    items = items.order_by(Item.name.asc()).limit(current_app.config['POSTS_PER_PAGE']).all()
    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for v in items:
        data.append(
            {
                "item_id": v.id,
                "item_name": v.name,
                "item_standard": v.standard,
                "item_unit": v.unit,
                "item_costprice": v.costprice,
                "item_salesprice": v.salesprice,
                "item_cate": v.cate,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

#20181022 liuqq  数据字典查询
@admin.route('/kvp/list', methods=['GET'])
def kvp_list():
    # 数据字典列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Kvp.query
    # 条件查询
    if key:
        # 类型编码/值/添加时间
        pagination = pagination.filter(
            or_(Kvp.type.ilike('%' + key + '%'),
                Kvp.value.ilike('%' + key + '%'),
                Kvp.addtime.ilike('%' + key + '%'))
        )
    pagination = pagination.order_by(
        Kvp.type.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('admin/kvp_list.html', type=type, pagination=pagination, key=key)