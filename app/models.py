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

# 管理员
class Admin(db.Model):
    __tablename__ = 'tb_admin'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 管理员账号
    pwd = db.Column(db.String(100))  # 管理员密码
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    def __repr__(self):
        return '<Admin %r>' % self.name

    def verify_password(self, pwd):
        return check_password_hash(self.pwd, pwd)

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
    salary = db.Column(db.Float, default=0, nullable=False)
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
    # 权限等级
    level = db.Column(db.Integer)
    # 名称
    name = db.Column(db.String(100), unique=True)
    # 地址
    url = db.Column(db.String(255), unique=True)
    # 20181108 上级id
    p_id = db.Column(db.Integer)
    # 20181106 元素标识
    html_id = db.Column(db.String(200))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def to_json(self):
        str_json = {'id': self.id,
                    'level': self.level,
                    'name': self.name,
                    'url': self.url,
                    'p_id': self.p_id,
                    'html_id': self.html_id
                    }
        return str_json

    def __repr__(self):
        return "<Auth %r>" % self.name

# 操作日志
class Oplog(db.Model):
    __tablename__ = 'tb_oplog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 编号
    user_id = db.Column(db.Integer)  # 所属员工  20181024 取消user外键,admin日志也记录这里头
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
    payment = db.Column(db.Float, default=0, nullable=False)
    # 有效期区间 数字类型(月)
    interval = db.Column(db.Float, default=1, nullable=False)
    # 积分规则(积分=消费金额*积分规则)
    scorerule = db.Column(db.Float, default=1, nullable=False)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999, nullable=False)
    # 卡状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1, nullable=False)
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
    discountprice = db.Column(db.Float, default=0, nullable=False)
    # 使用次数
    quantity = db.Column(db.Integer, default=9999, nullable=False)
    # 有效期 数字类型(月)
    interval = db.Column(db.Float, default=0, nullable=False)

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
    #balance = db.Column(db.Float, default=0, nullable=False)
    # 积分余额
    #score = db.Column(db.Float, default=0, nullable=False)
    # 积分规则(积分=消费金额*积分规则)
    scorerule = db.Column(db.Float, default=1, nullable=False)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999, nullable=False)
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
    discountprice = db.Column(db.Float, default=0, nullable=False)
    # 使用次数
    quantity = db.Column(db.Integer, default=9999, nullable=False)
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
    type = db.Column(db.SmallInteger, default=0, nullable=False)
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
    type = db.Column(db.SmallInteger, default=0, nullable=False)
    # 销售价
    salesprice = db.Column(db.Float, default=0, nullable=False)
    # 提成
    rewardprice = db.Column(db.Float, default=0, nullable=False)
    # 成本价
    costprice = db.Column(db.Float, default=0, nullable=False)
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
    # 收银单明细外键
    odetails = db.relationship('Odetail', backref='item')

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
    phone = db.Column(db.String(20))
    # 联系电话
    tel = db.Column(db.String(20))
    # QQ
    qq = db.Column(db.String(20))
    # 地址
    address = db.Column(db.String(200))
    # 状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1, nullable=False)
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
    costprice = db.Column(db.Float, default=0, nullable=False)
    # 数量
    qty = db.Column(db.Float, default=0, nullable=False)
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
    type = db.Column(db.SmallInteger, default=0, nullable=False)
    # 采购/领料/退货/报损ID
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 供应商id
    supplier_id = db.Column(db.Integer, db.ForeignKey('tb_supplier.id'))
    # 应收应付金额（主体为店主+为收款/-为付款）
    amount = db.Column(db.Float, default=0, nullable=False)
    # 优惠后应收应付金额(主体为店主+为收款/-为付款)
    discount = db.Column(db.Float, default=0, nullable=False)
    # 实际收付金额(主体为店主+为收款/-为付款)
    payment = db.Column(db.Float, default=0, nullable=False)
    # 欠款(主体为店主+为收款/-为付款)
    debt = db.Column(db.Float, default=0, nullable=False)
    # 单据状态 0:暂存 1:生效
    status = db.Column(db.SmallInteger, default=0, nullable=False)
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
    qty = db.Column(db.Float, default=0, nullable=False)
    # 进货/退货单价
    costprice = db.Column(db.Float, default=0, nullable=False)
    # 单行合计
    rowamount = db.Column(db.Float, default=0, nullable=False)

    def __repr__(self):
        return '<Podetail %r>' % self.id

