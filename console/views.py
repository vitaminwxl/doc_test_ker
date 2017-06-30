# coding: utf-8
from django.shortcuts import render
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.http import HttpResponse
from models import Config, Application, Host, Container, User, Monitor,container_auditLogs
import time, json, urllib2, random, os, ConfigParser
from task import check_ldap_user, handle_queue, mail_to_reviewer, mail_to_applicant
from validateLDAPLogin import LDAPLogin
from api import require_perm, handle_container_delete,rest_api_delete
from interface import api
from django.db.models import Q
from reset_install import *
import re

config = ConfigParser.ConfigParser()
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(os.path.join(BASE_DIR, 'judy.conf'))
zeus_url = config.get('zeus', 'zeus_url')
zeus_user = config.get('zeus', 'zeus_user')
zeus_password = config.get('zeus', 'zeus_password')


# Create your views here.
def test(request):
    return render_to_response('blank.html')

def _conn_zeus(host):
    import ConfigParser
    config = ConfigParser.ConfigParser()
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    config.read(os.path.join(BASE_DIR, 'judy.conf'))
    zeus_url = config.get('zeus', 'zeus_url')
    zeus_user = config.get('zeus', 'zeus_user')
    zeus_password = config.get('zeus', 'zeus_password')
    url = zeus_url + 'zapi/show_asset/'
    values = {"username": zeus_user, "password": zeus_password, "ip": host.ip, "disk_type": host.disk_used}
    values = json.dumps(values)
    req = urllib2.Request(url, values)
    response = urllib2.urlopen(req, timeout=300)
    the_page = response.read()
    if isinstance(the_page, str) and the_page.startswith("error"):
        return the_page
    host_info = json.loads(the_page)
    return host_info
    
@require_perm('M')
def host_moni(request):
    hosts = Host.objects.all()
    host_list=[]
    for host in hosts:
        host_info = _conn_zeus(host)
        memory_used = 4
        disk_used = 200
        containers = Container.objects.filter(host_ip=host.ip)
        if containers.count() != 0:
            for container in containers:
                memory_used += int(container.memory)
                disk_used += int(container.disk)
            host_list.append(dict(ip=host.ip,total_disk=host_info['disk'],used_disk=disk_used,total_memory=host_info['memory'],used_memory=memory_used))
    return render_to_response('host_moni.html',locals())

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')
        if username and password:
            # 过滤初始密码
            if password == 'Gome123.cOm':
                error = "不被允许的密码，初始密码请先修改"
                return render_to_response('login.html', {'error': error})

            # LDAP 验证
            login_status = LDAPLogin(username, password)
            if login_status != "success":
                error = login_status
                return render_to_response('login.html', {'error': error})
            elif User.objects.filter(username=username).count() == 0:
                # elif username not in permit_user:
                error = "禁止访问，请申请该系统登录权限"
                return render_to_response('login.html', {'error': error})
            else:
                # 设置session
                request.session['username'] = username
                # 设置cookie
                # response = HttpResponseRedirect('/')
                response = HttpResponseRedirect(request.session.get('pre_url', '/'))
                response.set_cookie('username', value=username)
                user = User.objects.get(username=username)
                response.set_cookie('show_li', value=user.perm)
                return response
        else:
            error = '用户名，密码不能为空'
            return render_to_response('login.html', {'error': error})
    return render_to_response('login.html')


def logout(request):
    del request.session['username']
    return HttpResponseRedirect('/login/')


@require_perm('A')
def index(request):
    username = request.session.get('username')
    user = User.objects.get(username=username)
    print user

    if user.perm == 'M':
        application_all = Application.objects.all().order_by('-apply_time')
        #application_all = Application.objects.filter(username=username).order_by('-id')
        #print application_all

    #elif user.perm == 'A':
        #host_id = request.GET.get('host_id', '')
        #print host_id
        #return render_to_response('container_manage.html', locals())
    else:
        application_all = Application.objects.filter(username=username).order_by('-id')
        #print application_all
    return render_to_response('index.html', locals())


