# coding: utf-8
from django_rq import job
import time
import urllib
import urllib2, os, ConfigParser
import json, random
from ipaddr import IPNetwork
from console.models import Container, Host, Application, User
from interface.api import disk_status, docker_all
from pymail import send_email
from django.db.models import Q
from api import handle_container_delete,zeus_response01,zeus_response02


config = ConfigParser.ConfigParser()
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(os.path.join(BASE_DIR, 'judy.conf'))
zeus_url = config.get('zeus', 'zeus_url')
zeus_user = config.get('zeus', 'zeus_user')
zeus_password = config.get('zeus', 'zeus_password')


def random_user():
    users = ['zhangshuai','fujiechao','hades']
    user_choose = users[random.randint(0, len(users)-1)]
    return user_choose


def application_execute(hostname, memory, cpu, image, disk, disk_used, host, container_ip,
                        container_netmask, container_gateway, add_users, application):
    print "正在执行创建容器"
    ip_with_mask = "%s/%s" % (container_ip, container_netmask)
    # image = "docker.io/centos:6.7"
    disk_gb = "%sGB" % disk
    print hostname, memory, cpu, image, disk, disk_used, host, ip_with_mask, container_gateway
    create_status = disk_status(hostname, memory, cpu, image, disk_gb, disk_used, host,
                                ip_with_mask, container_gateway)
    # create_status = json.loads(create_status)
    print create_status
    create_status = json.loads(create_status)

    if int(create_status['code']) == 200:
        print "success"
    else:

        application.status = 4
        application.result = str(create_status)
        application.resolver = random_user()
        application.save()

        return create_status

    print "添加到容器表"
    memory = str(int(memory) / 1000000000)
    print application
    print()
    container = Container(hostname=hostname, host_ip=host, container_ip=container_ip,
                          container_id=create_status['containers_ID'],
                          mount_dev=create_status['dev_disk'], mount_path=create_status['data_disk'],
                          cpu=cpu, memory=memory, disk=disk, os=image, application=application)
    container.save()
    print container.id
    print "正在添加到Zeus"
    #url = zeus_url + 'zapi/add_cmdb/'
    #print url
    #print type(url)
    #values = {"username": zeus_user, "password": zeus_password, "ip": container_ip,"hostname": hostname, "add_users": add_users}
    #print values
    #print values
    #values = json.dumps(values)
    #print values.get('ip')
    #print type(values)
    #req = urllib2.Request(url, values)
    #response = urllib2.urlopen(req, timeout=300)
    #the_page = response.read()
    #print the_page
    one = 0
    two = 0
    #zeus_one = zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users)
    #if zeus_one != 'success':
    try:
       while (one < 3):
            if zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users) != 'success':
               zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users)
               print zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users)

               #application.status = 4
               #application.result = str(zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users))
               #application.resolver = random_user()
               #application.save()
               #delete_status = handle_container_delete(container)
               #delete_status = json.loads(delete_status)
               #handle_container_delete(container)
               #time.sleep(10)
               #print one
               #if type(one) == int:
               print one
               #   delete_status = handle_container_delete(container)
               #   delete_status = json.loads(delete_status)


                  #handle_container_delete(container)
               one += 1
               application.status = 4
               application.result_error = zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users) + "\n" + u"zeus推送失败的容器IP:%s" % container_ip
               #application.result = "IP:%s" % container_ip
               application.resolver = random_user()
               application.save()
               #return "scccess"
               #eturn  "scccess"
               #return "scccess"
               #delete_status = handle_container_delete(container)
               #delete_status = json.loads(delete_status)
               #if int(delete_status['code'] != 200):
               #   pass
            #application.status = 4
            #application.result = str(zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users))
            #application.resolver = random_user()
            #application.save()
            #delete_status = handle_container_delete(container)
            #delete_status = json.loads(delete_status)
            else:
               application.status = 3
               application.result +=  "IP:%s" % container_ip
               #application.resolver = random_user()
               application.save()
               return "scccess"


       #print application.status
       print "all"
       print one
       #return  "scccess"
       #if one == 3:
       #   application.status = 4
       #   application.result = str(zeus_response01(zeus_user,zeus_password,container_ip,hostname,add_users))
       #   application.resolver = random_user()
       #   application.save()
          #delete_status = handle_container_delete(container)
          #delete_status = json.loads(delete_status)
          #handle_container_delete(container)

       #return "error: 删除失败"
    except Exception,e:
           return e

    #application.status = 3
    #application.result +=  "IP:%s" % container_ip
               #application.resolver = random_user()
    #application.save()
    #return "scccess"


        #return  "abcd"

    #print "修改application执行状态为执行完成"
    #application.status = 3
    #application.result += "IP:%s" % container_ip
    #application.save()

    #return "success"


