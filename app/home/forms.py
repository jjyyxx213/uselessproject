# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, \
    SelectMultipleField, RadioField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Regexp, Length
from app.models import User


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