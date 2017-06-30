# coding: utf-8
from django.shortcuts import HttpResponseRedirect
from console.models import User
import urllib2, json, os, ConfigParser
from interface import api
import time
import json
import urllib,urllib2


config = ConfigParser.ConfigParser()
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(os.path.join(BASE_DIR, 'judy.conf'))
zeus_url = config.get('zeus', 'zeus_url')
zeus_user = config.get('zeus', 'zeus_user')
zeus_password = config.get('zeus', 'zeus_password')


def require_perm(perm='A',*args, **kwargs):
    """
    decorator for require user role in ["super", "admin", "user"]
    要求用户是某种角色 ["super", "admin", "user"]的装饰器
    """

    def _deco(func):
        def __deco(request, *args, **kwargs):
            request.session['pre_url'] = request.path
            username = request.session.get('username')

            if not username:
                return HttpResponseRedirect('/login/')

            user = User.objects.get(username=username)

            if perm == 'R':
                if user.perm == 'A':
                    return HttpResponseRedirect('/')
            elif perm == 'M':
                if user.perm in ['A', 'R']:
                    return HttpResponseRedirect('/')
            return func(request, *args, **kwargs)

        return __deco

    return _deco


def handle_container_delete(container):
    delete_status = api.remove(container.host_ip, container.container_id, container.mount_dev, container.mount_path)
    delete_status = json.loads(delete_status)
    print delete_status
    if int(delete_status['code']) != 200:
        return json.dumps(delete_status)

    # 从zeus中删除
    username = 'admin'
    password = 'w3e4r5t5'
    url = zeus_url + 'zapi/delete_asset/'
    values = {"username": zeus_user, "password": zeus_password, "ip": container.container_ip}
    values = json.dumps(values)
    req = urllib2.Request(url, values)
    try:
        response = urllib2.urlopen(req)
    except Exception as e:
        status = {"code": "500", "msg": "宙斯删除失败"}
        return json.dumps(status)
    the_page = response.read()
    if the_page == "faild":
        status = {"code": "500", "msg": "删除失败"}
        return json.dumps(status)

    # 删除容器表记录
    container.delete()

    status = {"code": "200", "msg": "删除成功"}
    return json.dumps(status)


def rest_api_delete(container):
    rest_container = api.rest_delete(container.host_ip, container.container_id)
    #print "test_sck"
    #rest_container = json.loads(rest_container)
    #return rest_status



def zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users):
    url = 'http://10.69.213.29:21900/zapi/add_cmdb/'
    #url = 'http://zeus.intra.gomeplus.com:21900/zapi/add_cmdb/'
    data = values = {"username": zeus_user, "password": zeus_password, "ip": container_ip,"hostname": hostname, "add_users": add_users}
    values_ab = json.dumps(data)
    req = urllib2.Request(url, values_ab)
    response = urllib2.urlopen(req, timeout=300)
    the_page = response.read()
    return the_page

def zeus_response02(zeus_user,zeus_password,container_ip,hostname,add_users):
    #url = 'http://10.69.213.29:219000/zapi/add_cmdb/'
    url = 'http://zeus.intra.gomeplus.com:21900/zapi/add_cmdb/'
    data = values = {"username": zeus_user, "password": zeus_password, "ip": container_ip,"hostname": hostname, "add_users": add_users}
    values_ab = json.dumps(data)
    req = urllib2.Request(url, values_ab)
    response = urllib2.urlopen(req, timeout=300)
    the_page = response.read()
    return the_page







def retry(attempt):
    def decorator(func):
        def wrapper(*args, **kw):
            att = 0
            while att < attempt:
                if 'success' == True:
                    print "aaa"
                    pass
                    #return func(*args, **kw)
                else:
                    att += 1
                    print "重试"
                    time.sleep(5)

        #pass
        return wrapper
    #pass
    return decorator