@require_perm('A')
def server_apply(request):
    config_all = Config.objects.all()
    if request.method == 'POST':
        username = request.session.get('username')
        server_type = request.POST.get('server_type')
        server_os = request.POST.get('server_os')
        server_num = request.POST.get('server_num')
        users = request.POST.get('users')
        leader_email = request.POST.get('leader_email')
        apply_reason = request.POST.get('apply_reason')
        print server_type, server_os, server_num, users, leader_email, apply_reason


        #try:
        # 检查输入的用户是不是LDAP用户
        status = check_ldap_user(users)
        if status.startswith('error'):
              print "$$$$$$$$$$$$$$$$$$$$"
              print status
              print "$$$$$$$$$$$$$$$$$$$$"
              return HttpResponse(status)
        print "!!!!!!!!!!!!!!!!!"
        config_get = Config.objects.get(id=server_type)
        application = Application(username=username, config=config_get, os=server_os,
                                  server_num=server_num, users_add=users, status=1,
                                  leader_email=leader_email, apply_reason=apply_reason)
        application.save()
        print "@@@@@@@@@@@@@@@@@@@@"
        status = mail_to_reviewer.delay(application)
        print status

        #except Exception,e:
        #       print e
        return HttpResponse(u'送审成功')
    return render_to_response('server_apply.html', locals())


@require_perm('M')
def config_add(request):
    if request.method == 'POST':
        config_name = request.POST.get('config_name')
        cpu = request.POST.get('cpu')
        memory = request.POST.get('memory')
        disk = request.POST.get('disk')
        description = request.POST.get('description')
        print config_name, cpu, memory, disk, description
        server_config = Config(name=config_name, cpu=cpu, memory=memory, disk=disk, description=description)
        server_config.save()

        return HttpResponse('添加成功')

    return render_to_response('config_add.html')


@require_perm('M')
def config_list(request):
    config_all = Config.objects.all()
    return render_to_response('config_list.html', locals())


@require_perm('M')
def config_edit(request, config_id):
    config = Config.objects.get(id=config_id)
    if request.method == 'POST':
        config_name = request.POST.get('config_name')
        cpu = request.POST.get('cpu')
        memory = request.POST.get('memory')
        disk = request.POST.get('disk')
        description = request.POST.get('description', '')

        config.name = config_name
        config.cpu = cpu
        config.memory = memory
        config.disk = disk
        config.description = description
        config.save()
        return HttpResponse('修改成功')

    return render_to_response('config_edit.html', locals())


@require_perm('M')
def config_delete(request):
    config_id = request.POST.get('config_id')
    config = Config.objects.get(id=config_id)
    config.delete()
    return HttpResponse('删除成功')


@require_perm('R')
def review(request):
    username = request.session.get('username')
    user = User.objects.get(username=username)
    application_review = Application.objects.filter(status=1)
    q1 = Application.objects.filter(reviewer=user)
    reviewed_app = q1.filter(status__gte=2)
    return render_to_response('review.html', locals())


@require_perm('R')
def review_checked(request):
    app_id = request.POST.get('app_id')
    username = request.session.get('username')
    application = Application.objects.get(id=app_id)
    user = User.objects.get(username=username)

    # cpu = application.config.cpu
    # memory = application.config.memory[:-1]
    # disk = application.config.disk[:-1]
    # os = application.os
    # server_num = application.server_num
    # add_users = application.users_add

    # 判断是否已经审核
    if int(application.status) > 1:
        return HttpResponse(u'该申请已经被审核过')

    # 修改状态
    application.status = 2
    application.reviewer = user
    application.save()

    # status = handle_queue.delay(cpu, memory, disk, os, server_num, add_users)
    # 调用队列执行操作
    handle_queue.delay(application)
    # if status.startswith("error"):
    #     application.status = 4
    #     application.result = status
    #     application.save()
    # print status

    return HttpResponse(u'审批完成')


