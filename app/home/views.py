# -*- coding:utf-8 -*-
from . import home
from flask import render_template, session, redirect, request, url_for, flash, current_app
from forms import LoginForm, PwdForm, CustomerForm, CusVipForm, StockBuyForm, StockBuyListForm, StockBuyDebtForm, \
    StockOutListForm, StockOutForm, StockAllotListForm, StockAllotForm, StockLossListForm, StockLossForm, StockReturnListForm, StockReturnForm, StockReturnDebtForm, CusVipDepositForm
from app.models import User, Userlog, Oplog, Item, Supplier, Customer, Stock, Porder, Podetail, Kvp, Mscard, Msdetail, Vip, Vipdetail
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_, func, text
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
            #interval_day = int(form.interval.data) * 30  # 卡的有效期*30天
            # 20181008 liuqq 修改bug
            interval_day = int(iter_add.interval.data) * 30  # 卡的有效期*30天
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
# 20181007 liuqq 注销客户-会员卡
@home.route('/customer/cus_vip_list/<int:vip_id>', methods=['GET', 'POST'])
def cus_vip_list(vip_id=None):
    # 明细查看
    obj_customer = Customer.query.filter_by(vip_id=vip_id).first()
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    obj_vip_details = Vipdetail.query.filter_by(vip_id=vip_id).order_by(Vipdetail.id.asc()).all()
    if request.method == 'GET':
        return render_template('home/cus_vip_list.html', obj_vip=obj_vip, obj_vip_details=obj_vip_details)
    if request.method == 'POST':
        obj_customer.vip_id = None
        db.session.add(obj_customer)
        db.session.flush()
        db.session.query(Vipdetail).filter(Vipdetail.vip_id == vip_id).delete()
        db.session.delete(obj_vip)
        db.session.commit()
        flash(u'会员卡注销成功', 'ok')
        return redirect(url_for('home.customer_list'))

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
    # 采购单明细查看
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
            reason=u'修改结款,采购单:%s' % porder.id
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
        db.session.flush()  # 提交一下获取id,不要使用commit
        if switch == 1:#结算
            # 删除所有明细
            # for iter_del in podetails:
            #     db.session.delete(iter_del)
            # 更改删除方式直接找到全部删除
            db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
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
            # for iter_del in podetails:
            #     db.session.delete(iter_del)
            # 更改删除方式直接找到全部删除
            db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
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
    if porder.type != 0 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_buy_list'))
    Podetail.query.filter_by(porder_id=id).delete()
    db.session.delete(porder)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除采购单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'采购单删除成功', 'ok')
    return redirect(url_for('home.stock_buy_list'))

