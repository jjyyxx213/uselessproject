# -*- coding:utf-8 -*-
from . import wechat
from app.utils.utils import AccessToken
from hashlib import sha1
from xmltodict import parse, unparse
from time import time
from urllib2 import urlopen, Request
from json import dumps, loads
from flask import render_template, session, redirect, request, make_response, url_for, flash, current_app
from app.models import Customer, Oplog, WechatMedia, WechatPoi, User, Userlog, Item
from app import db
from app.decorators import permission_required, login_required
from poster import encode
from poster.streaminghttp import register_openers
import collections


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
                # 测试上传图片
                # upload_img(title=u"门店图片", img_path='venom.jpg')
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
                if resp_dict.get("Event") == "subscribe":
                    response = {
                        "ToUserName": resp_dict.get("FromUserName", ""),
                        "FromUserName": resp_dict.get("ToUserName", ""),
                        "CreateTime": int(time()),
                        "MsgType": "text",
                        "Content": u"感谢您的关注！"
                    }
                    # EventKey就是scene_id
                    if resp_dict.get("EventKey"):
                        id = (resp_dict.get("EventKey", "")).replace('qrscene_', '')
                        openid = resp_dict.get("FromUserName", "")
                        # 绑定客户和微信的关系
                        message = u"感谢您的关注"
                        if id and openid:
                            customer_info = customer_bindwechat(id, openid)
                            message = u"%s,你就是你~是颜色不一样的热翔" % customer_info["nickname"]
                        response["Content"] = message
                elif resp_dict.get('Event') == 'SCAN':
                    # 当用户关注过又扫描二维码的时候,会进入到这儿
                    id = (resp_dict.get("EventKey", "")).replace('qrscene_', '')
                    openid = resp_dict.get("FromUserName", "")
                    # 绑定客户和微信的关系
                    message = u"感谢您的关注"
                    if id and openid:
                        customer_info = customer_bindwechat(id, openid)
                        message = u"%s,你就是你~是颜色不一样的热翔" % customer_info["nickname"]
                    response = {
                        "ToUserName": resp_dict.get("FromUserName", ""),
                        "FromUserName": resp_dict.get("ToUserName", ""),
                        "CreateTime": int(time()),
                        "MsgType": "text",
                        "Content": message
                    }
                elif resp_dict.get('Event') == 'poi_check_notify':
                    # 门店创建审核事件
                    uniq_id = resp_dict.get("UniqId", "")
                    poi_id = resp_dict.get("PoiId", "")
                    result = resp_dict.get("Result", "")
                    msg = resp_dict.get("msg", "")
                    wechatpoi = WechatPoi.query.filter_by(uniqid=uniq_id).first()
                    wechatpoi.poiid = poi_id
                    wechatpoi.result = result
                    wechatpoi.msg = msg
                    db.session.add(wechatpoi)
                    db.session.commit()
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


def customer_bindwechat(id, openid):
    '''
    绑定客户和微信的关系
    '''
    # 获取客户基本信息
    access_token = AccessToken.get_access_token()
    url = "https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN" % (access_token, openid)
    response = urlopen(url).read()
    # 转换成字典
    resp_json = loads(response)

    if "errcode" in resp_json:
        raise Exception(resp_json.get("errmsg"))

    if resp_json.get("subscribe") == 0:
        raise Exception(u'该用户未关注公众号，拉取不到基本信息')

    customer = Customer.query.filter_by(id=id).first()
    customer.openid_wechat = openid
    customer.name_wechat = resp_json.get("nickname")
    db.session.add(customer)
    oplog = Oplog(
        user_id=id,
        ip=request.remote_addr,
        reason=u'绑定客户:%s,微信:%s' % (customer.name, resp_json.get("nickname"))
    )
    db.session.add(oplog)
    db.session.commit()
    return resp_json


@wechat.route('/qrcode/get', methods=['GET'])
@login_required
def qrcode_get():
    '''
    获取微信二维码
    :return: 微信二维码图片
    '''
    # 场景值ID，临时二维码时为32位非0整型，永久二维码时最大值为100000（目前参数只支持1--100000）
    scene_id = request.args.get('key', -1)
    if scene_id == -1:
        raise Exception(u"没有正确获取用户ID")
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
    data = []
    if ticket:
        data = {
            'qrcode': '<img src="https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s" style="width: 256px">' % ticket}
    else:
        data = {'qrcode': u'<h4>没有获取到二维码信息</h4>'}
    return dumps(data)


@wechat.route('/menu/add', methods=['GET'])
@login_required
def menu_add():
    # 添加菜单
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
                        "type": "view",
                        "name": "生成二维码",
                        "url": "http://jjyyxx213.ngrok.xiaomiqiu.cn/wechat/qrcode/get"
                    }]
            }]
    }
    response = urlopen(url, data=dumps(params, ensure_ascii=False)).read()
    # 转换成字典
    resp_json = loads(response)

    if "errcode" in resp_json and resp_json.get("errcode") != 0:
        raise Exception(resp_json.get("errmsg"))
    else:
        return u'<h2>菜单创建成功</h2>'


@wechat.route('/menu/del', methods=['GET'])
@login_required
def menu_del():
    # 删除菜单
    access_token = AccessToken.get_access_token()
    url = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token=%s" % access_token
    response = urlopen(url).read()
    # 转换成字典
    resp_json = loads(response)

    if "errcode" in resp_json and resp_json.get("errcode") != 0:
        raise Exception(resp_json.get("errmsg"))
    else:
        return u'<h2>菜单删除成功</h2>'