@require_perm('R')
def review_reject(request):
    app_id = request.POST.get('app_id')
    reject_reason = request.POST.get('reject_reason')
    username = request.session.get('username')
    user = User.objects.get(username=username)
    application = Application.objects.get(id=app_id)

    # 判断是否已经审核
    if int(application.status) > 1:
        return HttpResponse(u'该申请已经被审核过')

    application.reviewer = user
    application.result = reject_reason
    application.status = 5
    application.save()
    # Application.objects.filter(id=app_id).update(status=5)
    # application = Application.objects.get(id=app_id)
    mail_to_applicant.delay(application)
    return HttpResponse(u'驳回成功')


@require_perm('M')
def host_manage(request):
    host_all = Host.objects.all()
    return render_to_response('host_manage.html', locals())


@require_perm('M')
def host_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        ip = request.POST.get('ip')
        netmask = request.POST.get('netmask')
        gateway = request.POST.get('gateway')
        disk = request.POST.get('disk')
        ip_range = request.POST.get('ip_range')
        print name, ip, netmask, gateway, disk

        host = Host(name=name, ip=ip, netmask=netmask, gateway=gateway, disk_used=disk, ip_range=ip_range)
        host.save()
        return HttpResponse('添加成功')
    return render_to_response('host_add.html', locals())


@require_perm('M')
def host_edit(request, host_id):
    host = Host.objects.get(id=host_id)
    old_ip = host.ip
    if request.method == 'POST':
        name = request.POST.get('name')
        new_ip = request.POST.get('ip')
        netmask = request.POST.get('netmask')
        gateway = request.POST.get('gateway')
        disk = request.POST.get('disk')
        ip_range = request.POST.get('ip_range')

        host.name = name
        host.ip = new_ip
        host.netmask = netmask
        host.gateway = gateway
        host.ip_range = ip_range
        host.disk_used = disk
        host.save()

        # 判断IP是否变化，如果变化，修改container表中的宿主机IP
        if old_ip != new_ip:
            Container.objects.filter(host_ip=old_ip).update(host_ip=new_ip)

        return HttpResponse('编辑成功')

    return render_to_response('host_edit.html', locals())


@require_perm('M')
def host_delete(request):
    host_id = request.POST.get('host_id')
    host = Host.objects.get(id=host_id)
    host.delete()
    return HttpResponse('删除成功')





@require_perm('A','R')
def container_manage(request):
    username = request.session.get('username')
    #user = User.objects.get(username=username)
    host_id = request.GET.get('host_id', '')

    #print host_id
    host_all = Host.objects.all()

    ip_all = []
    for host in host_all:
        #print host
        ip_all.append(host.ip)
    container_all_status = []
    for ip in ip_all:
        container_status = api.status_info(ip)
        container_status = json.loads(container_status)
        #print container_status
        #print type(container_status['code'])

        if int(container_status['code']) == 200:
            container_all_status.extend(container_status['message'])
    # print container_all_status
    status_format = {}
    for item in container_all_status:
        status_format[item['ID']] = item['Status']
    # print status_format

    if host_id:
        ip = Host.objects.get(id=host_id).ip
        #print ip
        #print "aaa"
        container_all = Container.objects.filter(host_ip=ip)


        #print container_all
        #container_all = Container.objects.order_by("-id")
        #print container_all
    else:
        #if username:
        #for i in Container.objects.all():
        #    if str(i.application.username) == str(username):
        for i in User.objects.filter(username=str(username)):
           if str(i.perm) == 'A' or str(i.perm) == 'R':
              container_all = []
              container = Container.objects.all()
              for i in container:
                if i.application.username == str(username):
                   container_all.append(i)
           elif str(i.perm) == 'M':
              container_all = Container.objects.all()
        #elif str(request.GET.get('show_li')) == 'M':
             #container = Container.objects.all()
    return render_to_response('container_manage.html', locals())



