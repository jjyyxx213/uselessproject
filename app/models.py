# -*- coding:utf-8 -*-
from datetime import datetime
from app import db
from werkzeug.security import check_password_hash

# 字典
class Kvp(db.Model):
    __tablename__ = 'tb_kvp'
    # 编号
    type = db.Column(db.String(100), nullable=False)
    key = db.Column(db.Integer, primary_key=True, autoincrement=True)
    value = db.Column(db.String(200), nullable=False)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    def __repr__(self):
        return "<Kvp %r:%r>" % self.key, self.value


# 用户
class User(db.Model):
    __tablename__ = "tb_user"
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 姓名
    name = db.Column(db.String(100), nullable=False)
    # 密码
    pwd = db.Column(db.String(100), nullable=False)
    # 邮箱
    email = db.Column(db.String(100), unique=True)
    # 手机号
    phone = db.Column(db.String(11), unique=True)
    # 身份证
    id_card = db.Column(db.String(18), unique=True)
    # 工种
    jobs = db.Column(db.String(100))
    # 底薪
    salary = db.Column(db.Float, default=0)
    # 是否冻结(1：冻结；0：解冻)
    frozen = db.Column(db.SmallInteger, default=0, nullable=False)
    # 注册时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    # 唯一标识符
    uuid = db.Column(db.String(255), unique=True)
    # 所属角色
    role_id = db.Column(db.Integer, db.ForeignKey('tb_role.id'))

    # 员工登录日志外键关联
    userlogs = db.relationship('Userlog', backref='user')
    # 员工操作日志外键关系关联
    oplogs = db.relationship('Oplog', backref='user')
    # 客户外键关系关联
    customers = db.relationship('Customer', backref='user')
    # 库存单外键关联
    porders = db.relationship('Porder', backref='user')
    # 订单外键关联
    orders = db.relationship('Order', backref='user')

    def __repr__(self):
        return "<User %r>" % self.name

    def verify_password(self, password):
        return check_password_hash(self.pwd, password)

# 角色
class Role(db.Model):
    __tablename__ = "tb_role"
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), unique=True)
    # 角色权限列表
    auths = db.Column(db.String(600))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    #员工关系外键
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return "<Auth %r>" % self.name

# 权限
class Auth(db.Model):
    __tablename__ = "tb_auth"
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), unique=True)
    # 地址
    url = db.Column(db.String(255), unique=True)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<Auth %r>" % self.name

# 操作日志
class Oplog(db.Model):
    __tablename__ = 'tb_oplog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 编号
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))  # 所属员工
    ip = db.Column(db.String(100))  # 操作IP
    reason = db.Column(db.String(600))  # 操作原因
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return '<Oplog %r>' % self.user_id

# 员工登录日志
class Userlog(db.Model):
    __tablename__ = 'tb_userlog'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 所属员工id
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 登录ip
    ip = db.Column(db.String(100))
    # 登录时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Userlog %r>' %self.user_id

# 会员卡
class Mscard(db.Model):
    __tablename__ = 'tb_mscard'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), nullable=False)
    # 开卡金额
    payment = db.Column(db.Float, default=0)
    # 有效期区间 数字类型(月)
    interval = db.Column(db.Float, default=1)
    # 积分规则(积分=消费金额*积分规则)
    scorerule = db.Column(db.Float, default=1)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999)
    # 卡状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 会员卡明细外键
    msdetails = db.relationship('Msdetail', backref='mscard')

    def __repr__(self):
        return '<Mscard %r>' % self.name

    # 20180927 liuqq 转换json串儿
    def to_json(self):
        str_json = {'id': self.id,
                    'name': self.name,
                    'payment': self.payment,
                    'interval': self.interval,
                    'scorerule': self.scorerule,
                    'scorelimit': self.scorelimit,
                    'valid': self.valid
                    }
        return str_json

# 会员卡明细
class Msdetail(db.Model):
    __tablename__ = 'tb_msdetail'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 会员卡号
    mscard_id = db.Column(db.Integer, db.ForeignKey('tb_mscard.id'), nullable=False)
    # 服务/项目id
    item_id = db.Column(db.Integer, db.ForeignKey('tb_item.id'), nullable=True)
    # 优惠后销售价
    discountprice = db.Column(db.Float, default=0)
    # 使用次数
    quantity = db.Column(db.Integer, default=9999)
    # 有效期 数字类型(月)
    interval = db.Column(db.Float, default=0)

    def __repr__(self):
        return '<Msdetail %r>' % self.name

    # 20180927 liuqq 转换json串儿
    def to_json(self):
        str_json = {'id': self.id,
                    'mscard_id': self.mscard_id,
                    'item_id': self.item_id,
                    'discountprice': self.discountprice,
                    'quantity': self.quantity,
                    'interval': self.interval,
                    'salesprice': self.item.salesprice,
                    'item_name': self.item.name
                    }
        return str_json

