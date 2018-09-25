# -*- coding:utf-8 -*-
from . import home
from flask import render_template, session, redirect, request, url_for, flash, current_app
from forms import LoginForm, PwdForm, CustomerForm, StockBuyForm, StockBuyListForm
from app.models import User, Userlog, Oplog, Item, Supplier, Customer, Stock, Porder, Podetail, Kvp
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_
from json import dumps


@home.route('/', methods=['GET'])
def index():
    return render_template("home/index.html")

@home.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # 验证密码
        user = User.query.filter_by(phone=form.phone.data).first()
        if user is not None and user.verify_password(form.pwd.data) and user.frozen == 0:
            session['user_id'] = user.id
            session['user'] = user.name
            userlog = Userlog(
                user_id=user.id,
                ip=request.remote_addr,
            )
            db.session.add(userlog)
            db.session.commit()
            return redirect(request.args.get('next') or url_for('home.index'))
        flash(u'账户或密码错误', 'err')
        return redirect(url_for('home.login'))
    return render_template('home/login.html', form=form)

@home.route('/logout')
def logout():
    # 用户登出
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('home.login'))

# 20180913 liuqq 修改密码
@home.route('/user/pwd', methods=['GET', 'POST'])
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        # 验证密码
        user = User.query.filter_by(id=session.get('user_id')).first()
        if user.verify_password(form.old_pwd.data) != 1:
            flash(u'旧密码输入错误', 'err')
            return redirect(url_for('home.pwd'))
        if form.new_pwd.data != form.re_pwd.data:
            flash(u'您两次输入的密码不一致!', 'err')
            return redirect(url_for('home.pwd'))
        if form.new_pwd.data == form.old_pwd.data:
            flash(u'新密码与旧密码一致！', 'err')
            return redirect(url_for('home.pwd'))
        new_pwd = generate_password_hash(form.new_pwd.data)
        user.pwd = new_pwd
        db.session.add(user)
        # 20180917 jiangyu 增加修改密码日志
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改密码:%s' % user.name
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'密码修改成功', 'ok')
        return redirect(url_for('home.login'))
    return render_template('home/pwd.html', form=form)

@home.route('/item/list/<int:type>', methods=['GET'])
def item_list(type=0):
    # 商品/服务列表查询
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    # type 0: item; 1: service
    pagination = Item.query.filter_by(type=type)
    # 如果查询了增加查询条件
    if key:
        # 名称/规格/备注
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
    return render_template('home/item_list.html', type=type, pagination=pagination, key=key)

@home.route('/supplier/list', methods=['GET'])
def supplier_list():
    # 供应商列表查询
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
    return render_template('home/supplier_list.html', type=type, pagination=pagination, key=key)


@home.route('/customer/list', methods=['GET'])
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
    return render_template('home/customer_list.html', pagination=pagination, key=key)


# 20180916 liuqq 新增客户
@home.route('/customer/cus_add', methods=['GET', 'POST'])
def customer_add():
    form = CustomerForm()
    if form.validate_on_submit():
        if Customer.query.filter_by(pnumber=form.pnumber.data).first():
            flash(u'您输入的车牌号已存在', 'err')
            return redirect(url_for('home.customer_add'))
        if Customer.query.filter_by(phone=form.phone.data).first():
            flash(u'您输入的手机号已存在', 'err')
            return redirect(url_for('home.customer_add'))

        province = request.form.get('province')

        obj_customer = Customer(
            name=form.name.data,
            name_wechat=form.name_wechat.data,
            sex=int(form.sex.data),
            phone=form.phone.data,
            pnumber=province + form.pnumber.data,
            vin=form.vin.data,
            brand=form.brand.data,
            email=form.email.data,
            id_card=form.id_card.data,
            user_id=form.user_id.data
        )
        obj_oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加客户:%s' % form.name.data
        )
        objects = [obj_customer, obj_oplog]
        db.session.add_all(objects)
        db.session.commit()
        flash(u'客户添加成功', 'ok')
        return redirect(url_for('home.customer_add'))
    return render_template('home/customer_add.html', form=form)