@job
# def handle_queue(cpu_input, memory_input, disk, os, server_num, add_users):
def handle_queue(application):
    cpu_input = application.config.cpu
    memory_input = application.config.memory[:-1]
    disk = application.config.disk[:-1]
    os = application.os
    server_num = application.server_num
    add_users = application.users_add
    username = application.username

    cpu = "0-%s" % str(int(cpu_input) - 1)
    memory = int("%s000000000" % memory_input)
    # os = "%s:latest" % os
    add_users = add_users.split(' ')
    while '' in add_users:
        add_users.remove('')

    # 分配一台宿主机
    host = assign_host(cpu_input, memory_input, disk)
    print "hsot: %s" % host
    if isinstance(host, str) and host.startswith('error'):
        application.status = 4
        application.result = host
        application.save()
        mail_to_admin.delay(application)
        return host

    for num in range(int(server_num)):
        container_ip = gen_ip(host.ip_range)
        #print 'JC'
        #print host.ip_range
        #print 'JCa'
        #print container_ip

        container_netmask = host.ip_range.split('/')[1]
        container_gateway = host.gateway
        hostname = gen_hostname(container_ip, username=username)
        exe_status = application_execute(hostname, memory, cpu, os, disk, host.disk_used, host.ip,
                                         container_ip, container_netmask, container_gateway, add_users, application)
        print exe_status

        print "正在发送邮件"
    # 执行成功，发送给申请者
        if int(application.status) == 3:
           print "3 ok"
           print application
           print "---3----ok"
           mail_to_applicant.delay(application)
           #return "success"

    # 执行失败， 发送给管理者和审核者
    #else:
        if int(application.status) == 4:
        #print
           print "4 ok"
           print application
           print "---4----ok"
           mail_to_admin.delay(application)
    return "success"
    #return "aaa"


def gen_ip(network_with_mask):
    ip_list = []
    ip_network = IPNetwork(network_with_mask)
    #print "ab"
    #print ip_network
    for ip in ip_network.iterhosts():
        ip_list.append(ip.compressed)
    #print "ccc"
    #print ip

    for ip in ip_list:
        #print ip
        #print ip_list
        #print "dd"
        if int(ip.split('.')[3]) < 13 or int(ip.split('.')[3]) > 253:
            continue
        exist_status = Container.objects.filter(container_ip=ip)
        #print "asss"
        #print exist_status
        #print "ipsss"
        #print ip
        if exist_status.count() == 0:
            #print exist_status.count()
            exist_status = Host.objects.filter(ip=ip)
            #print exist_status
            if exist_status.count() == 0:
                #print ip
                return ip
            else:
                continue
        else:
            continue
    return "error: no ip will use"


def gen_hostname(ip, username):
    ip = ip.split('.')
    hostname = "docker_%s.%s.%s_%s" % (ip[1], ip[2], ip[3], username)
    return hostname


