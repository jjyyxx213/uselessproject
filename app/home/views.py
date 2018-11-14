# -*- coding:utf-8 -*-
from . import home
from flask import render_template, session, redirect, request, url_for, flash, current_app
from forms import LoginForm, PwdForm, CustomerForm, CusVipForm, CusVipDepositForm, StockBuyForm, StockBuyListForm, StockBuyDebtForm, \
    StockOutListForm, StockOutForm, StockAllotListForm, StockAllotForm, StockLossListForm, StockLossForm, StockReturnListForm, \
    StockReturnForm, StockReturnDebtForm, OrderListForm, OrderForm, OrderDebtForm, SalesAdvancedForm, IndexForm, VipsAdvancedForm
from app.models import User, Userlog, Oplog, Item, Supplier, Customer, Stock, Porder, Podetail, Kvp, Mscard, Msdetail, Vip, Vipdetail, Order, Odetail, Billing
from app import db
from app.decorators import permission_required, login_required
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_, func, text
from json import dumps
from datetime import datetime, timedelta, date
import os, random, uuid, collections, hashlib

def change_filename(filename):
    # 修改文件名称
    fileinfo = os.path.splitext(filename)
    filename = datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename

@home.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home/index.html')

@home.route('/summary/report', methods=['GET', 'POST'])
@login_required
@permission_required
def summary_report():
    form = IndexForm()
    # 收入总额
    sum_payment = '0'
    # 会员数量
    vip_count = '0'
    # 散客数量
    nvip_count = '0'
    # 销售金额
    sum_order = '0'
    # 会员充值金额
    sum_recharge = '0'
    # 客户办卡金额
    sum_vip = '0'
    # 销售金额比例
    per_order = '0%'
    # 办卡金额比例
    per_vip = '0%'
    # 充值金额比例
    per_recharge = '0%'
    ###################
    # 现金支付
    type_cash = '0'
    per_cash = '0%'
    # 银行卡支付
    type_card = '0'
    per_card = '0%'
    # 支付宝
    type_ali = '0'
    per_ali = '0%'
    # 微信
    type_wechat = '0'
    per_wechat = '0%'
    # 其他
    type_other = '0'
    per_other = '0%'
    if request.method == 'GET':
        # 本月第一天
        form.date_from.data = date(date.today().year,date.today().month,1)
        form.date_to.data = date.today()
    if form.validate_on_submit():
        date_from = datetime.strptime(form.date_from.data, '%Y-%m-%d')
        date_to = datetime.strptime(form.date_to.data, '%Y-%m-%d') + timedelta(days=1)
        # 获取会员数量
        sql_text = 'select count(id) as vip_count from tb_customer c where exists ( ' \
                   'select o.id from tb_order o where o.customer_id = c.id and o.type = 0 ' \
                   'and o.status = 1 and addtime >= \'%s\' and addtime < \'%s\' ' \
                   ') and c.vip_id is not null' % (date_from, date_to)
        sql_result = db.session.execute(text(sql_text))
        for iter in sql_result:
            vip_count = iter.vip_count
        # 获取散客数量
        sql_text = 'select count(id) as nvip_count from tb_customer c where exists ( ' \
                   'select o.id from tb_order o where o.customer_id = c.id and o.type = 0 ' \
                   'and o.status = 1 and addtime >= \'%s\' and addtime < \'%s\' ' \
                   ') and c.vip_id is null' % (date_from, date_to)
        sql_result = db.session.execute(text(sql_text))
        for iter in sql_result:
            nvip_count = iter.nvip_count
        # 销售金额
        sql_text = 'select sum(o.payment) as sum_order_payment from tb_order o where o.type = 0 and o.status = 1  ' \
                   'and o.addtime >= \'%s\' and o.addtime < \'%s\' ' % (date_from, date_to)
        sql_result = db.session.execute(text(sql_text))
        for iter in sql_result:
            if iter.sum_order_payment:
                sum_order = iter.sum_order_payment
        # 办卡充值金额
        sql_text = 'select paytype, sum(payment) as sum_vip_payment from tb_billing b where b.vip_id is not null ' \
                   'and b.addtime >= \'%s\' and b.addtime < \'%s\' group by paytype' % (date_from, date_to)
        sql_result = db.session.execute(text(sql_text))
        for iter in sql_result:
            if iter.paytype == u'会员充值':
                sum_recharge = iter.sum_vip_payment
            elif iter.paytype == u'客户办卡':
                sum_vip = iter.sum_vip_payment
        # 实收金额 = 销售金额 + 办卡/充值金额
        sum_payment = float(sum_order) + float(sum_recharge) + float(sum_vip)
        # 销售金额比例/办卡金额比例/充值金额比例
        if float(sum_payment) != 0:
            per_order = format(float(sum_order) / float(sum_payment), '.0%')
            per_vip = format(float(sum_vip) / float(sum_payment), '.0%')
            per_recharge = format(float(sum_recharge) / float(sum_payment), '.0%')

        # 获取结算方式
        sql_text = 'select paywith, sum(payment) as sum_payment from ( select o.payment, o.paywith, o.addtime from tb_order o where o.type = 0 and o.status = 1 ' \
                   'union all select b.payment, b.paywith, b.addtime from tb_billing b where b.vip_id is not null) t where ' \
                   't.addtime >= \'%s\' and t.addtime < \'%s\' group by paywith ' % (date_from, date_to)
        sql_result = db.session.execute(text(sql_text))
        for iter in sql_result:
            if iter.paywith == u'现金':
                type_cash = iter.sum_payment
                per_cash = format(float(type_cash) / float(sum_payment), '.0%')
            elif iter.paywith == u'银行卡':
                type_card = iter.sum_payment
                per_card = format(float(type_card) / float(sum_payment), '.0%')
            elif iter.paywith == u'支付宝':
                type_ali = iter.sum_payment
                per_ali = format(float(type_ali) / float(sum_payment), '.0%')
            elif iter.paywith == u'微信':
                type_wechat = iter.sum_payment
                per_wechat = format(float(type_wechat) / float(sum_payment), '.0%')
            elif iter.paywith == u'其他':
                type_other = iter.sum_payment
                per_other = format(float(type_other) / float(sum_payment), '.0%')

    context = {
        'sum_payment': sum_payment,
        'vip_count': vip_count,
        'nvip_count': nvip_count,
        'sum_order': sum_order,
        'sum_recharge': sum_recharge,
        'sum_vip': sum_vip,
        'per_order': per_order,
        'per_recharge': per_recharge,
        'per_vip': per_vip,
        'type_cash': type_cash,
        'per_cash': per_cash,
        'type_card': type_card,
        'per_card': per_card,
        'type_ali': type_ali,
        'per_ali': per_ali,
        'type_wechat': type_wechat,
        'per_wechat': per_wechat,
        'type_other': type_other,
        'per_other': per_other,
    }
    return render_template("home/summary_report.html", form=form, **context)

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
    session.pop('is_admin', None)
    return redirect(url_for('home.login'))