# 客户
class Customer(db.Model):
    __tablename__ = 'tb_customer'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 姓名
    name = db.Column(db.String(100), nullable=False)
    # 性别
    sex = db.Column(db.String(10))
    # 手机号
    phone = db.Column(db.String(11), unique=True)
    # 车牌号
    pnumber = db.Column(db.String(20))
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
    freq = db.Column(db.Integer, default=0, nullable=False)
    # 累计消费
    summary = db.Column(db.Float, default=0, nullable=False)
    # 余额 20181020 增加
    balance = db.Column(db.Float, default=0, nullable=False)
    # 积分余额 20181020 增加
    score = db.Column(db.Float, default=0, nullable=False)
    # 欠款 20181011 增加
    debt = db.Column(db.Float, default=0, nullable=False)
    # 会员卡号
    vip_id = db.Column(db.Integer, db.ForeignKey('tb_vip.id'))
    # 注册时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    # 微信openid
    openid_wechat = db.Column(db.String(100))
    # 微信昵称
    name_wechat = db.Column(db.String(100))

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
    order_id = db.Column(db.String(20), db.ForeignKey('tb_order.id'))
    # 20181024 会员卡号
    vip_id = db.Column(db.Integer, db.ForeignKey('tb_vip.id'))
    # 应付金额
    amount = db.Column(db.Float, default=0, nullable=False)
    # 支付金额
    payment = db.Column(db.Float, default=0, nullable=False)
    # 积分抵扣
    score = db.Column(db.Float, default=0, nullable=False)
    # 余额抵扣
    balance = db.Column(db.Float, default=0, nullable=False)
    # 欠款
    debt = db.Column(db.Float, default=0, nullable=False)
    # 支付时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    # 20181025 支付分类 如:会员充值
    paytype = db.Column(db.String(100))

    def __repr__(self):
        return '<Billing %r>' % self.paywith

# 销售订单主表
class Order(db.Model):
    __tablename__ = 'tb_order'
    # 编号
    id = db.Column(db.String(20), primary_key=True)
    # 单据类型 0:快速开单
    type = db.Column(db.SmallInteger, default=0, nullable=False)
    # 开单人id
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'))
    # 客户id
    customer_id = db.Column(db.Integer, db.ForeignKey('tb_customer.id'))
    # 支付方式
    paywith = db.Column(db.String(100), nullable=False)
    # 应收金额
    amount = db.Column(db.Float, default=0, nullable=False)
    # 优惠后应收金额
    discount = db.Column(db.Float, default=0, nullable=False)
    # 实际收款金额
    payment = db.Column(db.Float, default=0, nullable=False)
    # 余额抵扣
    balance = db.Column(db.Float, default=0, nullable=False)
    # 积分抵扣
    score = db.Column(db.Float, default=0, nullable=False)
    # 欠款
    debt = db.Column(db.Float, default=0, nullable=False)
    # 单据状态 0:暂存 1:生效
    status = db.Column(db.SmallInteger, default=0, nullable=False)
    # 备注
    remarks = db.Column(db.String(200))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    # 销售订单明细表外键
    odetails = db.relationship('Odetail', backref='order')
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
    # 仓库编号 冗余
    stock_id = db.Column(db.String(20))
    # 仓库
    store = db.Column(db.String(40))
    # 数量
    qty = db.Column(db.Float, default=0, nullable=False)
    # 销售单价
    salesprice = db.Column(db.Float, default=0, nullable=False)
    # 会员卡明细id  冗余
    vipdetail_id = db.Column(db.String(20))
    # 折扣价
    discount = db.Column(db.Float, default=0, nullable=False)
    # 单行合计
    rowamount = db.Column(db.Float, default=0, nullable=False)
    # 施工/销售人员 用于计算提成
    users = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Odetail %r>' % self.id

# 微信素材
class WechatMedia(db.Model):
    __tablename__ = 'tb_wechatmedia'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 标题
    title = db.Column(db.String(100), nullable=False)
    # 类型
    type = db.Column(db.String(40), nullable=False)
    # 路径
    file_path = db.Column(db.String(255))
    # 微信url
    url = db.Column(db.String(255))
    # 上传时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<WechatMedia %r>' % self.title

# 微信门店
class WechatPoi(db.Model):
    __tablename__ = 'tb_wechatpoi'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 商户自己内部ID，即字段中的sid
    uniqid = db.Column(db.String(100), nullable=False)
    # 微信的门店ID，微信内门店唯一标示ID
    poiid = db.Column(db.String(100))
    # 审核结果 succ fail
    result = db.Column(db.String(20))
    # 审核成功或失败的消息
    msg = db.Column(db.String(100))
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<WechatPoi %r>' % self.id
