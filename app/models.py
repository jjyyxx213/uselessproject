# -*- coding:utf-8 -*-
from datetime import datetime
from app import db
from werkzeug.security import check_password_hash

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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

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
    # 积分生成规则(积分=消费金额*积分生成规则)
    scorerule = db.Column(db.Float, default=1)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999)
    # 卡状态 (1有效；0无效)
    valid = db.Column(db.SmallInteger, default=1)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # 会员卡明细外键
    msdetails = db.relationship('Msdetail', backref='mscard')

    def __repr__(self):
        return '<Mscard %r>' % self.name

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
    freq = db.Column(db.Integer, default=1)
    # 累计消费
    summary = db.Column(db.Float, default=0)
    # 会员卡号
    vip_id = db.Column(db.Integer, db.ForeignKey('tb_vip.id'))
    # 注册时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # 消费流水外键
    billings = db.relationship('Billing', backref='customer')

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
    order_id = db.Column(db.Integer, db.ForeignKey('tb_order.id'), unique=True)
    # 销售金额
    price = db.Column(db.Float, default=0)
    # 销售积分
    score = db.Column(db.Float, default=0)
    # 支付时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Billing %r>' % self.paywith

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
    # 积分生成规则(积分=消费金额*积分生成规则)
    scorerule = db.Column(db.Float, default=1)
    # 积分限制提醒(到达额度后，提醒会员升级)
    scorelimit = db.Column(db.Float, default=9999)
    # 办理时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 截止时间
    endtime = db.Column(db.DateTime,index=True, default=datetime.utcnow)

    # 客户会员卡明细外键
    vipdetails = db.relationship('Vipdetail', backref='vip')

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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 优惠结束时间
    endtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Vipdetail %r>' % self.name

# 商品/服务类别
class Category(db.Model):
    __tablename__ = 'tb_category'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(200), nullable=False)
    # 类别(0:商品;1:服务项目)
    type = db.Column(db.SmallInteger, default=0)
    # 备注
    remarks = db.Column(db.Text)
    # 添加时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 服务/项目主表外键
    items = db.relationship('Item', backref='category')

    def __repr__(self):
        return '<Category %r>' % self.name


# 服务/项目主表 todo
class Item(db.Model):
    __tablename__ = 'tb_item'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(200), nullable=False)
    # 类别id
    cate_id = db.Column(db.Integer, db.ForeignKey('tb_category.id'))
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
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # 会员卡明细外键
    msdetails = db.relationship('Msdetail', backref='item')
    # 客户会员卡明细外键
    vipdetails = db.relationship('Vipdetail', backref='item')

    def __repr__(self):
        return '<Item %r>' % self.name

    def to_json(self):
        dict = self.__dict__
        if '_sa_instance_state' in dict:
            del dict['_sa_instance_state']
        return dict


# 销售订单主表 todo
class Order(db.Model):
    __tablename__ = 'tb_order'
    # 编号
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 名称
    name = db.Column(db.String(200), nullable=False)

    # 客户消费流水外键
    billings = db.relationship('Billing', backref='order')

    def __repr__(self):
        return '<Order %r>' % self.name