# 20180913 liuqq 修改密码
@home.route('/user/pwd', methods=['GET', 'POST'])
@login_required
def pwd():
    form = PwdForm()
    is_flag = True
    if form.validate_on_submit():
        # 验证密码
        user = User.query.filter_by(id=session.get('user_id')).first()
        if user.verify_password(form.old_pwd.data) != 1:
            is_flag = False
            flash(u'旧密码输入错误', 'err')
        if form.new_pwd.data != form.re_pwd.data:
            is_flag = False
            flash(u'您两次输入的密码不一致!', 'err')
        if form.new_pwd.data == form.old_pwd.data:
            is_flag = False
            flash(u'新密码与旧密码一致！', 'err')
        if is_flag == False:
            return render_template('home/pwd.html', form=form)
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
@login_required
@permission_required
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
@login_required
@permission_required
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
@login_required
@permission_required
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
@login_required
@permission_required
def customer_add():
    form = CustomerForm()
    is_flag = True
    if form.validate_on_submit():
        province = request.form.get('province')
        pnumber = province + form.pnumber.data
        if Customer.query.filter_by(pnumber=pnumber).first():
            is_flag = False
            flash(u'您输入的车牌号已存在', 'err')
        if Customer.query.filter_by(phone=form.phone.data).first():
            is_flag = False
            flash(u'您输入的手机号已存在', 'err')
        if is_flag == False:
            return render_template('home/customer_add.html', form=form)
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
@login_required
@permission_required
def customer_edit(id=None):
    # 修改客户
    form = CustomerForm()
    form.submit.label.text = u'修改'
    obj_customer = Customer.query.filter_by(id=id).first_or_404()
    is_flag = True
    if request.method == 'GET':
        province = obj_customer.pnumber[0:1]
        form.name.data = obj_customer.name
        form.name_wechat.data = obj_customer.name_wechat
        form.sex.data = int(obj_customer.sex)
        form.phone.data = obj_customer.phone
        form.pnumber.data = obj_customer.pnumber[1:]
        form.vin.data = obj_customer.vin
        form.brand.data = obj_customer.brand
        form.email.data = obj_customer.email
        form.id_card.data = obj_customer.id_card
        form.user_id.data = obj_customer.user_id

    if form.validate_on_submit():
        province = request.form.get('province')
        pnumber = province + form.pnumber.data
        if obj_customer.pnumber != pnumber and Customer.query.filter_by(pnumber=pnumber).first():
            is_flag = False
            flash(u'您输入的车牌号已存在', 'err')
        if obj_customer.phone != form.phone.data and Customer.query.filter_by(phone=form.phone.data).first():
            is_flag = False
            flash(u'您输入的手机号已存在', 'err')
        if is_flag == False:
            return render_template('home/customer_edit.html', form=form, province=province)

        obj_customer.name = form.name.data,
        obj_customer.name_wechat = form.name_wechat.data,
        obj_customer.sex = int(form.sex.data),
        obj_customer.phone = form.phone.data,
        obj_customer.pnumber = pnumber,
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
    return render_template('home/customer_edit.html', form=form, province=province)

# 20180920 liuqq 新增客户-会员卡
@home.route('/customer/cus_vip_add/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required
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
            # balance=form.payment.data,  # 余额
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
        obj_customer.balance = form.payment.data #20181024 余额记录在客户表中
        obj_oplog_cus = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'添加客户与vip卡关系及明细:%s' % max_vip_id
        )
        # 20181024 liuqq 客户消费流水
        obj_billing = Billing(
            cust_id=obj_customer.id,  # 客户id
            paywith=form.paywith.data,  # 支付方式
            vip_id=max_vip_id, # 会员卡号
            amount=form.payment.data,  # 应付金额
            payment=form.payment.data,  # 支付金额
            paytype=u'客户办卡'
        )
        objects = [obj_customer, obj_oplog_cus, obj_billing]
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
@login_required
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
@login_required
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
@login_required
@permission_required
def cus_vip_list(vip_id=None):
    # 明细查看
    obj_customer = Customer.query.filter_by(vip_id=vip_id).first()
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    obj_vip_details = Vipdetail.query.filter_by(vip_id=vip_id).order_by(Vipdetail.id.asc()).all()
    if request.method == 'GET':
        return render_template('home/cus_vip_list.html', obj_vip=obj_vip, obj_vip_details=obj_vip_details)
    if request.method == 'POST':
        obj_customer.vip_id = None
        obj_customer.balance = 0  # 20181024 余额清空
        obj_customer.score = 0  # 20181024 积分清空
        db.session.add(obj_customer)
        db.session.flush()
        db.session.query(Vipdetail).filter(Vipdetail.vip_id == vip_id).delete()
        db.session.query(Billing).filter(Billing.vip_id == vip_id).delete() #20181024 删除消费流水
        db.session.delete(obj_vip)
        # 20181024 记录日志
        obj_oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'注销客户会员卡:%s' % obj_customer.name
        )
        db.session.add(obj_oplog)
        db.session.commit()
        flash(u'会员卡注销成功', 'ok')
        return redirect(url_for('home.customer_list'))

# 20181008 liuqq 客户-会员卡充值
@home.route('/customer/cus_vip_deposit/<int:vip_id>', methods=['GET', 'POST'])
@login_required
@permission_required
def cus_vip_deposit(vip_id=None):
    form = CusVipDepositForm()
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    obj_customer = Customer.query.filter_by(vip_id=vip_id).first()
    if form.validate_on_submit():
        if form.deposit.data != form.re_deposit.data:
            flash(u'充值金额与确认充值金额不一致！', 'err')
            return render_template('home/cus_vip_deposit.html', obj_vip=obj_vip, form=form)

        obj_customer.balance = float(form.sum_deposit.data)
        obj_oplog_vip = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'充值vip卡:%s 会员:%s 金额:%s' % (obj_vip.id,obj_customer.name, form.deposit.data)
        )

        # 20181024 liuqq 客户消费流水
        obj_billing = Billing(
            cust_id=obj_customer.id,  # 客户id
            paywith=form.paywith.data,  # 支付方式
            vip_id=obj_vip.id, # 会员卡号
            amount=float(form.re_deposit.data),  # 应付金额
            payment=float(form.re_deposit.data),  # 支付金额
            paytype=u'会员充值'
        )

        # 数据提交
        objects = [obj_customer, obj_oplog_vip, obj_billing]
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


