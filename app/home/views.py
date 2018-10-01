# -*- coding:utf-8 -*-
from . import home
from flask import render_template, session, redirect, request, url_for, flash, current_app
from forms import LoginForm, PwdForm, CustomerForm, StockBuyForm, StockBuyListForm, StockBuyDebtForm, CusVipForm, StockOutListForm, StockOutForm
from app.models import User, Userlog, Oplog, Item, Supplier, Customer, Stock, Porder, Podetail, Kvp, Mscard, Msdetail, Vip, Vipdetail
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_
from json import dumps
from datetime import datetime, timedelta


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

# 20180920 liuqq 新增客户-会员卡
@home.route('/customer/cus_vip_add/<int:id>', methods=['GET', 'POST'])
def cus_vip_add(id=None):
    form = CusVipForm()
    obj_customer = Customer.query.filter_by(id=id).first()
    form.cus_name.data = obj_customer.name
    if form.validate_on_submit():
        # 计算vip ID
        obj_max_vip = Vip.query.order_by(Vip.id.desc()).first()
        if(obj_max_vip):
            max_vip_id = obj_max_vip.id + 1
        else:
            max_vip_id = 1

        # 计算截止日期
        interval_day = int(form.interval.data) * 30  # 卡的有效期*30天
        add_time = datetime.now()
        end_time = add_time + timedelta(days=interval_day)

        # 计算引用vip卡的名称
        obj_mscard = Mscard.query.filter_by(id=form.name.data).first()
        # 创建VIP主表对象
        obj_vip = Vip(
            id = max_vip_id,
            name=obj_mscard.name,  # 名称
            balance=form.payment.data,  # 余额
            scorerule=form.scorerule.data,  # 积分规则
            scorelimit=form.scorelimit.data,  # 积分限制提醒
            addtime=add_time,  # 办理时间
            endtime=end_time,  # 截止时间 = 办理时间 + 有效期
        )
        obj_oplog_vip = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加客户vip卡:%s' % max_vip_id
        )
        # 数据提交
        objects = [obj_vip, obj_oplog_vip]
        db.session.add_all(objects)
        db.session.commit()

        # 保存客户与vip—id关系
        obj_customer.vip_id = max_vip_id
        obj_oplog_cus = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加客户与vip卡关系及明细:%s' % max_vip_id
        )
        objects = [obj_customer, obj_oplog_cus]
        db.session.add_all(objects)

        # 保存vip明细内容
        for iter_add in form.inputrows:
            interval_day = int(form.interval.data) * 30  # 卡的有效期*30天
            obj_vip_detail = Vipdetail(
                vip_id=max_vip_id,  # 客户会员卡号
                item_id=iter_add.item_id.data,  # 服务/项目id
                discountprice=iter_add.discountprice.data,  # 优惠后销售价
                quantity=iter_add.quantity.data,  # 使用次数
                addtime=add_time,  # 优惠开始时间
                endtime=add_time + timedelta(days=interval_day)  # 优惠结束时间 = 优惠开始时间 + 有效期
            )
            db.session.add(obj_vip_detail)

        db.session.commit()
        flash(u'客户-会员卡添加成功', 'ok')
        return redirect(url_for('home.customer_list'))

    return render_template('home/cus_vip_add.html', form=form)


# 20180922 liuqq 获取会员卡信息
@home.route('/mscard/get', methods=['GET', 'POST'])
def mscard_get():
    # 获取产品分页清单
    if request.method == 'POST':
        # 获取json数据
        data = request.get_json()
        id = data.get('id')
        obj_mscard = Mscard.query.filter_by(id=id).first()
        s_json = obj_mscard.to_json()
        return (dumps(s_json))