# 客户会员卡
class Vip(db.Model):
    __tablename__ = 'tb_vip'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), nullable=False)
    # 余额
    balance = db.Column(db.Float, default=0)
    # 积分余额
    score = db.Column(db.Float, default=0)
    # 积分规则(积分=消费金额*积分规则)
    scorerule = db.Column(db.Float, default=1)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999)
    # 办理时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    # 截止时间
    endtime = db.Column(db.DateTime,index=True, default=datetime.now)

    # 客户会员卡明细外键
    vipdetails = db.relationship('Vipdetail', backref='vip')

    # 2080928 liuqq 客户外键
    customer = db.relationship('Customer',backref='vip')

    def __repr__(self):
        return '<Vip %r>' % self.name

# 客户会员卡优惠明细
class Vipdetail(db.Model):
    __tablename__ = 'tb_vipdetail'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 客户会员卡号
    vip_id = db.Column(db.Integer, db.ForeignKey('tb_vip.id'), nullable=False)
    # 服务/项目id
    item_id = db.Column(db.Integer, db.ForeignKey('tb_item.id'), nullable=False)
    # 优惠后销售价
    discountprice = db.Column(db.Float, default=0)
    # 使用次数
    quantity = db.Column(db.Integer, default=9999)
    # 优惠开始时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    # 优惠结束时间
    endtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Vipdetail %r>' % self.name

# 商品/服务类别
class Category(db.Model):
    __tablename__ = 'tb_category'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), nullable=False)
    # 类别(0:商品;1:服务项目)
    type = db.Column(db.SmallInteger, default=0)
    # 备注
    remarks = db.Column(db.Text)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Category %r>' % self.name

# 服务/项目主表
class Item(db.Model):
    __tablename__ = 'tb_item'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), nullable=False)
    # 商品/服务类别(冗余避免关联查询)
    cate = db.Column(db.String(100))
    # 类别(类别字段冗余，避免关联查询 type 0: item; 1: service)
    type = db.Column(db.SmallInteger, default=0)
    # 销售价
    salesprice = db.Column(db.Float, default=0)
    # 提成
    rewardprice = db.Column(db.Float, default=0)
    # 成本价
    costprice = db.Column(db.Float, default=0)
    # 单位
    unit = db.Column(db.String(40))
    # 规格
    standard = db.Column(db.String(100))
    # 状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1)
    # 备注
    remarks = db.Column(db.Text)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 会员卡明细外键
    msdetails = db.relationship('Msdetail', backref='item')
    # 客户会员卡明细外键
    vipdetails = db.relationship('Vipdetail', backref='item')
    # 库存外键
    stocks = db.relationship('Stock', backref='item')
    # 采购单明细外键
    podetails = db.relationship('Podetail', backref='item')

    def __repr__(self):
        return '<Item %r>' % self.name

    def to_json(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        return dict

# 供应商表
class Supplier(db.Model):
    __tablename__ = 'tb_supplier'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(100), nullable=False)
    # 联络人
    contact = db.Column(db.String(50), nullable=False)
    # 手机
    phone = db.Column(db.String(11))
    # 联系电话
    tel = db.Column(db.String(11))
    # QQ
    qq = db.Column(db.String(11))
    # 地址
    address = db.Column(db.String(200))
    # 状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1)
    # 备注
    remarks = db.Column(db.Text)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 采购订单外键
    porders = db.relationship('Porder', backref='supplier')

    def __repr__(self):
        return '<Supplier %r>' % self.name

# 库存表
class Stock(db.Model):
    __tablename__ = 'tb_stock'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 仓库名称
    store = db.Column(db.String(40), nullable=False)
    # 商品ID
    item_id = db.Column(db.Integer, db.ForeignKey('tb_item.id'), nullable=True)
    # 采购单价（最后一次采购价）
    costprice = db.Column(db.Float, default=0)
    # 数量
    qty = db.Column(db.Float, default=0)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Stock %r>' % self.id

# 采购订单主表
class Porder(db.Model):
    __tablename__ = 'tb_porder'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 单据类型 0:采购单 1:领料单 2:调拨单 3:报损单 4:退货单
    type = db.Column(db.SmallInteger, default=0)
    # 采购/领料/退货/报损ID
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 供应商id
    supplier_id = db.Column(db.Integer, db.ForeignKey('tb_supplier.id'))
    # 应收应付金额（主体为店主+为收款/-为付款）
    amount = db.Column(db.Float, default=0)
    # 优惠后应收应付金额(主体为店主+为收款/-为付款)
    discount = db.Column(db.Float, default=0)
    # 实际收付金额(主体为店主+为收款/-为付款)
    payment = db.Column(db.Float, default=0)
    # 欠款(主体为店主+为收款/-为付款)
    debt = db.Column(db.Float, default=0)
    # 单据状态 0:暂存 1:生效
    status = db.Column(db.SmallInteger, default=0)
    # 备注
    remarks = db.Column(db.String(200))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Porder %r>' % self.id