# 20181025 会员卡升级
@home.route('/customer/cus_vip_update/<int:vip_id>', methods=['GET', 'POST'])
@login_required
@permission_required
def cus_vip_update(vip_id=None):
    form = CusVipForm()
    # 明细查看
    obj_customer = Customer.query.filter_by(vip_id=vip_id).first()
    obj_vip = Vip.query.filter_by(id=vip_id).first()
    obj_vip_details = Vipdetail.query.filter_by(vip_id=vip_id).order_by(Vipdetail.id.asc()).all()
    if request.method == 'POST':
        # 计算截止日期
        interval_day = int(form.interval.data) * 30  # 卡的有效期*30天
        add_time = datetime.now()
        end_time = add_time + timedelta(days=interval_day)

        # 计算引用vip卡的名称
        obj_mscard = Mscard.query.filter_by(id=form.name.data).first()
        # 修改VIP主表对象
        obj_vip.name = obj_mscard.name
        obj_vip.scorerule = form.scorerule.data # 积分规则
        obj_vip.scorelimit = form.scorelimit.data # 积分限制提醒
        obj_vip.addtime = add_time # 办理时间
        obj_vip.endtime = end_time # 截止时间 = 办理时间 + 有效期

        obj_oplog_vip = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'升级客户:%s的vip卡:%s' % (obj_customer.name, vip_id)
        )
        # 数据提交
        objects = [obj_vip, obj_oplog_vip]
        db.session.add_all(objects)

        # 客户积分清零
        obj_customer.score = 0
        obj_oplog_cus = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'客户:%s会员卡:%s升级积分清零' % (obj_customer.name, vip_id)
        )
        objects = [obj_customer, obj_oplog_cus]
        db.session.add_all(objects)

        # 保存vip明细内容
        meal = form.meal.data
        # 若是保留原套餐
        if meal == 0:
            db.session.query(Vipdetail).filter(Vipdetail.vip_id == vip_id).delete()
            for iter_add in form.inputrows:
                interval_day = int(iter_add.interval.data) * 30  # 卡的有效期*30天
                obj_vip_detail = Vipdetail(
                    vip_id=vip_id,  # 客户会员卡号
                    item_id=iter_add.item_id.data,  # 服务/项目id
                    discountprice=iter_add.discountprice.data,  # 优惠后销售价
                    quantity=iter_add.quantity.data,  # 使用次数
                    addtime=add_time,  # 优惠开始时间
                    endtime=add_time + timedelta(days=interval_day)  # 优惠结束时间 = 优惠开始时间 + 有效期
                )
                db.session.add(obj_vip_detail)

        db.session.commit()
        flash(u'客户-会员卡升级成功', 'ok')
        return redirect(url_for('home.customer_list'))
    if request.method == 'GET':
        return render_template('home/cus_vip_update.html', obj_vip=obj_vip, obj_vip_details=obj_vip_details, form=form)


