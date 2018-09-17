# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
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