# 采购订单明细表
class Podetail(db.Model):
    __tablename__ = 'tb_podetail'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 采购订单号
    porder_id = db.Column(db.Integer, db.ForeignKey('tb_porder.id'), nullable=False)
    # 商品ID
    item_id = db.Column(db.Integer, db.ForeignKey('tb_item.id'), nullable=True)
    # 原仓库
    ostore = db.Column(db.String(40))
    # 新仓库
    nstore = db.Column(db.String(40))
    # 数量(进货、退货数量)
    qty = db.Column(db.Float, default=0)
    # 进货/退货单价
    costprice = db.Column(db.Float, default=0)
    # 单行合计
    rowamount = db.Column(db.Float, default=0)

    def __repr__(self):
        return '<Podetail %r>' % self.id

# 客户
class Customer(db.Model):
    __tablename__ = 'tb_customer'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 姓名
    name = db.Column(db.String(100), nullable=False)
    # 微信昵称
    name_wechat = db.Column(db.String(100))
    # 性别
    sex = db.Column(db.String(10))
    # 手机号
    phone = db.Column(db.String(11), unique=True)
    # 车牌号
    pnumber = db.Column(db.String(20), unique=True)
    # 车架号
    vin = db.Column(db.String(50))
    # 品牌类型
    brand = db.Column(db.String(100))
    # 邮箱
    email = db.Column(db.String(100))
    # 身份证
    id_card = db.Column(db.String(18))
    # 所属客户经理
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 到店次数
    freq = db.Column(db.Integer, default=0)
    # 累计消费
    summary = db.Column(db.Float, default=0)
    # 欠款 20181011 增加
    debt = db.Column(db.Float, default=0)
    # 会员卡号
    vip_id = db.Column(db.Integer, db.ForeignKey('tb_vip.id'))
    # 注册时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 消费流水外键
    billings = db.relationship('Billing', backref='customer')
    # 订单外键关联
    orders = db.relationship('Order', backref='customer')

    def __repr__(self):
        return '<Customer %r>' % self.name

# 客户消费流水
class Billing(db.Model):
    __tablename__ = 'tb_billing'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 客户id
    cust_id = db.Column(db.Integer, db.ForeignKey('tb_customer.id'), nullable=False)
    # 支付方式
    paywith = db.Column(db.String(100), nullable=False)
    # 订单id
    order_id = db.Column(db.String(20), db.ForeignKey('tb_order.id'), unique=True)
    # 销售金额
    price = db.Column(db.Float, default=0)
    # 销售积分
    score = db.Column(db.Float, default=0)
    # 支付时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Billing %r>' % self.paywith

# 销售订单主表
class Order(db.Model):
    __tablename__ = 'tb_order'
    # 编号
    id = db.Column(db.String(20), primary_key=True)
    # 单据类型 0:快速开单
    type = db.Column(db.SmallInteger, default=0)
    # 开单人id
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 客户id
    customer_id = db.Column(db.Integer, db.ForeignKey('tb_customer.id'))
    # 应收金额
    amount = db.Column(db.Float, default=0)
    # 优惠后应收金额
    discount = db.Column(db.Float, default=0)
    # 实际收款金额
    payment = db.Column(db.Float, default=0)
    # 积分抵扣
    score = db.Column(db.Float, default=0)
    # 欠款
    debt = db.Column(db.Float, default=0)
    # 单据状态 0:暂存 1:生效
    status = db.Column(db.SmallInteger, default=0)
    # 备注
    remarks = db.Column(db.String(200))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 客户消费流水外键
    billings = db.relationship('Billing', backref='order')

    def __repr__(self):
        return '<Order %r>' % self.name


# 销售订单明细表
class Odetail(db.Model):
    __tablename__ = 'tb_odetail'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 销售订单号
    order_id = db.Column(db.String(20), db.ForeignKey('tb_order.id'), nullable=False)
    # 项目/商品ID
    item_id = db.Column(db.Integer, db.ForeignKey('tb_item.id'), nullable=True)
    # 仓库
    store = db.Column(db.String(40))
    # 数量
    qty = db.Column(db.Float, default=0)
    # 销售单价
    salesprice = db.Column(db.Float, default=0)
    # 折扣价
    discount = db.Column(db.Float, default=0)
    # 单行合计
    rowamount = db.Column(db.Float, default=0)
    # 施工/销售人员 用于计算提成
    users = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Odetail %r>' % self.id