@require_perm('A','R')
def auditLogs_manage(request):
    username = request.session.get('username')
    user = User.objects.get(username=username)
    container_all = []
    #for i in User.objects.filter(username=str(username)):
    if user.perm == 'A' or user.perm == 'R':

       #print
       #container = container_auditLogs.objects.filter(login_user=username).order_by("-id")
       container = container_auditLogs.objects.all().order_by("-unix_time")
       for i in container:
           #print i
       #    if i.login_user == str(username):
           if i.login_user == str(username) or re.search(str(username),str(i.hostname)) != None:
              container_all.append(i)
       #for i in container_all:
       #    print i.unix_time
       #return render_to_response('container_autilogs.html', locals())
       #return render_to_response('container_autilogs.html', locals())
    elif user.perm == 'M':
       container_all = container_auditLogs.objects.all().order_by('-id')
           #application_all = Application.objects.filter(username=username).order_by('-id')
           #for i in container_all:
           #    print i.unix_time
    #for i in container_all:
    #    print i.unix_time
    return render_to_response('container_autilogs.html', locals())



@require_perm('A','R')
def container_start(request):
    username = request.session.get('username')
    container_id = request.POST.get('container_id')
    container = Container.objects.get(id=container_id)
    host_ip = container.host_ip
    host = Host.objects.filter(ip=host_ip)[0]
    netmask = host.ip_range.split("/")[1]
    gateway = host.gateway
    ip_with_mask = "%s/%s" % (container.container_ip, netmask)
    start_status = api.start(container.host_ip, container.container_id, ip_with_mask,
                             gateway, container.mount_dev, container.mount_path)
    start_status = json.loads(start_status)
    if start_status['code'] == 200 or start_status['code'] == 201:
        container_auditLog = container_auditLogs(login_user=str(username),host_ip=container.container_ip,hostname=container.hostname,action=0)
        container_auditLog.save()
        return HttpResponse("启动成功")
    else:
        return HttpResponse("启动失败：%s" % start_status['status'])


@require_perm('A','R')
def container_stop(request):
    username = request.session.get('username')
    container_id = request.POST.get('container_id')
    container = Container.objects.get(id=container_id)
    stop_status = api.stop(container.host_ip, container.container_id)
    stop_status = json.loads(stop_status)
    if stop_status['code'] == 200:
        #print username,container.host_ip,container.hostname
        #print type(username)
        #print type(container.host_ip)
        #print type(container.hostname)
        container_auditLog = container_auditLogs(login_user=str(username),host_ip=container.container_ip,hostname=container.hostname,action=1)
        container_auditLog.save()
        return HttpResponse("停止成功")
    else:
        return HttpResponse("停止失败: %s" % stop_status['stop_status'])


@require_perm('A','R')
def container_delete(request):
    username = request.session.get('username')
    container_id = request.POST.get('container_id')
    #print container_id
    container = Container.objects.get(id=container_id)

    # 删除容器
    print container.host_ip, container.container_id, container.mount_dev, container.mount_path
    # delete_status = api.remove(container.host_ip, container.container_id, container.mount_dev, container.mount_path)
    # delete_status = json.loads(delete_status)
    # print delete_status
    # if int(delete_status['code']) != 200:
    #     return HttpResponse("删除失败")
    #
    # # 从zeus中删除
    # username = 'admin'
    # password = 'w3e4r5t5'
    # url = 'http://10.125.211.2:3344/zapi/delete_asset/'
    # values = {"username": username, "password": password, "ip": container.container_ip}
    # values = json.dumps(values)
    # req = urllib2.Request(url, values)
    # response = urllib2.urlopen(req)
    # the_page = response.read()
    # print the_page
    # if the_page == "faild":
    #     return HttpResponse("删除失败")
    #
    # # 删除容器表记录
    # container.delete()
    delete_status = handle_container_delete(container)
    delete_status = json.loads(delete_status)
    try:
      container_auditLog = container_auditLogs(login_user=str(username),host_ip=container.container_ip,hostname=container.hostname,action=2)
      container_auditLog.save()
    except Exception,e:
      print e
    if int(delete_status['code']) != 200:
        return HttpResponse("删除失败:%s" % delete_status['msg'])

    return HttpResponse("删除成功")


