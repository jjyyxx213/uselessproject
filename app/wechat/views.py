# -*- coding:utf-8 -*-
from . import wechat
from hashlib import sha1
from xmltodict import parse, unparse
from flask import render_template, session, redirect, request, url_for, flash, current_app

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
            return echostr # 将验证结果返给微信服务器
    else:
        return 'errno', 403

@wechat.route('/example', methods=['GET'])
def example():
    xml_str =  """
             <xml>
             <ToUserName><![CDATA[gh_866835093fea]]></ToUserName>
             <FromUserName><![CDATA[ogdotwSc_MmEEsJs9-ABZ1QL_4r4]]></FromUserName>
             <CreateTime>1478317060</CreateTime>
             <MsgType><![CDATA[text]]></MsgType>
             <Content><![CDATA[你好]]></Content>
             <MsgId>6349323426230210995</MsgId>
             </xml>
             """
    xml_dict = parse(xml_str).get('xml')
    print xml_dict.get('MsgType')
    return render_template('home/index.html')