@home.route('/modal/customer', methods=['GET'])
@login_required
def modal_customer():
    # 获取客户弹出框数据
    key = request.args.get('key', '')
    customers = Customer.query.outerjoin(
        Vip, Customer.vip_id == Vip.id
    )
    # 条件查询
    if key:
        # 姓名/手机/车牌/邮箱
        customers = customers.filter(
            or_(Customer.name.ilike('%' + key + '%'),
                Customer.phone.ilike('%' + key + '%'),
                Customer.pnumber.ilike('%' + key + '%'),
                Customer.email.ilike('%' + key + '%'),
                )
        )
    customers = customers.order_by(Customer.name.asc()).limit(current_app.config['POSTS_PER_PAGE']).all()
    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for v in customers:
        vip_id = ''
        vip_name = ''
        if v.vip:
            vip_id = v.vip_id
            vip_name = v.vip.name
        data.append(
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "pnumber": v.pnumber,
                "brand": v.brand,
                "email": v.email,
                "freq": v.freq,
                "summary": v.freq,
                "vip_id": vip_id,
                "vip_name": vip_name,
                "balance": v.balance,
                "score": v.score,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/modal/item', methods=['GET'])
@login_required
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

@home.route('/modal/service', methods=['GET'])
@login_required
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

@home.route('/order/modal/service', methods=['GET'])
@login_required
def order_modal_service():
    # 获取服务弹出框数据
    key = request.args.get('key', '')
    vip_id = request.args.get('vip_id', '')
    sql_text = "select a.id, a.name, a.cate, a.type, a.salesprice, a.rewardprice, a.costprice, a.unit, a.standard, a.valid, " \
               "b.id as vipdetail_id, b.vip_id, b.discountprice, b.quantity, b.addtime, b.endtime " \
               "from tb_item a left outer join tb_vipdetail b on " \
               "a.id = b.item_id and vip_id = :vip_id and b.quantity > 0 and b.endtime > now() where a.type = 1 and a.valid = 1 "
    # 条件查询(服务名称/类别/规格)
    if key:
        sql_text += "and (a.name like '%" + key + "%' or a.standard like '%" + key + "%' or a.cate like '%" + key + "%')"
    # 排序
    sql_text += "order by b.vip_id desc, a.name limit " + str(current_app.config['POSTS_PER_PAGE'])
    services = db.session.execute(text(sql_text), {'vip_id': vip_id})

    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for iter in services:
        vipdetail_id = ''
        vipdetail_discountprice = ''
        vipdetail_quantity = ''
        vipdetail_addtime = ''
        vipdetail_endtime = ''
        if iter.vipdetail_id:
            vipdetail_id = iter.vipdetail_id
            vipdetail_discountprice = iter.discountprice
            vipdetail_quantity = iter.quantity
            vipdetail_addtime = iter.addtime.strftime('%Y-%m-%d %H:%M:%S')
            vipdetail_endtime = iter.endtime.strftime('%Y-%m-%d %H:%M:%S')
        data.append(
            {
                "item_id": iter.id,
                "item_name": iter.name,
                "item_standard": iter.standard,
                "item_unit": iter.unit,
                "item_costprice": iter.costprice,
                "item_salesprice": iter.salesprice,
                "item_cate": iter.cate,
                "vipdetail_id": vipdetail_id,
                "vipdetail_discountprice": vipdetail_discountprice,
                "vipdetail_quantity": vipdetail_quantity,
                "vipdetail_addtime": vipdetail_addtime,
                "vipdetail_endtime": vipdetail_endtime,
            }
        )

    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/order/modal/stock', methods=['GET'])
@login_required
def order_modal_stock():
    # 获取库存商品弹出框数据
    key = request.args.get('key', '')
    vip_id = request.args.get('vip_id', '')
    sql_text = "select c.stock_id, c.item_id, c.qty, c.store, c.item_name, c.salesprice, c.rewardprice, c.costprice, c.unit, c.standard, c.cate, " \
               "d.id as vipdetail_id, d.vip_id, d.discountprice, d.quantity, d.addtime, d.endtime  " \
               "from (select a.id as stock_id, a.item_id, a.qty, a.store, b.name as item_name, b.salesprice, b.rewardprice, b.costprice, b.unit, b.standard, b.cate " \
               "from tb_stock a, tb_item b where a.item_id = b.id and a.qty > 0 and b.type = 0 and b.valid = 1) c " \
               "left outer join tb_vipdetail d on c.item_id = d.item_id and d.vip_id = :vip_id and d.quantity > 0 and d.endtime > now() "
    # 条件查询(零件名称/类别/规格)
    if key:
        sql_text += "where (c.item_name like '%" + key + "%' or c.standard like '%" + key + "%' or c.cate like '%" + key + "%')"
    # 排序
    sql_text += "order by d.vip_id desc, c.item_id, c.store limit " + str(current_app.config['POSTS_PER_PAGE'])
    services = db.session.execute(text(sql_text), {'vip_id': vip_id})

    # 返回的数据格式为
    # {
    # "pages": 1,
    # "data": [
    #         {"id": "1",
    #         "name": "xx"}
    #         ]
    # }
    data = []
    for iter in services:
        vipdetail_id = ''
        vipdetail_discountprice = ''
        vipdetail_quantity = ''
        vipdetail_addtime = ''
        vipdetail_endtime = ''
        if iter.vipdetail_id:
            vipdetail_id = iter.vipdetail_id
            vipdetail_discountprice = iter.discountprice
            vipdetail_quantity = iter.quantity
            vipdetail_addtime = iter.addtime.strftime('%Y-%m-%d %H:%M:%S')
            vipdetail_endtime = iter.endtime.strftime('%Y-%m-%d %H:%M:%S')
        data.append(
            {
                "item_id": iter.item_id,
                "item_name": iter.item_name,
                "item_standard": iter.standard,
                "item_unit": iter.unit,
                "item_costprice": iter.costprice,
                "item_salesprice": iter.salesprice,
                "item_cate": iter.cate,
                "stock_id": iter.stock_id,
                "qty": iter.qty,
                "store": iter.store,
                "vipdetail_id": vipdetail_id,
                "vipdetail_discountprice": vipdetail_discountprice,
                "vipdetail_quantity": vipdetail_quantity,
                "vipdetail_addtime": vipdetail_addtime,
                "vipdetail_endtime": vipdetail_endtime,
            }
        )

    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/modal/stock', methods=['GET'])
@login_required
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
                "item_salesprice": v.item.salesprice,
                "costprice": v.costprice,
                "store": v.store,
                "qty": v.qty,
                "item_cate": v.item.cate,
            }
        )
    res = {
        "key": key,
        "data": data,
    }
    return dumps(res)

@home.route('/store/get', methods=['GET', 'POST'])
@login_required
@permission_required
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

@home.route('/select/user', methods=["GET"])
@login_required
def select_user():
    # 加载员工
    users = []
    for v in User.query.order_by(User.name).all():
        users.append(
            {
                "id": v.name,
                "text": v.name,
            }
        )
    return dumps(users)