# 20180923 liuqq 获取会员卡明细信息
@home.route('/msdetails/get', methods=['GET', 'POST'])
def msdetails_get():
    # 获取产品分页清单
    if request.method == 'POST':
        # 获取json数据
        data = request.get_json()
        id = data.get('id')
        # 将数据查询出来
        obj_msdetails = Msdetail.query.filter_by(mscard_id=id).order_by(Msdetail.item_id.asc()).all()
        s_json = [];
        for obj_msdetail in obj_msdetails:
            s_json.append(obj_msdetail.to_json())
        return (dumps(s_json))


# 20180930 liuqq 查询客户-会员卡明细
@home.route('/customer/cus_vip_list/<int:vip_id>', methods=['GET'])
def cus_vip_list(vip_id=None):
    # 明细查看
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    obj_vip_details = Vipdetail.query.filter_by(vip_id=vip_id).order_by(Vipdetail.id.asc()).all()
    return render_template('home/cus_vip_list.html', obj_vip=obj_vip, obj_vip_details=obj_vip_details)

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
                "unit": v.unit,
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

@home.route('/stock/buy/list', methods=['GET'])
def stock_buy_list():
    # 采购单列表
    key = request.args.get('key', '')
    # 采购单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    # 是否欠款 true 欠;false 否
    debt = request.args.get('debt', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Porder.query.filter_by(type=0)
    # 条件查询
    if key:
        # 单号/备注
        pagination = pagination.filter(
            or_(Porder.id.ilike('%' + key + '%'),
                Porder.remarks.ilike('%' + key + '%'),
                Porder.addtime.ilike('%' + key + '%'))
        )
    if status == 'true':
        pagination = pagination.filter(Porder.status == 0)
    if debt == 'true':
        pagination = pagination.filter(Porder.debt > 0)
    pagination = pagination.order_by(
        Porder.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/stock_buy_list.html', pagination=pagination, key=key, status=status, debt=debt)

@home.route('/stock/buy/view/<int:id>', methods=['GET'])
def stock_buy_view(id=None):
    # 明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_buy_view.html', porder=porder, podetails=podetails)

@home.route('/stock/buy/debt/<int:id>', methods=['GET', 'POST'])
def stock_buy_debt(id=None):
    # 结款
    form = StockBuyDebtForm()
    porder = Porder.query.filter_by(id=id).first_or_404()
    # 如果表单不属于用户，不是发布状态 退出
    if porder.user_id != int(session['user_id']) or porder.status == 0 or porder.type != 0:
        return redirect(url_for('home.stock_buy_list'))
    if request.method == 'GET':
        form.amount.data = porder.amount
        form.discount.data = porder.discount
        form.payment.data = porder.payment
        form.debt.data = porder.debt
        form.remarks.data = porder.remarks
    if form.validate_on_submit():
        porder.amount = form.amount.data
        porder.discount = form.discount.data
        porder.payment = form.payment.data
        porder.debt = form.debt.data
        porder.remarks = form.remarks.data
        db.session.add(porder)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改结款,订单号:%s' % porder.id
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'结款修改成功', 'ok')
        return redirect(url_for('home.stock_buy_list'))
    return render_template('home/stock_buy_debt.html', form=form, porder=porder)


@home.route('/stock/buy/edit/<int:id>', methods=['GET', 'POST'])
def stock_buy_edit(id=None):
    # 采购单
    form = StockBuyForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 0:
            return redirect(url_for('home.stock_buy_list'))
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    if request.method == 'GET':
        # porder赋值
        if porder:
            form.supplier_id.data = porder.supplier_id
            form.user_name.data = porder.user.name
            form.amount.data = porder.amount
            form.discount.data = porder.discount
            form.payment.data = porder.payment
            form.debt.data = porder.debt
            form.remarks.data = porder.remarks
        else:
            form.user_name.data = session['user']
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
                listform.item_unit = detail.item.unit
                listform.store = detail.nstore
                listform.qty = detail.qty
                listform.costprice = detail.costprice
                listform.rowamount = detail.rowamount
                form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    if form.validate_on_submit():
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
        # 提交类别 1：生效；0：暂存
        status = 1 if switch == 1 else 0
        # 添加主表
        if not porder:  # 没有新增一个
            porder = Porder(
                type=0,
                user_id=int(session['user_id']),
                supplier_id=form.supplier_id.data,
                amount=form.amount.data,
                discount=form.discount.data,
                payment=form.payment.data,
                debt=form.debt.data,
                status=status,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.supplier_id = form.supplier_id.data
            porder.amount = form.amount.data
            porder.discount = form.discount.data
            porder.payment = form.payment.data
            porder.debt = form.debt.data
            porder.status = status
            porder.remarks = form.remarks.data
        db.session.add(porder)
        db.session.commit()  # 这里实现的不太好，提交一下后面要获取值
        if switch == 1:#结算
            # 删除所有明细
            for iter_del in podetails:
                db.session.delete(iter_del)
            for iter_add in form.inputrows:
                # 新增明细
                podetail = Podetail(
                    porder_id=porder.id,
                    item_id=iter_add.item_id.data,
                    nstore=iter_add.store.data,
                    qty=iter_add.qty.data,
                    costprice=iter_add.costprice.data,
                    rowamount=iter_add.rowamount.data,
                )
                db.session.add(podetail)
                # 判断库存是否存在
                stock = Stock.query.filter_by(item_id=iter_add.item_id.data,
                                              store=iter_add.store.data).first()
                if stock: #存在就更新数量
                    stock.qty += float(iter_add.qty.data)
                    costprice = iter_add.costprice.data
                else: #不存在库存表加一条
                    stock = Stock(
                        item_id=iter_add.item_id.data,
                        costprice=iter_add.costprice.data,
                        qty=iter_add.qty.data,
                        store=iter_add.store.data,
                    )
                db.session.add(stock)
                # 设置主表为发布
                porder.status = 1
                db.session.add(porder)
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'结算采购单:%s' % porder.id
            )
            db.session.add(oplog)
            db.session.commit()
            flash(u'采购单结算成功', 'ok')
        else:#暂存
            # 删除所有明细
            for iter_del in podetails:
                db.session.delete(iter_del)
            for iter_add in form.inputrows:
                # 新增明细
                podetail = Podetail(
                    porder_id=porder.id,
                    item_id=iter_add.item_id.data,
                    nstore=iter_add.store.data,
                    qty=iter_add.qty.data,
                    costprice=iter_add.costprice.data,
                    rowamount=iter_add.rowamount.data,
                )
                db.session.add(podetail)
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存采购单:%s' % porder.id
            )
            db.session.commit()
            flash(u'采购单暂存成功', 'ok')
        return redirect(url_for('home.stock_buy_list'))
    return render_template('home/stock_buy_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/buy/del/<int:id>', methods=['GET'])
