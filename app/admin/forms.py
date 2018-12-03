# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, \
    SelectMultipleField, RadioField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Regexp, Length
from app.models import User, Auth, Role, Kvp, Category

class LoginForm(FlaskForm):
    # 超管登录表单
    name = StringField(
        label=u'账号',
        validators=[
            DataRequired(message=u'请输入管理员账号'),
        ],
        description=u'账号',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': u'请输入管理员账号',
        }
    )
    pwd = PasswordField(
        label=u'密码',
        validators=[DataRequired(message=u'请输入管理员密码')],
        description=u'密码',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': u'请输入管理员密码',
            # 'required': 'required'
        }
    )
    submit = SubmitField(
        label=u'登录',
        render_kw={
            'class': 'btn btn-primary btn-block btn-flat'
        }
    )

class AuthForm(FlaskForm):
    name = StringField(
        label=u'权限名称',
        validators=[
            DataRequired(message=u'请输入权限名称')
        ],
        description=u'权限名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入权限名称',
        }
    )
    url = StringField(
        label=u'权限地址',
        validators=[
            DataRequired(message=u'请输入权限地址')
        ],
        description=u'权限地址',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入权限地址',
        }
    )

    # 20181106 元素标识
    html_id = StringField(
        label=u'元素标识',
        validators=[
            DataRequired(message=u'请输入元素标识')
        ],
        description=u'元素标识',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入元素标识',
        }
    )

    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class RoleForm(FlaskForm):
    name = StringField(
        label=u'角色名称',
        validators=[
            DataRequired(message=u'请输入角色名称')
        ],
        description=u'角色名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入角色名称',
        }
    )

    auths = SelectMultipleField(
        label=u'权限列表',
        validators=[
            DataRequired(message=u'请选择权限')
        ],
        coerce=int,
        # 通过列表生成器生成列表
        choices=[],
        description=u'权限列表',
        render_kw={
            'class': 'form-control select2',
            'multiple': 'multiple',
            'data-placeholder': u'请选择权限(多选)',
        }
    )

    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )

    # 如果需要从数据库取值，一定要重写__init__方法，因为db对象不是全局的
    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.auths.choices = [(v.id, v.name) for v in Auth.query.order_by(Auth.name).all()]


class UserForm(FlaskForm):
    name = StringField(
        label=u'员工姓名',
        validators=[
            DataRequired(message=u'请输入姓名')
        ],
        description=u'员工姓名',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入姓名',
        }
    )
    phone = StringField(
        label=u'手机',
        validators=[
            DataRequired(message=u'请输入手机号'),
            Regexp('1[3456789]\\d{9}', message=u'手机号格式不正确'),
            Length(min=11, max=11, message=u'手机号长度不正确')
        ],
        description=u'手机',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入手机号',
        }
    )
    id_card = StringField(
        label=u'身份证',
        description=u'身份证号',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入身份证号',
        }
    )
    # jobs = StringField(
    #     label=u'工种',
    #     validators=[
    #         DataRequired(message=u'请输入工种'),
    #     ],
    #     description=u'工种',
    #     render_kw={
    #         'class': 'form-control',
    #         'placeholder': u'请输入工种',
    #     }
    # )
    salary = StringField(
        label=u'底薪',
        validators=[
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'底薪',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入底薪',
        }
    )
    pwd = PasswordField(
        label=u'员工密码',
        validators=[
            DataRequired(u'请输入密码')
        ],
        description=u'员工密码',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入密码',
        }
    )
    repwd = PasswordField(
        label=u'重复密码',
        validators=[
            DataRequired(u'请重复输入密码'),
            EqualTo('pwd', message=u'两次密码不一致')
        ],
        description=u'重复密码',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请重复输入密码',
        }
    )

    frozen = RadioField(
        label=u'员工状态',
        description=u'员工状态',
        coerce=int,
        choices=[(0, u'有效'), (1, u'冻结')],
        default=0,
    )

    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary',
        }
    )

    # 角色id
    role_id = SelectField(
        label=u'所属角色',
        coerce=int,
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择角色",
        }
    )

    # 如果需要从数据库取值，一定要重写__init__方法，因为db对象不是全局的
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(v.id, v.name) for v in Role.query.order_by(Role.name).all()]


class MscardForm(FlaskForm):
    name = StringField(
        label=u'名称',
        validators=[
            DataRequired(message=u'请输入会员卡名称')
        ],
        description=u'名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入会员卡名称',
        }
    )
    payment = StringField(
        label=u'开卡金额',
        validators=[
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'开卡金额',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入开卡金额',
        }
    )
    interval = StringField(
        label=u'有效期',
        validators=[
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'有效期',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入有效期(月)',
        }
    )
    scorerule = StringField(
        label=u'积分规则',
        validators=[
            DataRequired(message=u'请输入积分规则'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'积分规则',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入积分规则',
        }
    )
    scorelimit = StringField(
        label=u'积分上限',
        validators=[
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'积分上限',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入积分上限',
        }
    )
    valid = RadioField(
        label=u'卡状态',
        description=u'卡状态',
        coerce=int,
        choices=[(1, u'有效'), (0, u'停用')],
        default=1,
    )
    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary',
        }
    )


