# -*- coding:utf-8 -*-
from wtforms import SelectField

# 重写SelectField，动态列表不做pre_validate
class NoValidateSelectField(SelectField):
    def pre_validate(self, form):
        pass