# 20180918 liuqq 修改客户信息
@home.route('/customer/cus_edit/<int:id>', methods=['GET', 'POST'])
def customer_edit(id=None):
    # 修改客户
    form = CustomerForm()
    form.submit.label.text = u'修改'
    obj_customer = Customer.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        # get时进行赋值。应对SelectField无法模板中赋初值
        form.sex.data = int(obj_customer.sex)
    if form.validate_on_submit():
        if obj_customer.pnumber != form.pnumber.data and Customer.query.filter_by(pnumber=form.pnumber.data).first():
            flash(u'您输入的车牌号已存在', 'err')
            return redirect(url_for('home.customer_edit', id=obj_customer.id))
        if obj_customer.phone != form.phone.data and Customer.query.filter_by(phone=form.phone.data).first():
            flash(u'您输入的手机号已存在', 'err')
            return redirect(url_for('home.customer_edit', id=obj_customer.id))

        province = request.form.get('province')

        obj_customer.name = form.name.data,
        obj_customer.name_wechat = form.name_wechat.data,
        obj_customer.sex = int(form.sex.data),
        obj_customer.phone = form.phone.data,
        obj_customer.pnumber = province + form.pnumber.data,
        obj_customer.vin = form.vin.data,
        obj_customer.brand = form.brand.data,
        obj_customer.email = form.email.data,
        obj_customer.id_card = form.id_card.data,
        obj_customer.user_id = form.user_id.data

        db.session.add(obj_customer)
        obj_oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改客户信息:%s' % form.name.data
        )
        db.session.add(obj_oplog)
        db.session.commit()
        flash(u'客户信息修改成功', 'ok')
        return redirect(url_for('home.customer_list'))
    return render_template('home/customer_edit.html', form=form, customer=obj_customer)


@home.route('/stock/list', methods=['GET'])
def stock_list():
    # 库存列表
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = Stock.query.join(Item).filter(
        Item.id == Stock.item_id
    )
    # 条件查询
    if key:
        # 库房/名称
        pagination = pagination.filter(
            or_(Stock.store.ilike('%' + key + '%'),
                Item.name.ilike('%' + key + '%'))
        )
    pagination = pagination.order_by(
        Item.name.asc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/stock_list.html', pagination=pagination, key=key)

@home.route('/stock/buy/<int:id>', methods=['GET', 'POST'])
def stock_buy(id=None):
    # 采购单
    form = StockBuyForm()
    porder = Porder.query.filter_by(id=id).first()
    if not porder:
        porder = Porder(type=0)
        db.session.add(porder)
        db.session.commit()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    if request.method == 'GET':
        # porder赋值
        form.supplier_id.data = porder.supplier_id
        form.user_id.data = porder.user_id
        form.amount.data = porder.amount
        form.discount.data = porder.discount
        form.payment.data = porder.payment
        form.debt.data = porder.debt
        form.remarks.data = porder.remarks
        # 如果存在明细
        if podetails:
            # 先把空行去除
            while len(form.inputrows) > 0:
                form.inputrows.pop_entry()
            # 对FormField赋值，要使用append_entry方法
            for detail in podetails:
                listform = StockBuyListForm()
                listform.item_id = detail.item_id
                listform.item_name = detail.item.name
                listform.item_standard = detail.item.standard
                listform.store = detail.nstore
                listform.qty = detail.qty
                if detail.stock:
                    listform.stock_costprice = detail.stock.costprice
                else:
                    listform.stock_costprice = detail.costprice
                listform.costprice = detail.costprice
                listform.rowamount = detail.rowamount
                form.inputrows.append_entry(listform)


    # 计算动态input的初值
    form_count = len(form.inputrows)
    return render_template('home/stock_buy.html', form=form, porder=porder, form_count=form_count)

@home.route('/modal/item', methods=['GET'])
def modal_item():
    # 获取商品弹出框数据
    key = request.args.get('key', '')
    items = Item.query.outerjoin(
        Stock, Item.id == Stock.item_id
    )
    items = items.filter(Item.valid == 1, Item.type == 0)
    # 条件查询
    if key:
        # 库房/零件名称/类别/规格
        items = items.filter(
            or_(Stock.store.ilike('%' + key + '%'),
                Item.name.ilike('%' + key + '%'),
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
        qty = 0
        stock_costprice = v.costprice
        for j in v.stocks:
            qty += j.qty
            # 上一次的进货价不准确，暂时懒得改了
            stock_costprice = j.costprice
        data.append(
            {
                "id": v.id,
                "name": v.name,
                "qty": qty,
                "standard": v.standard,
                "costprice": v.costprice,
                "salesprice": v.salesprice,
                "cate": v.cate,
                "stock_costprice": stock_costprice,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/store/get', methods=['GET', 'POST'])
def store_get():
    # 获取库房分页清单
    if request.method == 'POST':
        params = request.form.to_dict()
        page = int(params['curPage']) if (params.has_key('curPage')) else 1
        key = params['selectInput'] if (params.has_key('selectInput')) else ''

        pagination = Kvp.query.filter(Kvp.type == 'store')
        # 如果查询了增加查询条件
        if key:
            pagination = pagination.filter(Kvp.value.ilike('%' + key + '%'))
        pagination = pagination.order_by(
            Kvp.value.asc()
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
                {#key和值都用字符
                    "id": v.value,
                    "name": v.value
                }
            )
        res = {
            "pages": pagination.pages,
            "data": data,
        }
    return dumps(res)