#@require_perm('M')
@require_perm('A','R')
def container_reset(request):
    username = request.session.get('username')
    container_id = request.POST.get('container_id')
    container_all = Container.objects.filter(id="%s" % container_id)
    for container in container_all:
        host_name = container.hostname
        memory_total = container.memory + "000000000"
        cpu_total = container.cpu
        disk_size = int(container.disk)
        mount_path = container.mount_path
        host_ip = container.host_ip
        container_ip = container.container_ip
        container_ip_with_mask = container.container_ip + "/24"
        str1 = []
        container_gw = container_ip.split('.')
        container_gw[len(container_gw) - 1] = '254'
        container_gw = '.'.join(container_gw)
        #print container_ip
        image = Container.objects.filter(container_ip="%s" % container_ip)
        for image_all in image:
            pass
        #print image_all.container_id
        images = image_all.os
        #print images
        #        images = 'centos6.7'
        mount_dev = container.mount_dev
        mount_path = container.mount_path
        add_users = container.application.users_add
        add_users = add_users.split(' ')
        # print host_name,container_ip
        while '' in add_users:
            #     print add_users
            add_users.remove('')

        try:
          #停止容器
          stop_status = api.stop(image_all.host_ip, image_all.container_id)
          stop_status = json.loads(stop_status)


          #删除容器
          delete_status = rest_api_delete(container)
          print delete_status

        except Exception,e:
          print e
          pass

        # 创建容器
        create_status = container_create(host_name, memory_total, cpu_total, images, disk_size,mount_path, host_ip,
                                         container_ip, container_gw)

        create_status = json.loads(create_status)
        #print create_status
        cid = create_status["containers_ID"]
        #print cid
        ids = [cid]
        #        print cid
        #        print create_status

        # 启动容器
        #        print host_ip, cid, container_ip, container_gw, mount_dev, mount_path
        start_status = start(host_ip, cid, container_ip_with_mask, container_gw, mount_dev, mount_path)
        #        print start_status
        # 更新Container表
        container.container_id = cid
        container.save()

        # 从zeus中删除
        url = zeus_url + 'zapi/delete_asset/'
        values = {"username": zeus_user, "password": zeus_password, "ip": container_ip}
        values = json.dumps(values)
        req = urllib2.Request(url, values)
        response = urllib2.urlopen(req, timeout=300)
        the_page = response.read()
        #       print the_page
        if the_page == "faild":
            fail_container.append(container.container_ip)
            continue

        # 推送用户
        url = zeus_url + 'zapi/add_cmdb/'
        values = {"username": zeus_user, "password": zeus_password, "ip": container_ip,
                  "hostname": host_name, "add_users": add_users}
        values = json.dumps(values)
        req = urllib2.Request(url, values)
        response = urllib2.urlopen(req, timeout=300)
        the_page = response.read()
        container_auditLog = container_auditLogs(login_user=str(username),host_ip=container.container_ip,hostname=container.hostname,action=3)
        container_auditLog.save()
        #      print "aaa"
        #      print the_page

        return HttpResponse("容器重置成功!")


@require_perm('A','R')
def container_detail(request, cid):
    #print request.session['show_li']
    #print request
    #print request.POST.get('show_li')
    #print request.COOKIES['show_li']

    username = request.session.get('username')
    #print username
    container = Container.objects.get(id=cid)
    print type(container.container_ip)
    container_auditLog = container_auditLogs(login_user=str(username),host_ip=container.container_ip,hostname=container.hostname,action=4)
    container_auditLog.save()
    return render_to_response('container_detail.html', locals())