def assign_host(cpu, memory, disk):
    host_all = Host.objects.all()
    username = 'admin'
    password = 'w3e4r5t5'
    for host in host_all:
        ip = host.ip
        # 判断docker空间是否满足要求
        #print ip
        disk_check = docker_all(ip)
        #print disk_check
        disk_check = json.loads(disk_check)
        if int(disk_check['code']) != 200:
            continue

        # 从cmdb里获取信息10.125.211.2
        url = zeus_url + 'zapi/show_asset/'
        values = {"username": zeus_user, "password": zeus_password, "ip": ip, "disk_type": host.disk_used}
        values = json.dumps(values)
        req = urllib2.Request(url, values)
        response = urllib2.urlopen(req, timeout=300)
        the_page = response.read()
        if isinstance(the_page, str) and the_page.startswith("error"):
            return the_page
        host_info = json.loads(the_page)
        print host_info

        memory_total = host_info['memory']
        disk_total = host_info['disk']
        print memory_total, disk_total

        memory_used = 4
        disk_used = 200

        containers = Container.objects.filter(host_ip=ip)

        if containers.count() != 0:
            for container in containers:
                memory_used += int(container.memory)
                disk_used += int(container.disk)

        if (memory_used + int(memory)) > int(memory_total):
            continue
        else:
            if (disk_used + int(disk)) > int(disk_total):
                continue
            else:
                return host
    return "error: 没有可分配的宿主机"


@job
def mail_to_reviewer(application):
    # 获取所有审核者
    reviewers = User.objects.filter(Q(perm='R') | Q(perm='M'))
    cc = application.leader_email
    reviewer_email = [cc]
    for r in reviewers:
        reviewer_email.append(r.email)

    container_select = Container.objects.filter(Q(application__username=application.username), Q(application__status=3))
    hosts_have = ""
    for container in container_select:
        hosts_have += container.hostname
        hosts_have += '<br>'

    subject = "judy: 服务器申请"
    body = "%s申请了%s台%s服务器，请到下面的地址进行审核 <a href='http://devdocker.intra.gomeplus.com/review/'>" \
           "审核地址</a><br>该用户已经申请的机器如下：<br>%s" % (application.username, application.server_num,
                                                application.config.name, hosts_have)

    send_status = send_email(reviewer_email, subject, body)
    return send_status


@job
def mail_to_applicant(application):
    user_email = User.objects.get(username=application.username).email
    receiver = [user_email]
    if int(application.status) == 4:
        reviewer = application.reviewer
        reviewer_email = User.objects.get(username=reviewer).email
        receiver.append(reviewer_email)

    ip_str = ""
    print application.result
    print application
    print "nosqldba1"
    ip_list = application.result.split("IP:")
    print ip_list
    for ip in ip_list:
        if ip:
            ip_str += ip
            ip_str += "<br>"

    print ip_str
    print "ip____str"
    subject = "judy: 服务器申请执行结果"
    body = "执行状态：%s<br>执行结果：分配IP如下:<br>%s" % (application.get_status_display(), ip_str)
    print receiver, subject, body

    send_status = send_email(receiver, subject, body)
    return send_status


@job
def mail_to_admin(application):
    if application.resolver:
        username = application.resolver
    else:
        username = random_user()

    random_user_email = User.objects.get(username=username).email
    receiver = [random_user_email,'fujiechao@gomeplus.com','hades@gomeplus.com','zhangshuai@gomeplus.com','zhaohong@gomeplus.com','sunfeng@gomeplus.com','gaochunpeng@gomeplus.com','huangjiechang@gomeplus.com']
    print receiver
    print "a"

    reviewer = application.reviewer
    print receiver
    print "b"
    reviewer_email = User.objects.get(username=reviewer).email
    receiver.append(reviewer_email)
    subject = "judy: 执行失败，请排查"
    body = "推送zeus失败的授权用户:%s<br>失败原因:%s<br> <a href='http://devdocker.intra.gomeplus.com/" \
           "application/detail/%s/'>详情查看</a>"\
           % (application.users_add, application.result_error, application.id)

    print receiver, subject, body
    print "acke"
    send_status = send_email(receiver, subject, body)

    return send_status


def check_ldap_user(users):
    add_users = users.split(' ')
    while '' in add_users:
        add_users.remove('')

    url = zeus_url + 'zapi/check_ldap/'
    print url
    values = {"username": zeus_user, "password": zeus_password, "users": add_users}
    values = json.dumps(values)
    req = urllib2.Request(url, values)
    try:
        response = urllib2.urlopen(req, timeout=300)
    except Exception as e:
        return "error:访问zeus接口失败"
    print response
    the_page = response.read()
    return the_page