def stock_buy_del(id=None):
    # 采购单删除
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).all()
    if porder.type != 0 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_buy_list'))
    db.session.delete(porder)
    for iter_del in podetails:
        db.session.delete(iter_del)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除采购单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'采购单删除成功', 'ok')
    return redirect(url_for('home.stock_buy_list'))

@home.route('/stock/out/list', methods=['GET'])
def stock_out_list():
    # 领料单列表
    key = request.args.get('key', '')
    # 采购单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Porder.query.filter_by(type=1)
    # 条件查询
    if key:
        # 单号/备注
        pagination = pagination.filter(
            or_(Porder.id.ilike('%' + key + '%'),
                Porder.remarks.ilike('%' + key + '%'),
                Porder.addtime.ilike('%' + key + '%'))
        )
    if status == 'true':
        pagination = pagination.filter(Porder.status == 0)
    pagination = pagination.order_by(
        Porder.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/stock_out_list.html', pagination=pagination, key=key, status=status)

@home.route('/stock/out/edit/<int:id>', methods=['GET', 'POST'])
def stock_out_edit(id=None):
    # 出库单
    form = StockOutForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 1:
            return redirect(url_for('home.stock_out_list'))
    #podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    podetails = db.session.query(Podetail, Stock).filter(
        Podetail.item_id == Stock.item_id,
        Podetail.nstore == Stock.store,
        Podetail.porder_id == id,
    ).order_by(Podetail.id.asc()).all()
    if request.method == 'GET':
        # porder赋值
        if porder:
            form.user_name.data = porder.user.name
            form.remarks.data = porder.remarks
        else:
            form.user_name.data = session['user']
        # 如果存在明细
        if podetails:
            # 先把空行去除
            while len(form.inputrows) > 0:
                form.inputrows.pop_entry()
            # 对FormField赋值，要使用append_entry方法
            for detail in podetails:
                listform = StockOutListForm()
                listform.item_id = detail.Podetail.item_id
                listform.item_name = detail.Podetail.item.name
                listform.item_standard = detail.Podetail.item.standard
                listform.item_unit = detail.Podetail.item.unit
                listform.costprice = detail.Podetail.item.costprice # 新增商品的价格
                listform.stock_costprice = detail.Stock.costprice # 库存中最后一次采购价
                listform.store = detail.Podetail.nstore
                listform.stock_qty = detail.Stock.qty
                listform.qty = detail.Podetail.qty
                form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    # todo 以下内容未完成仍需调试
    if form.validate_on_submit():
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
        # 提交类别 1：生效；0：暂存
        status = 1 if switch == 1 else 0
        # 添加主表
        if not porder:  # 没有新增一个
            porder = Porder(
                type=1,
                user_id=int(session['user_id']),
                status=status,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.status = status
            porder.remarks = form.remarks.data
        db.session.add(porder)
        db.session.commit()  # 这里实现的不太好，提交一下后面要获取值
        if switch == 1:#结算
            # 删除所有明细
            for iter_del in podetails:
                db.session.delete(iter_del)
            for iter_add in form.inputrows:
                # 新增明细
                podetail = Podetail(
                    porder_id=porder.id,
                    item_id=iter_add.item_id.data,
                    nstore=iter_add.store.data,
                    qty=iter_add.qty.data,
                    costprice=iter_add.costprice.data,
                    rowamount=iter_add.rowamount.data,
                )
                db.session.add(podetail)
                # 判断库存是否存在
                stock = Stock.query.filter_by(item_id=iter_add.item_id.data,
                                              store=iter_add.store.data).first()
                if stock: #存在就更新数量
                    stock.qty += float(iter_add.qty.data)
                    costprice = iter_add.costprice.data
                else: #不存在库存表加一条
                    stock = Stock(
                        item_id=iter_add.item_id.data,
                        costprice=iter_add.costprice.data,
                        qty=iter_add.qty.data,
                        store=iter_add.store.data,
                    )
                db.session.add(stock)
                # 设置主表为发布
                porder.status = 1
                db.session.add(porder)
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'结算采购单:%s' % porder.id
            )
            db.session.add(oplog)
            db.session.commit()
            flash(u'采购单结算成功', 'ok')
        else:#暂存
            # 删除所有明细
            for iter_del in podetails:
                db.session.delete(iter_del)
            for iter_add in form.inputrows:
                # 新增明细
                podetail = Podetail(
                    porder_id=porder.id,
                    item_id=iter_add.item_id.data,
                    nstore=iter_add.store.data,
                    qty=iter_add.qty.data,
                    costprice=iter_add.costprice.data,
                    rowamount=iter_add.rowamount.data,
                )
                db.session.add(podetail)
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存采购单:%s' % porder.id
            )
            db.session.commit()
            flash(u'采购单暂存成功', 'ok')
        return redirect(url_for('home.stock_out_edit'))
    return render_template('home/stock_out_edit.html', form=form, porder=porder, form_count=form_count)