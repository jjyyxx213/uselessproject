# -*- coding:utf-8 -*-
import os
class Config:
    SECRET_KEY = (os.getenv('SECRET_KEY_TXL') or 'hard to guess string')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 20
    POSTS_AUTH_PAGE = 150
    UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads/')
    USER_UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads/users/')
    WECHAT_TOKEN = (os.getenv('WECHAT_TOKEN_TXL') or 'null')
    WECHAT_APPID = (os.getenv('WECHAT_APPID_TXL') or 'null')
    WECHAT_APPSECRET = (os.getenv('WECHAT_APPSECRET_TXL') or 'null')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://dev:dev123@localhost:3306/db_auto_sys'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = (os.getenv('DB_URI_TXL') or 'null')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}