class MsdetailListForm(FlaskForm):
    item_id = HiddenField(
        label=u'产品/服务ID',
        description=u'产品/服务ID',
        validators=[
            DataRequired(message=u'请选择产品或服务'),
        ],
    )
    item_name = StringField(
        label=u'产品/服务',
        description=u'产品/服务',
    )
    salesprice = StringField(
        label=u'原售价',
        description=u'原售价',
    )
    discountprice = StringField(
        label=u'优惠价',
        validators=[
            DataRequired(message=u'请输入优惠价'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'优惠价',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入优惠价',
        }
    )
    quantity = StringField(
        label=u'次数',
        validators=[
            Regexp('[\d+]', message=u'请输入次数'),
        ],
        description=u'次数',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入次数',
        }
    )
    interval = StringField(
        label=u'有效期',
        validators=[
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'有效期',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入有效期(月)',
        }
    )
    #FieldList里的对象也是FormField，不知道怎么给CSRF_TOKEN赋值，关掉验证
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

class MsdetailForm(FlaskForm):
    inputrows = FieldList(
        FormField(MsdetailListForm), min_entries=1
    )
    submit = SubmitField(
        label=u'保存',
        render_kw={
            'class': 'btn btn-primary',
        }
    )

class CategoryForm(FlaskForm):
    name = StringField(
        label=u'分类名称',
        validators=[
            DataRequired(message=u'请输入分类名称')
        ],
        description=u'分类名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入分类名称',
        }
    )
    remarks = TextAreaField(
        label=u'备注',
        description=u'备注',
        render_kw={
            'class': 'form-control',
            'rows': 10
        }
    )
    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )

class ItemForm(FlaskForm):
    name = StringField(
        label=u'名称',
        validators=[
            DataRequired(message=u'请输入名称')
        ],
        description=u'名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入名称',
        }
    )
    # 类别
    cate = SelectField(
        label=u'类别',
        coerce=unicode,
        validators=[
            DataRequired(message=u'请选择类别')
        ],
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择类别",
        }
    )
    # 销售价
    salesprice = StringField(
        label=u'销售价',
        validators=[
            DataRequired(message=u'请输入优惠价'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'销售价',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入优惠价',
        }
    )
    # 成本价
    costprice = StringField(
        label=u'成本价',
        validators=[
            DataRequired(message=u'请输入成本价'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'成本价',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入成本价',
        }
    )
    # 提成
    rewardprice = StringField(
        label=u'提成',
        validators=[
            DataRequired(message=u'请输入提成'),
            Regexp('[\d+\.\d]', message=u'请输入数字'),
        ],
        description=u'成本价',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入提成',
        }
    )
    # 规格
    standard = StringField(
        label=u'规格',
        description=u'规格',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入规格',
        }
    )
    # 备注
    remarks = TextAreaField(
        label=u'备注',
        description=u'备注',
        render_kw={
            'class': 'form-control',
            'rows': 10
        }
    )
    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )
    # 单位
    unit = SelectField(
        label=u'单位',
        validators=[
            DataRequired(message=u'请选择单位')
        ],
        coerce=unicode,
        choices=[],
        render_kw={
            "class": "form-control select2",
            "data-placeholder": u"请选择计量单位",
        }
    )
    # 状态
    valid = RadioField(
        label=u'状态',
        description=u'状态',
        coerce=int,
        choices=[(1, u'有效'), (0, u'停用')],
        default=1,
    )
    # 如果需要从数据库取值，一定要重写__init__方法，因为db对象不是全局的
    def __init__(self, type, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        self.unit.choices = [(v.value, v.value) for v in Kvp.query.filter_by(type='unit').order_by(Kvp.value).all()]
        self.cate.choices = [(v.name, v.name) for v in Category.query.filter_by(type=type).order_by(Category.name).all()]

class SupplierForm(FlaskForm):
    name = StringField(
        label=u'供应商名称',
        validators=[
            DataRequired(message=u'请输入供应商名称')
        ],
        description=u'供应商名称',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入供应商名称',
        }
    )
    contact = StringField(
        label=u'联络人',
        validators=[
            DataRequired(message=u'请输入联络人')
        ],
        description=u'联络人',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入联络人',
        }
    )
    phone = StringField(
        label=u'手机号',
        description=u'手机号',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入手机号',
            'maxlength': '11'
        }
    )
    tel = StringField(
        label=u'联系电话',
        description=u'联系电话',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入联系电话',
            'maxlength': '20'
        }
    )
    qq = StringField(
        label=u'QQ',
        description=u'QQ',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入QQ',
            'maxlength': '20'
        }
    )
    address = StringField(
        label=u'地址',
        description=u'地址',
        render_kw={
            'class': 'form-control',
            'placeholder': u'请输入地址',
        }
    )
    valid = RadioField(
        label=u'状态',
        description=u'状态',
        coerce=int,
        choices=[(1, u'有效'), (0, u'停用')],
        default=1,
    )
    remarks = TextAreaField(
        label=u'备注',
        description=u'备注',
        render_kw={
            'class': 'form-control',
            'rows': 10
        }
    )
    submit = SubmitField(
        label=u'添加',
        render_kw={
            'class': 'btn btn-primary'
        }
    )