def img_upload(title, img_path):
    # 上传图片
    access_token = AccessToken.get_access_token()
    upload_url = "	https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=%s" % access_token
    # img_path = 'uploads/venom.jpg'
    img_abspath = current_app.config['UPLOAD_DIR'] + img_path
    open_file = open(img_abspath, "rb")
    params = {
        "media": open_file
    }
    '''使用poster模仿post请求'''
    register_openers()
    post_data, post_headers = encode.multipart_encode(params)
    request = Request(upload_url, post_data, post_headers)
    response = urlopen(request).read()
    # 转换成字典
    resp_json = loads(response)
    if "errcode" in resp_json:
        raise Exception(resp_json.get("errmsg"))
    else:
        url = resp_json.get('url')
        # 保存到WechatMedia
        media = WechatMedia(
            title=title,
            type="image",
            file_path=img_path,
            url=url
        )
        db.session.add(media)
        db.session.commit()
    return


@wechat.route('/poi/add', methods=['GET'])
@login_required
def poi_add():
    # 新增门店信息(未测试无权限)
    access_token = AccessToken.get_access_token()
    url = "http://api.weixin.qq.com/cgi-bin/poi/addpoi?access_token=%s" % access_token
    sid = "13333333333"
    params = {
        "business": {
            "base_info": {
                "sid": sid,
                "business_name": "大鸡儿有限公司",
                "branch_name": "大鸡儿有限公司(十堰店)",
                "province": "湖北省",
                "city": "十堰市",
                "district": "茅箭区",
                "address": "门店所在的详细街道地址",
                "telephone": "13333333333",
                "categories": ["汽车美容,贴膜"],
                "offset_type": 1,
                "longitude": 115.32375,
                "latitude": 25.097486,
                "photo_list": [{
                    "photo_url": "http://mmbiz.qpic.cn/mmbiz_jpg/F8ERAG17ZlhKz2xu19GfZA1Gicu3N3l4wgmcbqiaviaScKou6d8ln52Gf7WoXOItP99BKWicEwg9icB3cCMMovllawQ/0"
                }, {
                    "photo_url": "http://mmbiz.qpic.cn/mmbiz_jpg/F8ERAG17ZlhKz2xu19GfZA1Gicu3N3l4wgmcbqiaviaScKou6d8ln52Gf7WoXOItP99BKWicEwg9icB3cCMMovllawQ/0"
                }],
                "recommend": "洗车，贴膜，按摩",
                "special": "免费wifi，精油",
                "introduction": "我，秦始皇！打钱",
                "open_time": "9:00-17:00",
                "avg_price": 2000
            }
        }
    }
    response = urlopen(url, data=dumps(params, ensure_ascii=False)).read()
    # 转换成字典
    resp_json = loads(response)

    if "errcode" in resp_json and resp_json.get("errcode") != 0:
        raise Exception(resp_json.get("errmsg"))
    else:
        # 保存到WechatPoi
        media = WechatPoi(
            uniqid=sid,
        )
        db.session.add(media)
        db.session.commit()
        return u'<h2>门店创建成功</h2>'


@wechat.route("/wxlogin", methods=['GET', 'POST'])
def wxlogin():
    if (request.method == 'POST'):
        if not (request.json):
            res = {
                "result": 'false'
            }
            return (dumps(res))
        else:
            # 验证密码
            data = request.get_json()
            rec_phone = data['phone']
            rec_pwd = data['password']
            user = User.query.filter_by(phone=rec_phone).first()
            if user is not None and user.verify_password(rec_pwd) and user.frozen == 0:
                userlog = Userlog(
                    user_id=user.id,
                    ip=request.remote_addr,
                )
                db.session.add(userlog)
                db.session.commit()
                res = {
                    "result": 'success'
                }
            else:
                res = {
                    "result": 'pwderror'
                }
            return (dumps(res))
    else:
        res = {
            "result": 'false'
        }
        return (dumps(res))


@wechat.route("/getopenid", methods=['GET', 'POST'])
def getopenid():
    if (request.method == 'POST'):
        data = request.get_json()
        rec_code= data['code']
        url = "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code" % (current_app.config['WECHAT_APPID'],current_app.config['WECHAT_APPSECRET'], rec_code)
        response = urlopen(url).read()
        return (dumps(response))


@wechat.route('/item/list/<int:type>', methods=['GET', 'POST'])
def item_list(type=0):
    # 商品/服务列表高级权限
    if request.method == 'POST':
        # 获取json数据
        data = request.get_json()
        rec_page = data['page']
        rec_pagesize = data['pagesize']
        # 查询数据
        obj_item = Item.query
        obj_item = obj_item.filter_by(type=type).order_by(Item.addtime.desc()).paginate(page=rec_page,
               per_page=rec_pagesize,
               error_out=False)
        total = obj_item.total
        if obj_item:
            s_json = []
            for v in obj_item.items:
                dic = collections.OrderedDict()
                if v.valid == 1:
                    c_valid = '有效'
                else:
                    c_valid = '失效'
                dic["id"] = v.id
                dic["name"] = v.name
                dic["salesprice"] = str(v.salesprice) + u'元'
                dic["costprice"] = str(v.costprice) + u'元'
                dic["rewardprice"] = str(v.rewardprice) + u'元'
                dic["valid"] = c_valid
                dic["unit"] = v.unit
                dic["standard"] = v.standard
                dic["remarks"] = v.remarks
                dic["addtime"] = str(v.addtime)
                s_json.append(dic)
            res = {
                "rows": s_json,
                "total": total
            }
            return (dumps(res))
        else:
            return (None)
    return (None)