@require_perm('A','R')
def container_batch_handle(request):
    username = request.session.get('username')
    option = request.POST.get('option')
    containers = request.POST.get('containers')
    containers = json.loads(containers)
    print containers
    print "aaaccc"
    fail_container = []
    ips = ""
    ip_hostname = ""
    for cid in containers:
        container = Container.objects.get(id=cid)
        host_ip = container.host_ip
        host = Host.objects.filter(ip=host_ip)[0]
        netmask = host.ip_range.split("/")[1]
        gateway = host.gateway
        ip_with_mask = "%s/%s" % (container.container_ip, netmask)
        if option == 'start':

            start_status = api.start(container.host_ip, container.container_id, ip_with_mask,gateway, container.mount_dev, container.mount_path)
            print "bbb"
            start_status = json.loads(start_status)
            print "eeee"
            if start_status['code'] == 200 or start_status['code'] == 201:
                ips += ","
                ips += container.container_ip
                ip_hostname += ","
                ip_hostname += container.hostname
                status_type = 5
                pass
            else:
                fail_container.append(container.container_ip)

        if option == 'stop':
            stop_status = api.stop(container.host_ip, container.container_id)
            stop_status = json.loads(stop_status)
            if stop_status['code'] == 200:
               ips += ","
               ips += container.container_ip
               ip_hostname += ","
               ip_hostname += container.hostname
               status_type = 6
               pass
            else:
                fail_container.append(container.container_ip)
        if option == 'reset':
            container_all = Container.objects.filter(id="%s" % cid)
            for container in container_all:
                host_name = container.hostname
                memory_total = container.memory + "000000000"
                cpu_total = container.cpu
                disk_size = int(container.disk)
                mount_path = container.mount_path
                host_ip = container.host_ip
                container_ip = container.container_ip
                container_ip_with_mask = container.container_ip + "/24"
                str1 = []
                container_gw = container_ip.split('.')
                container_gw[len(container_gw) - 1] = '254'
                container_gw = '.'.join(container_gw)
                print container_ip
                #image = Application.objects.filter(result="IP:%s" % container_ip)
                image = Container.objects.filter(container_ip="%s" % container_ip)
                #print image
                for image_all in image:
                    #print image_all.os
                    pass
                #print "tttddd"
                #print images_all
                images = image_all.os
                print images
                #print "cccaaa"
                #        images = 'centos6.7'
                mount_dev = container.mount_dev
                mount_path = container.mount_path
                add_users = container.application.users_add
                add_users = add_users.split(' ')
                # print host_name,container_ip
                while '' in add_users:
                    #     print add_users
                    add_users.remove('')

                try:
                  #停止容器
                  stop_status = api.stop(image_all.host_ip, image_all.container_id)
                  stop_status = json.loads(stop_status)


                  #删除容器
                  delete_status = rest_api_delete(container)
                  print delete_status

                except Exception,e:
                  pass


                # 创建容器
                create_status = container_create(host_name, memory_total, cpu_total, images, disk_size, mount_path,
                                                 host_ip, container_ip, container_gw)
                create_status = json.loads(create_status)
                cid = create_status["containers_ID"]
                ids = [cid]

                # 启动容器
                start_status = start(host_ip, cid, container_ip_with_mask, container_gw, mount_dev, mount_path)
                # 更新Container表
                container.container_id = cid
                container.save()

                # 从zeus中删除
                url = zeus_url + 'zapi/delete_asset/'
                values = {"username": zeus_user, "password": zeus_password, "ip": container_ip}
                values = json.dumps(values)
                req = urllib2.Request(url, values)
                response = urllib2.urlopen(req, timeout=300)
                the_page = response.read()
                if the_page == "faild":
                    fail_container.append(container.container_ip)
                    continue

                    # 推送用户
                url = zeus_url + 'zapi/add_cmdb/'
                values = {"username": zeus_user, "password": zeus_password, "ip": container_ip,
                          "hostname": host_name, "add_users": add_users}
                values = json.dumps(values)
                req = urllib2.Request(url, values)
                response = urllib2.urlopen(req, timeout=300)
                the_page = response.read()
                ips += ","
                ips += container.container_ip
                ip_hostname += ","
                ip_hostname += container.hostname
                status_type = 8

        if option == 'delete':
            delete_status = api.remove(container.host_ip, container.container_id, container.mount_dev,
                                       container.mount_path)
            delete_status = json.loads(delete_status)
            print delete_status
            if int(delete_status['code']) != 200:
                fail_container.append(container.container_ip)
                continue

            # 从zeus中删除
            url = zeus_url + 'zapi/delete_asset/'
            values = {"username": zeus_user, "password": zeus_password, "ip": container.container_ip}
            values = json.dumps(values)
            req = urllib2.Request(url, values)
            response = urllib2.urlopen(req, timeout=300)
            the_page = response.read()
            print the_page
            if the_page == "faild":
                fail_container.append(container.container_ip)
                continue

            # 删除容器表记录
            container.delete()
            ips += ","
            ips += container.container_ip
            ip_hostname += ","
            ip_hostname += container.hostname
            status_type = 7

    if fail_container:
        return HttpResponse("操作失败：%s" % fail_container)
    else:
        ips_all = ips.strip(',').strip('\n')
        ip_hostname_all = ip_hostname.strip(',').strip('\n')
        #print ips_all
        #print "ccc"
        print ip_hostname_all
        #print ip_hostname_all,type(ip_hostname_all)
        try:
          container_auditLog = container_auditLogs(login_user=str(username),host_ip=ips_all,hostname=str(ip_hostname_all),action=status_type)
          container_auditLog.save()
          return HttpResponse("操作成功")
        except Exception,e:
          pass
          print "nosqloracler"
          print e
          return HttpResponse("操作成功")
        #  return "数据库无法写入,报错:{0}".format(e)


