# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, \
    SelectMultipleField, RadioField, FieldList, FormField, HiddenField
from flask import session
from app.utils.baseforms import NoValidateSelectField
from wtforms.validators import DataRequired, Regexp, Length
from app.models import User, Kvp, Supplier


class LoginForm(FlaskForm):
    # 用户登录表单
    phone = StringField(
        label=u'昵称',
        validators=[
            DataRequired(message=u'请输入您的手机号'),
            Regexp('1[3458]\\d{9}', message=u'手机号格式不正确'),
            Length(min=11, max=11, message=u'手机号长度不正确')
        ],
        description=u'手机号',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': u'请输入您的手机号',
        }
    )
    pwd = PasswordField(
        label=u'密码',
        validators=[DataRequired(message=u'请输入您的密码')],
        description=u'密码',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': u'请输入您的密码',
            # 'required': 'required'
        }
    )
    submit = SubmitField(
        label=u'登录',
        render_kw={
            'class': 'btn btn-primary btn-block btn-flat'
        }
    )

# 20180913 liuqq 修改密码表单
class PwdForm(FlaskForm):
    old_pwd = StringField(
        label=u'旧密码',
        validators=[
            DataRequired(message=u'请输入旧密码')
        ],
        description=u'旧密码',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入旧密码',
        }
    )
    new_pwd = StringField(
        label=u'新密码',
        validators=[
            DataRequired(message=u'请输入新密码')
        ],
        description=u'新密码',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入新密码',
        }
    )
    re_pwd = StringField(
        label=u'确认新密码',
        validators=[
            DataRequired(message=u'请再次输入新密码')
        ],
        description=u'确认密码',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请再次输入新密码',
        }
    )

    submit = SubmitField(
        label=u'修改',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


# 20180916 liuqq 客户表单
class CustomerForm(FlaskForm):
    name = StringField(
        label=u'客户姓名',
        validators=[
            DataRequired(message=u'请输入客户姓名')
        ],
        description=u'客户姓名',
        render_kw={
            'class': 'form-control',
            'placeholder': u'客户姓名',
        }
    )

    name_wechat = StringField(
        label=u'微信昵称',
        description=u'微信昵称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'微信昵称',
        }
    )

    sex = RadioField(
        label=u'性别',
        description=u'性别',
        coerce=int,
        choices=[(1, u'男'), (2, u'女')],
        default=1
    )

    phone = StringField(
        label=u'手机号',
        validators=[
            DataRequired(message=u'请输入手机号'),
            Regexp('1[3458]\\d{9}', message=u'手机号格式不正确'),
            Length(min=11, max=11, message=u'手机号长度不正确')
        ],
        description=u'手机',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入手机号',
            'maxlength': '11'
        }
    )

    pnumber = StringField(
        label=u'车牌号',
        validators=[
            DataRequired(message=u'请输入车牌号'),
            #Regexp(u'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z]{1}[A-Z_0-9]{5}$', message=u'车牌号格式不正确'),
            Regexp(u'^[A-Z]{1}[A-Z_0-9]{5}$', message=u'车牌号格式不正确'),
            # Length(min=7, max=7, message=u'车牌号长度不正确')
        ],
        description=u'车牌号',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入车牌号',
            'maxlength': '6'
        }
    )

    vin = StringField(
        label=u'车架号',
        description=u'车架号',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入车架号',
        }
    )

    brand = StringField(
        label=u'车型品牌类型',
        validators=[
            DataRequired(message=u'请输入车型品牌类型')
        ],
        description=u'车型品牌类型',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入车型品牌类型',
        }
    )

    # 校验邮箱合法性
    email = StringField(
        label=u'电子邮箱',
        validators=[
            DataRequired(message=u'请输入电子邮箱'),
            Regexp('^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$', message=u'电子邮箱格式不正确'),
            # Email(message=u'邮箱格式错误')
        ],
        description=u'电子邮箱',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入电子邮箱',
        }
    )

    id_card = StringField(
        label=u'身份证',
        description=u'身份证号',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入身份证号',
            'maxlength': '18'
        }
    )

    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )

    # 所属客户经理
    user_id = SelectField(
        label=u'客户经理',
        coerce=int,
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择客户经理",
        }
    )

    # 如果需要从数据库取值，一定要重写__init__方法，因为db对象不是全局的
    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(v.id, v.name) for v in User.query.order_by(User.name).all()]

