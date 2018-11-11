# -*- coding:utf-8 -*-
from . import wechat
from app.utils.utils import AccessToken
from hashlib import sha1
from xmltodict import parse, unparse
from time import time
from urllib2 import urlopen
from json import dumps, loads
from flask import render_template, session, redirect, request, make_response, url_for, flash, current_app


@wechat.route('/', methods=['GET', 'POST'])
def index():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    echostr = request.args.get('echostr')
    # 将token、timestamp、nonce三个参数进行字典序排序
    temp = [current_app.config['WECHAT_TOKEN'], timestamp, nonce]
    temp.sort()
    # 将三个参数字符串拼接成一个字符串进行sha1加密
    temp = "".join(temp)
    # sig是计算出来的签名结果
    sig = sha1(temp).hexdigest()
    # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
    if sig == signature:
        # 根据请求方式.返回不同的内容 ,get代表是验证服务器有效性
        if request.method == "GET":
            return echostr  # 将验证结果返给微信服务器
        # post代表微信服务器发来的消息
        else:
            resp_data = request.data
            resp_dict = parse(resp_data).get('xml')
            #### 测试消息接口
            # 如果是文本消息
            if resp_dict.get('MsgType') == 'text':
                response = {
                    "ToUserName": resp_dict.get('FromUserName'),
                    "FromUserName": resp_dict.get('ToUserName'),
                    "CreateTime": int(time()),
                    "MsgType": "text",
                    "Content": resp_dict.get('Content'),
                }
            elif resp_dict.get('MsgType') == 'voice':
                if resp_dict.get('Recognition'):
                    Recognition = resp_dict.get('Recognition')
                else:
                    Recognition = u"大声点,几把！"
                response = {
                    "ToUserName": resp_dict.get('FromUserName'),
                    "FromUserName": resp_dict.get('ToUserName'),
                    "CreateTime": int(time()),
                    "MsgType": "text",
                    "Content": Recognition,  # 把语音的消息转换成文字返回
                }
            elif resp_dict.get('MsgType') == "event":
                # subscribe订阅 unsubscribe取消订阅
                if "subscribe" == resp_dict.get("Event"):
                    response = {
                        "ToUserName": resp_dict.get("FromUserName", ""),
                        "FromUserName": resp_dict.get("ToUserName", ""),
                        "CreateTime": int(time()),
                        "MsgType": "text",
                        "Content": u"感谢您的关注！"
                    }
                    if resp_dict.get('EventKey'):
                        response["Content"] = u"可以的扫码保平安"
                elif 'SCAN' == resp_dict.get('Event'):
                    # 当用户关注过又扫描二维码的时候,会进入到这儿
                    response = {
                        "ToUserName": resp_dict.get("FromUserName", ""),
                        "FromUserName": resp_dict.get("ToUserName", ""),
                        "CreateTime": int(time()),
                        "MsgType": "text",
                        "Content": u"大兄弟关注过了扫你妹儿？"
                    }
                else:
                    response = None
            else:
                response = {
                    "ToUserName": resp_dict.get('FromUserName'),
                    "FromUserName": resp_dict.get('ToUserName'),
                    "CreateTime": int(time()),
                    "MsgType": "text",
                    "Content": u"你说什么几把？说话！打字！",
                }

            if response:
                response = {"xml": response}
                response = unparse(response)
            else:
                response = ''
            return make_response(response)

    else:
        return 'errno', 403


@wechat.route('/qrcode/get', methods=['GET'])
def qrcode_get():
    '''
    获取微信二维码
    :return: 微信二维码图片
    '''
    # 场景值ID，临时二维码时为32位非0整型，永久二维码时最大值为100000（目前参数只支持1--100000）
    scene_id = request.args.get('id', 1)
    access_token = AccessToken.get_access_token()
    url = "https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token=%s" % access_token
    params = {
        "expire_seconds": 604800,
        "action_name": "QR_SCENE",
        "action_info": {"scene": {"scene_id": scene_id}}
    }
    response = urlopen(url, data=dumps(params)).read()
    # 转换成字典
    resp_json = loads(response)

    if "errcode" in resp_json:
        raise Exception(resp_json.get("errmsg"))

    ticket = resp_json.get('ticket')

    if ticket:
        return '<img src="https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s">' % ticket
    else:
        return u'<h2>没有获取到二维码信息</h2>'


@wechat.route('/menu/add', methods=['GET'])
def menu_add():
    access_token = AccessToken.get_access_token()
    url = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s" % access_token
    params = {
        "button": [
            {
                "type": "click",
                "name": "没用1",
                "key": "USELESS1"
            },
            {
                "type": "click",
                "name": "没用2",
                "key": "USELESS2"
            },
            {
                "name": "点我",
                "sub_button": [
                    {
                        "type": "click",
                        "name": "生成二维码",
                        "key": "QRCODE_GET"
                    },
                    {
                        "type": "view",
                        "name": "搜索",
                        "url": "http://m.baidu.com/"
                    }]
            }]
    }
    response = urlopen(url, data=dumps(params, ensure_ascii=False)).read()
    # 转换成字典
    resp_json = loads(response)

    if resp_json.get("errcode")  != 0:
        raise Exception(resp_json.get("errmsg"))
    else:
        return u'<h2>菜单创建成功</h2>'