@require_perm('M')
def user_manage(request):
    user_all = User.objects.all()
    return render_to_response('user_manage.html', locals())


@require_perm('M')
def user_add(request):
    user_perm = {"A": u'申请者', "R": u'审核者', "M": u'管理者'}
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        perm = request.POST.get('perm')
        print username, email, perm

        user_exist = User.objects.filter(username=username)
        if user_exist.count() != 0:
            return HttpResponse('该用户已经存在')

        user = User(username=username, email=email, perm=perm)
        user.save()
        return HttpResponse('用户添加成功')
    return render_to_response('user_add.html', locals())


@require_perm('M')
def user_edit(request, host_id):
    user = User.objects.get(id=host_id)
    user_perm = {"A": u'申请者', "R": u'审核者', "M": u'管理者'}
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        perm = request.POST.get('perm')
        print username, email, perm

        user.username = username
        user.email = email
        user.perm = perm
        user.save()

        return HttpResponse('用户编辑成功')

    return render_to_response('user_edit.html', locals())


@require_perm('M')
def user_delete(request):
    user_id = request.POST.get('user_id')
    user = User.objects.get(id=user_id)
    user.delete()
    return HttpResponse('用户删除成功')


@require_perm('A')
def application_detail(request, app_id):
    application = Application.objects.get(id=app_id)
    return render_to_response('server_detail.html', locals())


@require_perm('M')
def application_retry(request):
    app_id = request.POST.get('app_id')
    username = request.session.get('username')
    application = Application.objects.get(id=app_id)
    user = User.objects.get(username=username)

    # 判断是否已经重新执行
    if int(application.status) != 4:
        return HttpResponse(u'该申请已经在执行')

    # 修改状态
    application.status = 2
    # 清除失败结果
    application.result = ""

    application.save()

    # 调用队列执行操作
    handle_queue.delay(application)

    return HttpResponse(u'重新执行操作成功')