class StockBuyListForm(FlaskForm):
    item_id = HiddenField(
        label=u'产品/服务ID',
        description=u'产品/服务ID',
        validators=[
            DataRequired(message=u'请选择产品或服务'),
        ],
    )
    item_name = StringField(
        label=u'商品名称',
        validators=[
            DataRequired(message=u'请选择商品')
        ],
        description=u'商品名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请选择商品',
            'readonly': 'true',
        }
    )
    # 规格
    item_standard = StringField(
        label=u'规格',
        description=u'规格',
        render_kw={
            'class': 'form-control',
            'readonly' : 'true',
        }
    )
    # 仓库
    store = NoValidateSelectField(
        label=u'仓库',
        validators=[
            DataRequired(message=u'请选择仓库'),
        ],
        description=u'仓库',
        coerce=unicode,
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择仓库",
        }
    )
    # 数量
    qty = StringField(
        label=u'数量',
        validators=[
            Regexp('^(([0-9]+[\.]?[0-9]+)|[1-9])$', message=u'请输入正数'),
        ],
        description=u'数量',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入数量',
        }
    )
    # 采购单价
    costprice = StringField(
        label=u'单价',
        validators=[
            DataRequired(message=u'请输入单价'),
            Regexp('^[+]{0,1}(\d+)$|^[+]{0,1}(\d+\.\d+)$', message=u'请输入数字'),
        ],
        description=u'单价',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入单价',
        }
    )
    # 采购金额（合计）
    rowamount = StringField(
        label=u'采购金额',
        description=u'采购金额',
        render_kw={
            'class': 'form-control',
            'readonly' : 'true',
        }
    )
    #FieldList里的对象也是FormField，不知道怎么给CSRF_TOKEN赋值，关掉验证
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)
        #self.store.choices = [(v.value, v.value) for v in Kvp.query.filter_by(type='store').order_by(Kvp.value).all()]

class StockBuyForm(FlaskForm):
    inputrows = FieldList(
        FormField(StockBuyListForm), min_entries=1
    )
    # 供应商
    supplier_id = SelectField(
        label=u'供应商',
        validators=[
            DataRequired(message=u'请选择供应商'),
        ],
        coerce=int,
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择供应商",
        }
    )
    # 操作员
    user_name = StringField(
        label=u'采购员',
        render_kw={
            "class": "form-control",
            "readonly": "true",
        }
    )
    # 应付金额
    amount = StringField(
        label=u'应付金额',
        description=u'应付金额',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入应付金额',
            'readonly' : 'true'
        }
    )
    # 优惠后金额
    discount = StringField(
        label=u'优惠后金额',
        validators=[
            DataRequired(message=u'请输入优惠后金额'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'优惠后金额',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入优惠后金额',
        }
    )
    # 实际付款金额
    payment = StringField(
        label=u'本次付款',
        validators=[
            DataRequired(message=u'请输入本次付款金额'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'本次付款',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入本次付款金额',
        }
    )
    # 欠款
    debt = StringField(
        label=u'本次欠款',
        description=u'本次欠款',
        validators=[
            Regexp('^[+]{0,1}(\d+)$|^[+]{0,1}(\d+\.\d+)$', message=u'欠款不能为负数'),
        ],
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入本次欠款金额',
            'readonly': 'true',
        }
    )
    # 备注
    remarks = StringField(
        label=u'备注',
        description=u'备注',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入备注',
        }
    )
    type_switch = HiddenField(
        label=u'开关',
    )
    # 保存
    submit = SubmitField(
        label=u'确定',
        render_kw={
            'class': 'btn btn-primary',
        }
    )
    # 如果需要从数据库取值，一定要重写__init__方法，因为db对象不是全局的
    def __init__(self, *args, **kwargs):
        super(StockBuyForm, self).__init__(*args, **kwargs)
        self.supplier_id.choices = [(v.id, v.name) for v in
                                    Supplier.query.filter(Supplier.valid==1).order_by(Supplier.name).all()]

class StockBuyDebtForm(FlaskForm):
    # 应付金额
    amount = StringField(
        label=u'应付金额',
        description=u'应付金额',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入应付金额',
            'readonly' : 'true'
        }
    )
    # 优惠后金额
    discount = StringField(
        label=u'优惠后金额',
        validators=[
            DataRequired(message=u'请输入优惠后金额'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'优惠后金额',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入优惠后金额',
        }
    )
    # 实际付款金额
    payment = StringField(
        label=u'本次付款',
        validators=[
            DataRequired(message=u'请输入本次付款金额'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'本次付款',
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入本次付款金额',
        }
    )
    # 欠款
    debt = StringField(
        label=u'本次欠款',
        description=u'本次欠款',
        validators=[
            Regexp('^[+]{0,1}(\d+)$|^[+]{0,1}(\d+\.\d+)$', message=u'欠款不能为负数'),
        ],
        render_kw={
            'class': 'form-control',
            #'placeholder': u'请输入本次欠款金额',
            'readonly': 'true',
        }
    )
    # 备注
    remarks = StringField(
        label=u'备注',
        description=u'备注',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入备注',
        }
    )
    # 保存
    submit = SubmitField(
        label=u'确定',
        render_kw={
            'class': 'btn btn-primary',
        }
    )
