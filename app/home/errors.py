# -*- coding:utf-8 -*-
from flask import render_template
from app.home import home


@home.app_errorhandler(403)
def page_not_found(e):
    return render_template('ui/403.html'), 403

@home.app_errorhandler(404)
def page_not_found(e):
    return render_template('ui/404.html'), 404

@home.app_errorhandler(500)
def page_not_found(e):
    return render_template('ui/500.html'), 500