@require_perm('M')
def monitor(request):
    container_first = Container.objects.all()[0]
    hostname = container_first.hostname
    redirect_url = "/monitor/%s/" % hostname
    return HttpResponseRedirect(redirect_url)


@require_perm('M')
def monitor_host(request, hostname):
    container_all = Container.objects.all()
    return render_to_response('monitor.html', locals())


@require_perm('M')
def get_data(request):
    cid = request.GET.get('hostname')
    item = request.GET.get('item')
    aaa = Monitor.objects.filter(Q(hostname=cid) & Q(item=item))
    monitor_value = []
    for item in aaa:
        unix_time = int(item.unix_time) * 1000
        value = float(item.value)
        monitor_value.append([unix_time, value])

    monitor_value = json.dumps(monitor_value)

    # test_value = [[1463456960000, 7], [1463456961000, 56], [1463456962000, 56], [1463456963000, 87], [1463456964000, 27], [1463456965000, 90], [1463456966000, 18], [1463456967000, 35], [1463456968000, 94], [1463456969000, 40], [1463456970000, 10], [1463456971000, 29], [1463456972000, 85], [1463456973000, 53], [1463456974000, 97], [1463456975000, 87], [1463456976000, 50], [1463456977000, 98], [1463456978000, 44], [1463456979000, 98], [1463456980000, 70], [1463456981000, 53], [1463456982000, 41], [1463456983000, 23], [1463456984000, 38], [1463456985000, 99], [1463456986000, 59], [1463456987000, 66], [1463456988000, 54], [1463456989000, 16], [1463456990000, 40], [1463456991000, 90], [1463456992000, 80], [1463456993000, 38], [1463456994000, 46], [1463456995000, 27], [1463456996000, 69], [1463456997000, 54], [1463456998000, 57], [1463456999000, 53], [1463457000000, 53], [1463457001000, 11], [1463457002000, 50], [1463457003000, 47], [1463457004000, 5], [1463457005000, 53], [1463457006000, 58], [1463457007000, 46], [1463457008000, 12], [1463457009000, 35], [1463457010000, 68], [1463457011000, 66], [1463457012000, 89], [1463457013000, 23], [1463457014000, 8], [1463457015000, 75], [1463457016000, 85], [1463457017000, 92], [1463457018000, 12], [1463457019000, 19], [1463457020000, 53], [1463457021000, 15], [1463457022000, 51], [1463457023000, 94], [1463457024000, 83], [1463457025000, 44], [1463457026000, 32], [1463457027000, 73], [1463457028000, 69], [1463457029000, 95], [1463457030000, 88], [1463457031000, 75], [1463457032000, 91], [1463457033000, 15], [1463457034000, 4], [1463457035000, 80], [1463457036000, 46], [1463457037000, 42], [1463457038000, 5], [1463457039000, 47], [1463457040000, 98], [1463457041000, 55], [1463457042000, 41], [1463457043000, 41], [1463457044000, 55], [1463457045000, 11], [1463457046000, 33], [1463457047000, 72], [1463457048000, 31], [1463457049000, 61], [1463457050000, 19], [1463457051000, 20], [1463457052000, 90], [1463457053000, 17], [1463457054000, 45], [1463457055000, 25], [1463457056000, 61], [1463457057000, 35], [1463457058000, 74]]
    # test_value = json.dumps(test_value)
    return HttpResponse(monitor_value)


@require_perm('M')
def get_dynamic_data(request):
    cid = request.POST.get('hostname')
    item = request.POST.get('item')
    print cid, item

    latest_value = Monitor.objects.filter(Q(hostname=cid) & Q(item=item)).order_by('-id')[0]
    unix_time = int(latest_value.unix_time) * 1000
    value = latest_value.value

    # time_now = int(str(time.time()).split(".")[0] + "000")
    # value = random.randint(1, 100)
    aaa = "%s,%s" % (unix_time, value)
    print aaa
    return HttpResponse(aaa)
