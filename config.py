import os
class Config:
    SECRET_KEY = 'hard to guess string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 5
    UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads/')
    USER_UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads/users/')
    WECHAT_TOKEN = 'uselessproject'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost:3306/db_auto_sys'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}