@home.route('/modal/stock', methods=['GET'])
def modal_stock():
    # 获取库存弹出框数据
    key = request.args.get('key', '')
    stocks = Stock.query.join(Item)
    # 条件查询
    if key:
        # 库房/零件名称/类别/规格
        stocks = stocks.filter(
            or_(Stock.store.ilike('%' + key + '%'),
                Item.name.ilike('%' + key + '%'),
                Item.cate.ilike('%' + key + '%'),
                Item.standard.ilike('%' + key + '%'),
                )
        )
    stocks = stocks.order_by(Stock.item_id.asc(), Stock.store.asc()).limit(current_app.config['POSTS_PER_PAGE']).all()
    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for v in stocks:
        data.append(
            {
                "id": v.id,
                "item_id": v.item.id,
                "item_name": v.item.name,
                "item_standard": v.item.standard,
                "item_unit": v.item.unit,
                "item_costprice": v.item.costprice,
                "costprice": v.costprice,
                "store": v.store,
                "qty": v.qty,
                "cate": v.item.cate,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/stock/out/list', methods=['GET'])
def stock_out_list():
    # 领料单列表
    key = request.args.get('key', '')
    # 出库单状态 true 临时;false 全部
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

    podetails = db.session.query(Podetail, Stock).filter(
        Podetail.porder_id == id,
        Podetail.item_id == Stock.item_id,
        Podetail.nstore == Stock.store,
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
    if form.validate_on_submit():
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
        # 添加主表
        if not porder:  # 没有新增一个
            porder = Porder(
                type=1,
                user_id=int(session['user_id']),
                status=0,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.status = 0
            porder.remarks = form.remarks.data
        db.session.add(porder)
        # 主表暂存，需要使用id
        db.session.flush()

        # 删除所有明细
        # for iter_del in podetails:
        #     db.session.delete(iter_del)
        # 更改删除方式直接找到全部删除
        db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
        for iter_add in form.inputrows:
            # 新增明细
            podetail = Podetail(
                porder_id=porder.id,
                item_id=iter_add.item_id.data,
                nstore=iter_add.store.data,
                qty=float(iter_add.qty.data), # 这里一定要强转，临时数据后面要比较
            )
            db.session.add(podetail)
        # 把所有明细暂存，后面用于计算是否存在核减为负数的情况
        db.session.flush()

        if switch == 1:# 结算
            # valid True可以提交; False 不能提交
            valid = True
            # 合并所有item_id,store相同的，总数不能比库存数量大
            sql_text = 'select b.item_id, d.name as item_name, b.nstore, b.sum_qty, c.qty from ' \
                       '(select a.item_id, nstore, sum(qty) as sum_qty from tb_podetail as a ' \
                       'where a.porder_id = :id group by item_id, nstore) as b, tb_stock as c, tb_item as d ' \
                       'where b.item_id = c.item_id and b.nstore = c.store and b.item_id = d.id'
            grouplists = db.session.execute(text(sql_text), {'id' : porder.id})
            for iter in grouplists:
                if iter.qty < iter.sum_qty:
                    flash(u'零件:' + iter.item_name + u',出库后数量小于0', 'err')
                    valid = False

            # 校验通过
            if valid:
                # 遍历临时数据
                checklists = db.session.query(Podetail, Stock).filter(
                    Podetail.porder_id == porder.id,
                    Podetail.item_id == Stock.item_id,
                    Podetail.nstore == Stock.store,
                ).order_by(Podetail.id.asc()).all()
                # 减少库存数量
                for iter in checklists:
                    iter.Stock.qty -= iter.Podetail.qty
                porder.status = 1 # 设置为发布状态
                db.session.add(porder)
                # 记录出库日志
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'结算出库单:%s' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                flash(u'出库单结算成功', 'ok')
                return redirect(url_for('home.stock_out_list'))
            # 校验不通过,暂存
            else:
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                     reason=u'结算出库单:%s失败' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                return redirect(url_for('home.stock_out_edit', id=porder.id))

        else: # 暂存
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存出库单:%s' % porder.id
            )
            db.session.commit()
            flash(u'出库单暂存成功', 'ok')
            return redirect(url_for('home.stock_out_list'))

    return render_template('home/stock_out_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/out/del/<int:id>', methods=['GET'])
def stock_out_del(id=None):
    # 出库单删除
    porder = Porder.query.filter_by(id=id).first_or_404()
    if porder.type != 1 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_out_list'))
    Podetail.query.filter_by(porder_id=id).delete()
    db.session.delete(porder)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除出库单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'出库单删除成功', 'ok')
    return redirect(url_for('home.stock_out_list'))

@home.route('/stock/out/view/<int:id>', methods=['GET'])
def stock_out_view(id=None):
    # 出库单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_out_view.html', porder=porder, podetails=podetails)

@home.route('/stock/allot/list', methods=['GET'])
def stock_allot_list():
    # 调拨单列表
    key = request.args.get('key', '')
    # 调拨单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Porder.query.filter_by(type=2)
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
    return render_template('home/stock_allot_list.html', pagination=pagination, key=key, status=status)

@home.route('/stock/allot/edit/<int:id>', methods=['GET', 'POST'])
def stock_allot_edit(id=None):
    # 调拨单
    form = StockAllotForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 2:
            return redirect(url_for('home.stock_allot_edit'))

    podetails = db.session.query(Podetail, Stock).filter(
        Podetail.porder_id == id,
        Podetail.item_id == Stock.item_id,
        Podetail.ostore == Stock.store,
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
                listform = StockAllotListForm()
                listform.item_id = detail.Podetail.item_id
                listform.item_name = detail.Podetail.item.name
                listform.item_standard = detail.Podetail.item.standard
                listform.item_unit = detail.Podetail.item.unit
                listform.item_costprice = detail.Podetail.item.costprice
                # listform.stock_costprice = detail.Stock.costprice # 库存中最后一次采购价
                listform.ostore = detail.Podetail.ostore # 来源仓库
                listform.nstore = detail.Podetail.nstore # 目标仓库
                listform.stock_qty = detail.Stock.qty
                listform.qty = detail.Podetail.qty
                form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    if form.validate_on_submit():
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
        # 添加主表
        if not porder:  # 没有新增一个
            porder = Porder(
                type=2,
                user_id=int(session['user_id']),
                status=0,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.status = 0
            porder.remarks = form.remarks.data
        db.session.add(porder)
        # 主表暂存，需要使用id
        db.session.flush()

        # 删除所有明细
        # for iter_del in podetails:
        #     db.session.delete(iter_del)
        # 更改删除方式直接找到全部删除
        db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
        for iter_add in form.inputrows:
            # 新增明细
            podetail = Podetail(
                porder_id=porder.id,
                item_id=iter_add.item_id.data,
                ostore=iter_add.ostore.data,
                nstore=iter_add.nstore.data,
                qty=float(iter_add.qty.data), # 这里一定要强转，临时数据后面要比较
            )
            db.session.add(podetail)
        # 把所有明细暂存，后面用于计算是否存在核减为负数的情况
        db.session.flush()

        if switch == 1:# 结算
            # valid True可以提交; False 不能提交
            valid = True
            # 判断临时数据中有无调拨数量大于库存的
            sql_text = 'select b.item_id, d.name as item_name, b.ostore, b.sum_qty, c.qty from ' \
                       '(select a.item_id, ostore, sum(qty) as sum_qty from tb_podetail as a ' \
                       'where a.porder_id = :id group by item_id, ostore) as b, tb_stock as c, tb_item as d ' \
                       'where b.item_id = c.item_id and b.ostore = c.store and b.item_id = d.id'
            grouplists = db.session.execute(text(sql_text), {'id': porder.id})
            for iter in grouplists:
                if iter.qty < iter.sum_qty:
                    flash(u'零件:' + iter.item_name + u',调拨后数量小于0', 'err')
                    valid = False

            # 校验通过
            if valid:
                # 遍历临时数据
                checklists = db.session.query(Podetail, Stock).filter(
                    Podetail.porder_id == porder.id,
                    Podetail.item_id == Stock.item_id,
                    Podetail.ostore == Stock.store,
                ).order_by(Podetail.id.asc()).all()
                for iter in checklists:
                    # 减少原库存数量
                    iter.Stock.qty -= iter.Podetail.qty
                    # 增加新库存数量
                    # 判断库存是否存在
                    stock = Stock.query.filter_by(item_id=iter.Podetail.item_id,
                                                  store=iter.Podetail.nstore).first()
                    if stock:  # 存在就更新数量
                        stock.qty += float(iter.Podetail.qty)
                    else:  # 不存在库存表加一条
                        stock = Stock(
                            item_id=iter.Podetail.item_id,
                            costprice=iter.Stock.costprice,
                            qty=iter.Podetail.qty,
                            store=iter.Podetail.nstore,
                        )
                    db.session.add(iter.Stock)
                    db.session.add(stock)

                porder.status = 1 # 设置为发布状态
                db.session.add(porder)
                # 记录出库日志
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'结算调拨单:%s' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                flash(u'调拨单结算成功', 'ok')
                return redirect(url_for('home.stock_allot_list'))
            # 校验不通过,暂存
            else:
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                     reason=u'结算调拨单:%s失败' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                return redirect(url_for('home.stock_allot_edit', id=porder.id))

        else: # 暂存
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存调拨单:%s' % porder.id
            )
            db.session.commit()
            flash(u'调拨单暂存成功', 'ok')
            return redirect(url_for('home.stock_allot_list'))

    return render_template('home/stock_allot_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/allot/del/<int:id>', methods=['GET'])
def stock_allot_del(id=None):
    # 调拨单删除
    porder = Porder.query.filter_by(id=id).first_or_404()
    if porder.type != 2 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_allot_list'))
    Podetail.query.filter_by(porder_id=id).delete()
    db.session.delete(porder)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除调拨单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'调拨单删除成功', 'ok')
    return redirect(url_for('home.stock_allot_list'))

@home.route('/stock/allot/view/<int:id>', methods=['GET'])
def stock_allot_view(id=None):
    # 调拨单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_allot_view.html', porder=porder, podetails=podetails)

@home.route('/stock/loss/list', methods=['GET'])
def stock_loss_list():
    # 报损单列表
    key = request.args.get('key', '')
    # 报损单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Porder.query.filter_by(type=3)
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
    return render_template('home/stock_loss_list.html', pagination=pagination, key=key, status=status)

@home.route('/stock/loss/edit/<int:id>', methods=['GET', 'POST'])
def stock_loss_edit(id=None):
    # 报损单
    form = StockLossForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 3:
            return redirect(url_for('home.stock_allot_edit'))

    podetails = db.session.query(Podetail, Stock).filter(
        Podetail.porder_id == id,
        Podetail.item_id == Stock.item_id,
        Podetail.ostore == Stock.store,
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
                listform = StockLossListForm()
                listform.item_id = detail.Podetail.item_id
                listform.item_name = detail.Podetail.item.name
                listform.item_standard = detail.Podetail.item.standard
                listform.item_unit = detail.Podetail.item.unit
                listform.item_costprice = detail.Podetail.item.costprice
                # listform.stock_costprice = detail.Stock.costprice # 库存中最后一次采购价
                listform.ostore = detail.Podetail.ostore
                listform.stock_qty = detail.Stock.qty
                listform.qty = detail.Podetail.qty
                form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    if form.validate_on_submit():
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
        # 添加主表
        if not porder:  # 没有新增一个
            porder = Porder(
                type=3,
                user_id=int(session['user_id']),
                status=0,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.status = 0
            porder.remarks = form.remarks.data
        db.session.add(porder)
        # 主表暂存，需要使用id
        db.session.flush()

        # 删除所有明细
        # for iter_del in podetails:
        #     db.session.delete(iter_del)
        # 更改删除方式直接找到全部删除
        db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
        for iter_add in form.inputrows:
            # 新增明细
            podetail = Podetail(
                porder_id=porder.id,
                item_id=iter_add.item_id.data,
                ostore=iter_add.ostore.data,
                qty=float(iter_add.qty.data), # 这里一定要强转，临时数据后面要比较
            )
            db.session.add(podetail)
        # 把所有明细暂存，后面用于计算是否存在核减为负数的情况
        db.session.flush()

        if switch == 1:# 结算
            # valid True可以提交; False 不能提交
            valid = True
            # 判断临时数据中有无报损数量大于库存的
            sql_text = 'select b.item_id, d.name as item_name, b.ostore, b.sum_qty, c.qty from ' \
                       '(select a.item_id, ostore, sum(qty) as sum_qty from tb_podetail as a ' \
                       'where a.porder_id = :id group by item_id, ostore) as b, tb_stock as c, tb_item as d ' \
                       'where b.item_id = c.item_id and b.ostore = c.store and b.item_id = d.id'
            grouplists = db.session.execute(text(sql_text), {'id': porder.id})
            for iter in grouplists:
                if iter.qty < iter.sum_qty:
                    flash(u'零件:' + iter.item_name + u',报损后数量小于0', 'err')
                    valid = False

            # 校验通过
            if valid:
                # 遍历临时数据
                checklists = db.session.query(Podetail, Stock).filter(
                    Podetail.porder_id == porder.id,
                    Podetail.item_id == Stock.item_id,
                    Podetail.ostore == Stock.store,
                ).order_by(Podetail.id.asc()).all()
                for iter in checklists:
                    # 减少原库存数量
                    iter.Stock.qty -= iter.Podetail.qty
                    db.session.add(iter.Stock)

                porder.status = 1 # 设置为发布状态
                db.session.add(porder)
                # 记录出库日志
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'结算报损单:%s' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                flash(u'报损单结算成功', 'ok')
                return redirect(url_for('home.stock_loss_list'))
            # 校验不通过,暂存
            else:
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                     reason=u'结算报损单:%s失败' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                return redirect(url_for('home.stock_loss_edit', id=porder.id))

        else: # 暂存
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存报损单:%s' % porder.id
            )
            db.session.commit()
            flash(u'报损单暂存成功', 'ok')
            return redirect(url_for('home.stock_loss_list'))

    return render_template('home/stock_loss_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/loss/del/<int:id>', methods=['GET'])
def stock_loss_del(id=None):
    # 报损单删除
    porder = Porder.query.filter_by(id=id).first_or_404()
    if porder.type != 3 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_loss_list'))
    Podetail.query.filter_by(porder_id=id).delete()
    db.session.delete(porder)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除报损单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'报损单删除成功', 'ok')
    return redirect(url_for('home.stock_loss_list'))

@home.route('/stock/loss/view/<int:id>', methods=['GET'])
def stock_loss_view(id=None):
    # 报损单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_loss_view.html', porder=porder, podetails=podetails)

@home.route('/stock/return/list', methods=['GET'])
def stock_return_list():
    # 退货单列表
    key = request.args.get('key', '')
    # 退货单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    # 是否欠款 true 欠;false 否
    debt = request.args.get('debt', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Porder.query.filter_by(type=4)
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
    return render_template('home/stock_return_list.html', pagination=pagination, key=key, status=status, debt=debt)

@home.route('/stock/return/edit/<int:id>', methods=['GET', 'POST'])
def stock_return_edit(id=None):
    # 退货单
    form = StockReturnForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 4:
            return redirect(url_for('home.stock_return_list'))
    podetails = db.session.query(Podetail, Stock).filter(
        Podetail.porder_id == id,
        Podetail.item_id == Stock.item_id,
        Podetail.ostore == Stock.store,
    ).order_by(Podetail.id.asc()).all()
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
                listform = StockReturnListForm()
                listform.item_id = detail.Podetail.item_id
                listform.item_name = detail.Podetail.item.name
                listform.item_standard = detail.Podetail.item.standard
                listform.item_unit = detail.Podetail.item.unit
                listform.costprice = detail.Podetail.item.costprice
                listform.ostore = detail.Podetail.ostore
                listform.stock_qty = detail.Stock.qty
                listform.qty = detail.Podetail.qty
                listform.rowamount = detail.Podetail.rowamount
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
                type=4,
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
        db.session.flush()  # 提交一下获取id,不要使用commit

        # 更改删除方式直接找到全部删除
        db.session.query(Podetail).filter(Podetail.porder_id == porder.id).delete()
        for iter_add in form.inputrows:
            # 新增明细
            podetail = Podetail(
                porder_id=porder.id,
                item_id=iter_add.item_id.data,
                ostore=iter_add.ostore.data,
                qty=float(iter_add.qty.data),  # 这里一定要强转，临时数据后面要比较
                costprice=iter_add.costprice.data,
                rowamount=iter_add.rowamount.data,
            )
            db.session.add(podetail)
        # 把所有明细暂存，后面用于计算是否存在核减为负数的情况
        db.session.flush()

        if switch == 1:#结算
            # valid True可以提交; False 不能提交
            valid = True
            # 判断临时数据中有无报损数量大于库存的
            sql_text = 'select b.item_id, d.name as item_name, b.ostore, b.sum_qty, c.qty from ' \
                       '(select a.item_id, ostore, sum(qty) as sum_qty from tb_podetail as a ' \
                       'where a.porder_id = :id group by item_id, ostore) as b, tb_stock as c, tb_item as d ' \
                       'where b.item_id = c.item_id and b.ostore = c.store and b.item_id = d.id'
            grouplists = db.session.execute(text(sql_text), {'id': porder.id})
            for iter in grouplists:
                if iter.qty < iter.sum_qty:
                    flash(u'零件:' + iter.item_name + u',退货后数量小于0', 'err')
                    valid = False
            # 校验通过
            if valid:
                # 遍历临时数据
                checklists = db.session.query(Podetail, Stock).filter(
                    Podetail.porder_id == porder.id,
                    Podetail.item_id == Stock.item_id,
                    Podetail.ostore == Stock.store,
                ).order_by(Podetail.id.asc()).all()
                for iter in checklists:
                    # 减少原库存数量
                    iter.Stock.qty -= iter.Podetail.qty
                    db.session.add(iter.Stock)

                porder.status = 1  # 设置为发布状态
                db.session.add(porder)
                # 记录出库日志
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'结算退货单:%s' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                flash(u'退货单结算成功', 'ok')
                return redirect(url_for('home.stock_return_list'))
            else:# 校验不通过,暂存
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'结算退货单:%s失败' % porder.id
                )
                db.session.add(oplog)
                db.session.commit()
                return redirect(url_for('home.stock_return_edit', id=porder.id))
        else:# 暂存
            oplog = Oplog(
                user_id=session['user_id'],
                ip=request.remote_addr,
                reason=u'暂存退货单:%s' % porder.id
            )
            db.session.commit()
            flash(u'退货单暂存成功', 'ok')
            return redirect(url_for('home.stock_return_list'))

    return render_template('home/stock_return_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/return/del/<int:id>', methods=['GET'])
def stock_return_del(id=None):
    # 退货单删除
    porder = Porder.query.filter_by(id=id).first_or_404()
    if porder.type != 4 or porder.user_id != int(session['user_id']) or porder.status == 1:
        return redirect(url_for('home.stock_return_list'))
    Podetail.query.filter_by(porder_id=id).delete()
    db.session.delete(porder)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除退货单:%s' % porder.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'退货单删除成功', 'ok')
    return redirect(url_for('home.stock_return_list'))

@home.route('/stock/return/view/<int:id>', methods=['GET'])
def stock_return_view(id=None):
    # 退货单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_return_view.html', porder=porder, podetails=podetails)

@home.route('/stock/return/debt/<int:id>', methods=['GET', 'POST'])
def stock_return_debt(id=None):
    # 退货单结款
    form = StockReturnDebtForm()
    porder = Porder.query.filter_by(id=id).first_or_404()
    # 如果表单不属于用户，不是发布状态 退出
    if porder.user_id != int(session['user_id']) or porder.status == 0 or porder.type != 4:
        return redirect(url_for('home.stock_return_list'))
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
            reason=u'修改结款,退货单号:%s' % porder.id
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'结款修改成功', 'ok')
        return redirect(url_for('home.stock_return_list'))
    return render_template('home/stock_return_debt.html', form=form, porder=porder)


# 20181008 liuqq 客户-会员卡充值
@home.route('/customer/cus_vip_deposit/<int:vip_id>', methods=['GET', 'POST'])
def cus_vip_deposit(vip_id=None):
    form = CusVipDepositForm()
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    if form.validate_on_submit():
        if form.deposit.data != form.re_deposit.data:
            flash(u'充值金额与确认充值金额不一致！', 'err')
            return render_template('home/cus_vip_deposit.html', obj_vip=obj_vip, form=form)

        obj_vip.balance = float(form.sum_deposit.data)
        obj_oplog_vip = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'充值vip卡:%s 金额:%s' % (obj_vip.id, form.deposit.data)
        )
        # 数据提交
        objects = [obj_vip, obj_oplog_vip]
        db.session.add_all(objects)
        db.session.flush()

        # 保存vip明细内容
        add_time = datetime.now()
        for iter_add in form.inputrows:
            interval_day = int(iter_add.interval.data) * 30  # 卡的有效期*30天
            obj_vip_detail = Vipdetail(
                vip_id=obj_vip.id,  # 客户会员卡号
                item_id=iter_add.item_id.data,  # 服务/项目id
                discountprice=iter_add.discountprice.data,  # 优惠后销售价
                quantity=iter_add.quantity.data,  # 使用次数
                addtime=add_time,  # 优惠开始时间
                endtime=add_time + timedelta(days=interval_day)  # 优惠结束时间 = 优惠开始时间 + 有效期
            )
            db.session.add(obj_vip_detail)
        db.session.commit()

        flash(u'充值成功', 'ok')
        return redirect(url_for('home.customer_list'))
    return render_template('home/cus_vip_deposit.html', obj_vip=obj_vip, form=form)