@home.route('/stock/list', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
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
@login_required
@permission_required
def stock_buy_view(id=None):
    # 采购单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_buy_view.html', porder=porder, podetails=podetails)

@home.route('/stock/buy/debt/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required
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
@login_required
@permission_required
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
        # 1009判断是否选择仓库
        for iter_add in form.inputrows:
            ns = Kvp.query.filter_by(
                type='store',
                value=iter_add.store.data,
            ).first()
            if not ns:
                flash(iter_add.item_name.data + u':未选择仓库', 'err')
                return redirect(url_for('home.stock_buy_edit', id=porder.id))
        # type_switch:1结算;0暂存
        switch = int(form.type_switch.data)
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
                status=0,
                remarks=form.remarks.data,
            )
        else:  # 有更新值
            porder.user_id = int(session['user_id'])
            porder.supplier_id = form.supplier_id.data
            porder.amount = form.amount.data
            porder.discount = form.discount.data
            porder.payment = form.payment.data
            porder.debt = form.debt.data
            porder.remarks = form.remarks.data
            porder.addtime = datetime.now()#更新为发布日期
        try:
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
                # 判断是否选择仓库
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
        except Exception as e:
            db.session.rollback()
            flash(u'采购单:%s结算/暂存异常,错误码：%s' % (porder.id, e), 'err')
            return redirect(url_for('home.stock_buy_edit', id=porder.id))

    return render_template('home/stock_buy_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/buy/del/<int:id>', methods=['GET'])
@login_required
@permission_required
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

@home.route('/stock/out/list', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
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
        try:
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
                porder.addtime = datetime.now()  # 更新为发布日期
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
                        flash(u'零件:[' + iter.item_name + u']出库后数量小于0', 'err')
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
        except Exception as e:
            db.session.rollback()
            flash(u'出库单:%s结算/暂存异常,错误码：%s' % (porder.id, e.message), 'err')
            return redirect(url_for('home.stock_out_edit', id=porder.id))

    return render_template('home/stock_out_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/out/del/<int:id>', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_out_view(id=None):
    # 出库单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_out_view.html', porder=porder, podetails=podetails)

@home.route('/stock/allot/list', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_allot_edit(id=None):
    # 调拨单
    form = StockAllotForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 2:
            return redirect(url_for('home.stock_allot_list'))

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
        # 1009判断是否选择仓库
        for iter_add in form.inputrows:
            ns = Kvp.query.filter_by(
                type='store',
                value=iter_add.nstore.data,
            ).first()
            if not ns:
                flash(iter_add.item_name.data + u':未选择仓库', 'err')
                return redirect(url_for('home.stock_allot_edit', id=porder.id))
        try:
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
                porder.addtime = datetime.now()  # 更新为发布日期
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
                        flash(u'零件:[' + iter.item_name + u']调拨后数量小于0', 'err')
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
        except Exception as e:
            db.session.rollback()
            flash(u'调拨单:%s结算/暂存异常,错误码：%s' % (porder.id, e), 'err')
            return redirect(url_for('home.stock_allot_edit', id=porder.id))

    return render_template('home/stock_allot_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/allot/del/<int:id>', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_allot_view(id=None):
    # 调拨单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_allot_view.html', porder=porder, podetails=podetails)

@home.route('/stock/loss/list', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_loss_edit(id=None):
    # 报损单
    form = StockLossForm()
    porder = Porder.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if porder:
        # 如果表单不属于用户，不是编辑状态 退出
        if porder.user_id != int(session['user_id']) or porder.status == 1 or porder.type != 3:
            return redirect(url_for('home.stock_loss_list'))

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
        try:
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
                porder.addtime = datetime.now()  # 更新为发布日期
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
                        flash(u'零件:[' + iter.item_name + u']报损后数量小于0', 'err')
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
        except Exception as e:
            db.session.rollback()
            flash(u'报损单:%s结算/暂存异常,错误码：%s' % (porder.id, e.message), 'err')
            return redirect(url_for('home.stock_loss_edit', id=porder.id))

    return render_template('home/stock_loss_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/loss/del/<int:id>', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_loss_view(id=None):
    # 报损单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_loss_view.html', porder=porder, podetails=podetails)

@home.route('/stock/return/list', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
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
        try:
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
                porder.addtime = datetime.now()  # 更新为发布日期
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
                        flash(u'零件:[' + iter.item_name + u']退货后数量小于0', 'err')
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
        except Exception as e:
            db.session.rollback()
            flash(u'退货单:%s结算/暂存异常,错误码：%s' % (porder.id, e.message), 'err')
            return redirect(url_for('home.stock_return_edit', id=porder.id))

    return render_template('home/stock_return_edit.html', form=form, porder=porder, form_count=form_count)

@home.route('/stock/return/del/<int:id>', methods=['GET'])
@login_required
@permission_required
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
@login_required
@permission_required
def stock_return_view(id=None):
    # 退货单明细查看
    porder = Porder.query.filter_by(id=id).first_or_404()
    podetails = Podetail.query.filter_by(porder_id=id).order_by(Podetail.id.asc()).all()
    return render_template('home/stock_return_view.html', porder=porder, podetails=podetails)

@home.route('/stock/return/debt/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required
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

@home.route('/stock/list/history/<int:id>', methods=['GET'])
@login_required
@permission_required
def stock_list_history(id=None):
    # 历史
    key = request.args.get('key', '')
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Porder, Podetail).filter(
        Porder.id == Podetail.porder_id,
        Porder.status == 1,
        Podetail.item_id == id,
        )
    # 条件查询
    if key:
        # 单号/备注
        pagination = pagination.filter(
            or_(Porder.remarks.ilike('%' + key + '%'),
                Porder.addtime.ilike('%' + key + '%'))
        )
    pagination = pagination.order_by(
        Porder.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/stock_list_history.html', pagination=pagination, key=key, id=id)

@home.route('/order/list', methods=['GET'])
@login_required
@permission_required
def order_list():
    # 收银单列表
    key = request.args.get('key', '')
    # 收银单状态 true 临时;false 全部
    status = request.args.get('status', 'false')
    # 是否欠款 true 欠;false 否
    debt = request.args.get('debt', 'false')
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.join(Customer).filter(
        Order.type == 0,
        Order.customer_id == Customer.id,
        )
    # 条件查询
    if key:
        # 单号/车牌/姓名/手机/备注/日期
        pagination = pagination.filter(
            or_(Order.id.ilike('%' + key + '%'),
                Customer.name.ilike('%' + key + '%'),
                Customer.pnumber.ilike('%' + key + '%'),
                Customer.phone.ilike('%' + key + '%'),
                Order.remarks.ilike('%' + key + '%'),
                Order.addtime.ilike('%' + key + '%'))
        )
    if status == 'true':
        pagination = pagination.filter(Order.status == 0)
    if debt == 'true':
        pagination = pagination.filter(Order.debt > 0)
    pagination = pagination.order_by(
        Order.addtime.desc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/order_list.html', pagination=pagination, key=key, status=status, debt=debt)

@home.route('/order/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@permission_required
def order_edit(id=None):
    # 收银单
    form = OrderForm()
    order = Order.query.filter_by(id=id).first()
    # 表单不存在代表新增不做校验
    if order:
        # 如果表单不属于用户，不是编辑状态 退出
        if order.user_id != int(session['user_id']) or order.status == 1 or order.type != 0:
            return redirect(url_for('home.order_list'))

    odetails = Odetail.query.filter(Odetail.order_id == id,).order_by(Odetail.id.asc()).all()
    if request.method == 'GET':
        # porder赋值
        if order:
            form.customer_id.data = order.customer_id
            form.customer_name.data = order.customer.name
            form.customer_phone.data = order.customer.phone
            form.customer_pnumber.data = order.customer.pnumber
            form.customer_brand.data = order.customer.brand
            form.paywith.data = order.paywith
            if order.customer.vip:
                form.vip_id.data = order.customer.vip_id
                form.vip_name.data = order.customer.vip.name
            form.customer_balance.data = order.customer.balance
            form.customer_score.data = order.customer.score
            form.amount.data = order.amount
            form.discount.data = order.discount
            form.payment.data = order.payment
            form.debt.data = order.debt
            form.balance.data = order.balance
            form.score.data = order.score
            form.remarks.data = order.remarks
        else:
            # 积分消耗默认为0
            form.balance.data = 0
            form.score.data = 0

        # 如果存在明细
        if odetails:
            # 先把空行去除
            while len(form.inputrows) > 0:
                form.inputrows.pop_entry()
            # 对FormField赋值，要使用append_entry方法
            for detail in odetails:
                listform = OrderListForm()
                listform.item_id = detail.item_id
                listform.item_name = detail.item.name
                listform.item_type = detail.item.type
                listform.stock_id = detail.stock_id # 方便计算
                listform.store = detail.store
                listform.item_unit = detail.item.unit
                listform.item_salesprice = detail.item.salesprice
                listform.vipdetail_id = detail.vipdetail_id # 方便计算
                listform.discount = detail.discount
                listform.qty = detail.qty
                listform.users = detail.users
                listform.rowamount = detail.rowamount
                form.inputrows.append_entry(listform)
    # 计算动态input的初值
    form_count = len(form.inputrows)
    if form.validate_on_submit():
        try:
            # type_switch:1结算;0暂存
            switch = int(form.type_switch.data)
            # 添加主表
            if not order:  # 没有新增一个
                order = Order(
                    id=datetime.now().strftime('%Y%m%d%H%M%S') + ''.join([str(random.randint(1,10)) for i in range(2)]),
                    type=0,
                    user_id=int(session['user_id']),
                    customer_id=form.customer_id.data,
                    paywith=form.paywith.data,
                    amount=form.amount.data,
                    discount=form.discount.data,
                    payment=form.payment.data,
                    debt=form.debt.data,
                    score=form.score.data,
                    status=0,
                    remarks=form.remarks.data,
                )
            else:  # 有更新值
                order.user_id = int(session['user_id'])
                order.customer_id = form.customer_id.data
                order.paywith = form.paywith.data
                order.amount = form.amount.data
                order.discount = form.discount.data
                order.payment = form.payment.data
                order.debt = form.debt.data
                order.balance = form.balance.data
                order.score = form.score.data
                order.status = 0
                order.remarks = form.remarks.data
                order.addtime = datetime.now()  # 更新为发布日期
            db.session.add(order)
            # 主表暂存，需要使用id
            db.session.flush()
            # 更改删除方式直接找到全部删除
            db.session.query(Odetail).filter(Odetail.order_id == order.id).delete()
            for iter_add in form.inputrows:
                # 新增明细
                # 折扣有可能为空，处理一下
                discount = 0 if iter_add.discount.data == "" else float(iter_add.discount.data)
                odetail = Odetail(
                    order_id=order.id,
                    item_id=iter_add.item_id.data,
                    stock_id=iter_add.stock_id.data,
                    store=iter_add.store.data,
                    qty=float(iter_add.qty.data), # 这里一定要强转，临时数据后面要比较
                    salesprice=float(iter_add.item_salesprice.data),
                    vipdetail_id=iter_add.vipdetail_id.data,
                    discount=discount,
                    rowamount=float(iter_add.rowamount.data),
                    users=iter_add.users.data,
                    #users=','.join(map(lambda v: str(v), iter_add.users.data)),
                )
                db.session.add(odetail)
            # 把所有明细暂存，后面用于计算是否存在核减为负数的情况
            db.session.commit()
            if switch == 1: # 结算
                # valid True可以提交; False 不能提交
                valid = True
                customer = Customer.query.filter(Customer.id == order.customer_id).first_or_404()
                # 判断余额是否充足
                if float(form.balance.data) > customer.balance:
                    flash(u'客户余额不足', 'err')
                    valid = False
                # 判断积分是否充足
                if float(form.score.data) > customer.score:
                    flash(u'客户积分不足', 'err')
                    valid = False
                # 判断优惠是否属于当前会员
                sql_text = 'select distinct o.order_id, o.item_id, i.name as item_name, o.discount, o.vipdetail_id from tb_odetail o, tb_item i  ' \
                           'where o.order_id = :order_id and o.item_id = i.id and o.vipdetail_id != \'\' and not exists ( ' \
                           'select id  from tb_vipdetail v where o.vipdetail_id = v.id and v.endtime > now() ) order by o.id '
                checklist = db.session.execute(text(sql_text), {'order_id': order.id})
                for iter in checklist:
                    flash(u'商品/服务:[' + iter.item_name + u']优惠已失效', 'err')
                    valid = False
                # 判断商品中有无大于库存的
                sql_text = 'select a.item_id, i.name as item_name, a.vipdetail_id, a.sum_qty, v.quantity, v.addtime, v.endtime from ' \
                           '(select item_id, vipdetail_id, sum(qty) as sum_qty from tb_odetail o where o.order_id = :order_id ' \
                           'group by item_id, vipdetail_id) as a, tb_item as i, tb_vipdetail v ' \
                           'where a.item_id = i.id and a.vipdetail_id = v.id and a.sum_qty > v.quantity and v.endtime > now()'
                checklist = db.session.execute(text(sql_text), {'order_id': order.id})
                for iter in checklist:
                    flash(u'商品/服务:[' + iter.item_name + u']能选择的优惠总数为' + str(int(iter.quantity)) + u',已选择' + str(int(iter.sum_qty)) + u'次' , 'err')
                    valid = False

                # 校验通过
                if valid:
                    # 商品冲减库存 tb_stock
                    ## 不过滤服务了，因为服务不可能有库存，有问题再说吧
                    stocklist = db.session.query(Odetail, Stock).filter(
                        Odetail.order_id == order.id,
                        Odetail.stock_id == Stock.id,
                        ).order_by(Odetail.id.asc()).all()
                    for iter in stocklist:
                        ## 减少库存数量
                        iter.Stock.qty -= iter.Odetail.qty
                        db.session.add(iter.Stock)
                    # 商品/服务 消减VIP优惠次数 tb_vipdetail
                    viplist = db.session.query(Odetail, Vipdetail).filter(
                        Odetail.order_id == order.id,
                        Odetail.vipdetail_id == Vipdetail.id,
                        ).order_by(Odetail.id.asc()).all()
                    for iter in viplist:
                        ## 减少VIP使用次数
                        iter.Vipdetail.quantity -= iter.Odetail.qty
                        db.session.add(iter.Vipdetail)
                    # 客户 更新到店次数/累计消费/余额/欠款/积分 tb_customer
                    customer.freq += 1
                    customer.summary += order.payment
                    customer.balance -= order.balance
                    customer.debt += order.debt
                    ## 积分 = 本次实际支付总额 * 会员积分系数 - 消费的积分总额
                    score_ins = 0
                    if customer.vip:
                        ## 如果是会员 增加的积分 = 消费金额 * 系数
                        score_ins = order.payment * customer.vip.scorerule
                    else:
                        ## 如果不是会员，系数按0.8计算；
                        score_ins = order.payment * 0.8
                    temp_score = score_ins - order.score
                    customer.score += temp_score
                    db.session.add(customer)
                    # 增加客户流水 tb_billing
                    billing = Billing(
                        cust_id=order.customer_id,
                        paywith=order.paywith,
                        order_id=order.id,
                        amount=order.amount,
                        payment=order.payment,
                        balance=order.balance,
                        score=order.score,
                        debt=order.debt,
                        paytype=u'收银付款',
                    )
                    db.session.add(billing)
                    # 订单状态更新 tb_order
                    order.status = 1  # 设置为发布状态
                    db.session.add(order)
                    # 记录出库日志
                    oplog = Oplog(
                        user_id=session['user_id'],
                        ip=request.remote_addr,
                        reason=u'结算收银单:%s' % order.id
                    )
                    db.session.add(oplog)
                    db.session.commit()
                    flash(u'收银单结算成功', 'ok')
                    return redirect(url_for('home.order_list'))
                # 校验不通过,暂存
                else:
                    oplog = Oplog(
                        user_id=session['user_id'],
                        ip=request.remote_addr,
                        reason=u'结算收银单:%s失败' % order.id
                    )
                    db.session.add(oplog)
                    db.session.commit()
                    return redirect(url_for('home.order_edit', id=order.id))

            else:  # 暂存
                oplog = Oplog(
                    user_id=session['user_id'],
                    ip=request.remote_addr,
                    reason=u'暂存收银单:%s' % order.id
                )
                db.session.commit()
                flash(u'收银单暂存成功', 'ok')
                return redirect(url_for('home.order_list'))


        except Exception as e:
            db.session.rollback()
            order_id = '0'
            if order:
                order_id = order.id
            flash(u'收银单:%s结算/暂存异常,错误码：%s' % (order_id, e), 'err')
            return redirect(url_for('home.order_edit', id=order_id))
    return render_template('home/order_edit.html', form=form, order=order, form_count=form_count)

@home.route('/order/del/<string:id>', methods=['GET'])
@login_required
@permission_required
def order_del(id=None):
    # 收银单删除
    order = Order.query.filter_by(id=id).first_or_404()
    if order.type != 0 or order.user_id != int(session['user_id']) or order.status == 1:
        return redirect(url_for('home.order_list'))
    Odetail.query.filter_by(order_id=id).delete()
    db.session.delete(order)
    oplog = Oplog(
        user_id=session['user_id'],
        ip=request.remote_addr,
        reason=u'删除收银单:%s' % order.id
    )
    db.session.add(oplog)
    db.session.commit()
    flash(u'收银单删除成功', 'ok')
    return redirect(url_for('home.order_list'))

@home.route('/order/view/<string:id>', methods=['GET'])
@login_required
@permission_required
def order_view(id=None):
    # 收银单明细查看
    order = Order.query.filter_by(id=id).first_or_404()
    odetails = Odetail.query.filter_by(order_id=id).order_by(Odetail.id.asc()).all()
    return render_template('home/order_view.html', order=order, odetails=odetails)

@home.route('/order/debt/<string:id>', methods=['GET', 'POST'])
@login_required
@permission_required
def order_debt(id=None):
    # 收银单结款
    form = OrderDebtForm()
    order = Order.query.filter_by(id=id).first_or_404()
    billing = Billing.query.filter_by(order_id=id).order_by(Billing.id.desc()).first_or_404()
    # 如果表单不属于用户，不是发布状态 退出
    if order.user_id != int(session['user_id']) or order.status == 0 or order.type != 0:
        return redirect(url_for('home.order_list'))
    if request.method == 'GET':
        form.customer_name.data = order.customer.name
        form.customer_phone.data = order.customer.phone
        form.customer_pnumber.data = order.customer.pnumber
        form.customer_brand.data = order.customer.brand
        form.paywith.data = order.paywith
        if order.customer.vip:
            form.vip_id.data = order.customer.vip_id
            form.vip_name.data = order.customer.vip.name
        form.customer_balance.data = order.customer.balance
        form.customer_score.data = order.customer.score
        form.amount.data = order.amount
        form.discount.data = order.discount
        form.payment.data = order.payment
        form.balance.data = order.balance
        form.score.data = order.score
        form.debt.data = order.debt
        form.remarks.data = order.remarks
    if form.validate_on_submit():
        if float(form.debt.data) >= order.debt:
            flash(u'欠款不能增多', 'err')
            return redirect(url_for('home.order_debt', id=id))
        # 订单
        order.paywith = form.paywith.data
        order.amount = float(form.amount.data)
        order.discount = float(form.discount.data)
        order.payment = float(form.payment.data)
        order.balance = float(form.balance.data)
        order.score = float(form.score.data)
        order.debt = float(form.debt.data)
        order.remarks = form.remarks.data
        order.addtime = datetime.now()
        db.session.add(order)
        # 消费流水,与上次算差值
        new_billing = Billing(
            cust_id=order.customer_id,
            paywith=order.paywith,
            order_id=order.id,
            amount=order.amount,
            payment=order.payment,
            balance=order.balance,
            score=order.score,
            debt=order.debt,
            paytype=u'收银结款',
        )
        db.session.add(new_billing)
        oplog = Oplog(
            user_id=session['user_id'],
            ip=request.remote_addr,
            reason=u'修改结款,收银单号:%s' % order.id
        )
        db.session.add(oplog)
        db.session.commit()
        flash(u'结款修改成功', 'ok')
        return redirect(url_for('home.order_list'))
    return render_template('home/order_debt.html', form=form, order=order)

@home.route('/order/billing/<string:id>', methods=['GET'])
@login_required
@permission_required
def order_billing(id=None):
    # 流水历史列表
    page = request.args.get('page', 1, type=int)
    pagination = Billing.query.filter_by(order_id=id).order_by(
        Billing.addtime.asc()
    ).paginate(page=page,
               per_page=current_app.config['POSTS_PER_PAGE'],
               error_out=False)
    return render_template('home/order_billing.html', pagination=pagination, id=id)

@home.route('/sales/report/', methods=['GET', 'POST'])
@login_required
@permission_required
def sales_report():
    # 收银报表
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '')
    form = SalesAdvancedForm()
    pagination = None
    if form.validate_on_submit():
        pagination = db.session.query(Order, Odetail, Customer, Item).filter(
            Order.id == Odetail.order_id,
            Order.customer_id == Customer.id,
            Odetail.item_id == Item.id)
        if form.order_id.data:
            search_key = form.order_id.data
            pagination = pagination.filter(Order.id.ilike('%' + search_key + '%'))
        if form.customer_name.data:
            search_key = form.customer_name.data
            pagination = pagination.filter(Customer.name.ilike('%' + search_key + '%'))
        if form.item_name.data:
            search_key = form.item_name.data
            pagination = pagination.filter(Item.name.ilike('%' + search_key + '%'))
        if form.users.data:
            search_key = form.users.data
            pagination = pagination.filter(Odetail.users.ilike('%' + search_key + '%'))
        if form.date_from.data:
            search_key = datetime.strptime(form.date_from.data, '%Y-%m-%d')
            pagination = pagination.filter(Order.addtime >= search_key)
        if form.date_to.data:
            search_key = datetime.strptime(form.date_to.data, '%Y-%m-%d') + timedelta(days=1)
            pagination = pagination.filter(Order.addtime < search_key)
        pagination = pagination.order_by(
            Order.addtime.desc(), Odetail.id.asc()
        ).paginate(page=page,
                   per_page=current_app.config['POSTS_PER_PAGE'],
                   error_out=False)
    else:
        pagination = db.session.query(Order, Odetail, Customer, Item).filter(
            Order.id == Odetail.order_id,
            Order.customer_id == Customer.id,
            Odetail.item_id == Item.id)
        # 条件查询
        if key:
            # 单号/车牌/姓名/手机/备注/日期
            pagination = pagination.filter(
                or_(Order.id.ilike('%' + key + '%'),
                    Customer.name.ilike('%' + key + '%'),
                    Item.name.ilike('%' + key + '%'),
                    Odetail.users.ilike('%' + key + '%'))
            )
        pagination = pagination.order_by(
            Order.addtime.desc(), Odetail.id.asc()
        ).paginate(page=page,
                   per_page=current_app.config['POSTS_PER_PAGE'],
                   error_out=False)
    return render_template('home/sales_report.html', form=form, pagination=pagination, key=key)


#20181027 会员充值报表
@home.route('/vips/report/', methods=['GET', 'POST'])
@login_required
@permission_required
def vips_report():
    # 收银报表
    page = request.args.get('page', 1, type=int)
    key = request.args.get('key', '')
    form = VipsAdvancedForm()
    pagination = None
    pagination = db.session.query(Customer, Billing).filter(
        Customer.vip_id == Billing.vip_id)
    if form.validate_on_submit():
        if form.customer_name.data:
            search_key = form.customer_name.data
            pagination = pagination.filter(Customer.name.ilike('%' + search_key + '%'))
        if form.phone.data:
            search_key = form.phone.data
            pagination = pagination.filter(Customer.phone.ilike('%' + search_key + '%'))
        if form.date_from.data:
            search_key = datetime.strptime(form.date_from.data, '%Y-%m-%d')
            pagination = pagination.filter(Billing.addtime >= search_key)
        if form.date_to.data:
            search_key = datetime.strptime(form.date_to.data, '%Y-%m-%d') + timedelta(days=1)
            pagination = pagination.filter(Billing.addtime < search_key)
        pagination = pagination.order_by(
            Billing.addtime.desc(), Customer.name.asc()
        ).paginate(page=page,
                   per_page=current_app.config['POSTS_PER_PAGE'],
                   error_out=False)
    else:
        # 条件查询
        if key:
            # 客户姓名/车牌/手机
            pagination = pagination.filter(
                or_(Customer.name.ilike('%' + key + '%'),
                    Customer.pnumber.ilike('%' + key + '%'),
                    Customer.phone.ilike('%' + key + '%'))
            )
        pagination = pagination.order_by(
            Billing.addtime.desc(), Customer.name.asc()
        ).paginate(page=page,
                   per_page=current_app.config['POSTS_PER_PAGE'],
                   error_out=False)
    return render_template('home/cus_vip_report.html', form=form, pagination=pagination, key=key)


#20181027 会员充值信息
@home.route('/vips/report_list/', methods=['GET', 'POST'])
@login_required
@permission_required
def vips_report_list():
    # 获取会员充值信息
    if request.method == 'POST':
        # 获取json数据
        obj_vips_report = db.session.query(Customer, Billing).filter(Customer.vip_id == Billing.vip_id).order_by(Billing.addtime.desc(), Customer.name.asc())
        if obj_vips_report:
            s_json = []
            i = 1
            for v in obj_vips_report:
                dic = collections.OrderedDict()
                dic[u"编号"] = i
                dic[u"姓名"] = v.Customer.name
                dic[u"手机号"] = v.Customer.phone
                dic[u"品牌类型"] = v.Customer.brand
                dic[u"车牌号"] = v.Customer.pnumber
                dic[u"余额"] = v.Customer.balance
                dic[u"积分余额"] = v.Customer.score
                dic[u"支付方式"] = v.Billing.paytype
                dic[u"应付金额"] = v.Billing.paywith
                dic[u"支付金额"] = v.Billing.amount
                dic[u"支付方式"] = v.Billing.payment
                dic[u"欠款"] = v.Billing.debt
                dic[u"支付时间"] = str( v.Billing.addtime)
                s_json.append(dic)
                i = i + 1
            return (dumps(s_json))
        else:
            return (None)


#20181029 收银报表信息
@home.route('/sales/report_list/', methods=['GET', 'POST'])
@login_required
@permission_required
def sales_report_list():
    # 获取收银报表信息
    if request.method == 'POST':

        obj_sales_report = db.session.query(Order, Odetail, Customer, Item).filter(
            Order.id == Odetail.order_id, Order.customer_id == Customer.id,
            Odetail.item_id == Item.id).order_by(Order.addtime.desc(), Odetail.id.asc())

        if obj_sales_report:
            s_json = []
            i = 1
            for v in obj_sales_report:
                dic = collections.OrderedDict()
                dic[u"编号"] = i
                dic[u"订单号"] = str(v.Order.id)
                dic[u"应收"] = v.Order.amount
                dic[u"优惠后"] = v.Order.discount
                dic[u"实收"] = v.Order.payment
                dic[u"欠款"] = v.Order.debt
                dic[u"客户"] = v.Customer.name
                dic[u"时间"] = str(v.Order.addtime)
                dic[u"商品 / 服务"] = v.Item.name
                dic[u"单价"] = v.Odetail.salesprice
                dic[u"折扣价"] = v.Odetail.discount
                dic[u"提成"] = v.Item.rewardprice
                dic[u"数量"] = v.Odetail.qty
                dic[u"合计"] = v.Odetail.rowamount
                dic[u"工作人员"] = v.Odetail.users
                s_json.append(dic)
                i = i + 1
            return (dumps(s_json))
        else:
            return (None)