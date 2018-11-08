# -*- coding:utf-8 -*-
from time import time
from flask import current_app
from urllib2 import urlopen
from json import loads


class AccessToken(object):
    '''
    获取/保存access_token
    判断是否过期,如果没有过期,那么直接返回一次请求的access_token
    '''
    access_token = {
        "access_token": "",
        "expires_in": 7200,
        "update_time": time(),
    }

    @classmethod
    def get_access_token(cls):
        # 如果access_token不存在/access_token 过期
        if not cls.access_token.get("access_token") or \
                (time() - cls.access_token.get("update_time")) > cls.access_token.get("expires_in"):
            # 获取access_token
            url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s"\
                  % (current_app.config["WECHAT_APPID"], current_app.config["WECHAT_APPSECRET"])
            # 获取响应
            response = urlopen(url).read()
            # 转换为字典
            resp_json = loads(response)
            # 返回错误信息
            if "errcode" in resp_json:
                raise Exception(resp_json.get("errmsg"))
            else:
                # 保存
                cls.access_token["access_token"] = resp_json.get("access_token")
                cls.access_token["expires_in"] = resp_json.get("expires_in")
                cls.access_token["update_time"] = time()
                return cls.access_token.get("access_token")
        else:
            return cls.access_token.get("access_token")

