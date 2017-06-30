#!/usr/bin/env python
# encoding: utf-8
import os, sys
sys.path.append('/gomeo2o/htdocs/judy')
os.environ['DJANGO_SETTINGS_MODULE'] = 'judy.settings'
import paramiko
# import subprocess
# import os,sys
import fileinput
import time
import pexpect
from docker import Client
import docker
import threading
import socket
socket.setdefaulttimeout(9.0)
import json
import urllib, urllib2
import re, ConfigParser
from console.models import Container, Application,Host
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import render_to_response
#from api.models import dockerdata
reload(sys)
sys.setdefaultencoding("utf-8")

from django.conf import settings

zeusadmin_pwd = settings.ZEUSADMIN_PWD


config = ConfigParser.ConfigParser()
BASE_DIR = '/gomeo2o/htdocs/judy'
config.read(os.path.join(BASE_DIR, 'judy.conf'))
zeus_url = config.get('zeus', 'zeus_url')
zeus_user = config.get('zeus', 'zeus_user')
zeus_password = config.get('zeus', 'zeus_password')

####容器创建新代码####
def container_create(host_name, memory_total,cpu_total,images,disk_size,mount_path,host_ip,container_ip,container_gw):

    #disk_size_all = disk_size.replace('GB','')
    cli = docker.Client(base_url='http://{0}:5555'.format(host_ip),version='1.21')
    args_centos6 = {

            "hostname":"{0}".format(host_name),
            "name":"{0}".format(host_name),
            "tty":True,
            "stdin_open":True,
            "command":"/usr/bin/supervisord",
    }
    args_centos7 = {

            "hostname": "{0}".format(host_name),
            "name": "{0}".format(host_name),
            "tty": True,
            "stdin_open": True,
    }

    binds=[
        "{0}:/gomeo2o".format(mount_path)
    ]
    #hostconfig_all = cli.create_host_config(
    #        binds=binds,
    #        mem_limit=memory_total,
    #        memswap_limit=memory_total,
            #cpuset_cpus='0-1',
    #        network_mode="none",
    #        privileged =True,
   #)

    #print type(hostconfig_all)

    print "abcs"
    hostconfig = {'Binds':binds,'Memory':int(memory_total),'MemorySwap':int(memory_total),'CpusetCpus':cpu_total,'NetworkMode': 'none','Privileged': True}
    #print type(hostconfig)
    try:
        if images == "centos6.7":
            a = cli.create_container(image=images, host_config=hostconfig, **args_centos6)
        elif images == "centos7":
            a = cli.create_container(image=images, host_config=hostconfig, **args_centos7)
        print a
    except Exception,e:
        print e
    #dev_disk = "/dev/%s/%s" %(disk_type,host_name)
    #data_disk = "/docker_data/%s/%s" %(disk_type,host_name)
    return (json.dumps({'code':200,'host_name':host_name,'containers_ID':a.get('Id')},indent=4))







#def container_create(host_name, memory_total,cpu_total,images,disk_size,disk_type_name,host_ip,container_ip,container_gw):
#    disk_type = "cloud_" + disk_type_name
#    json_data = '''
#         {
#
#            "Hostname":"%s",
#            "HostConfig": {"Memory":%s,"MemorySwap":%s,"Binds": ["/docker_data/%s/%s:/gomeo2o"],"NetworkMode": "none","CpusetCpus": "%s","Privileged": true},
#            "AttachStdin":false,
#            "AttachStdout":true,
#            "AttachStderr":true,
#            "PortSpecs":null,
#            "Tty":true,
#            "OpenStdin":false,
#            "StdinOnce":false,
#            "Env":["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
#            "Cmd":["/usr/bin/supervisord"],
#            "Dns":null,
#            "Config": {"Entrypoint": ["/usr/bin/supervisord"]},
#            "Image":"%s"
#           }
#         ''' % (host_name, memory_total, memory_total,disk_type,host_name,cpu_total,images)


#    headers = {'Content-type': 'application/json', 'Accept': 'charset=utf-8'}
#    req = urllib2.Request("http://%s:5555/containers/create" % (host_ip), json_data, headers)
#    response = urllib2.urlopen(req)
#    a = response.read()
#
#    dev_disk = "/dev/%s/%s" %(disk_type,host_name)
#    data_disk = "/docker_data/%s/%s" %(disk_type,host_name)
#
#    return (json.dumps({'code':200,'host_name':host_name,'containers_ID':json.loads(a).get('Id'),'dev_disk':dev_disk,'data_disk':data_disk},indent=4))


#print disk_status('python-docker190', int('4000000000'),'0-3','centos6.7','100GB','sdd','10.69.111.11','10.69.112.13/24','10.69.112.254')


def stop(host_ip,ids):
#    print type(ids)
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'charset=utf-8'}
        req_stop = urllib2.Request("http://%s:5555/containers/%s/stop" %(host_ip,ids),'{}',headers)
        response_stop = urllib2.urlopen(req_stop)
        out_stop = response_stop.read()
        return (json.dumps({'code':200,'stop_status':'Stop Success'},sort_keys=True,indent=4))

    except:
        return (json.dumps({'code':500,'stop_status':'Stop failure'},sort_keys=True,indent=4))
#print stop('10.125.111.12','d8059bb05c7937168f55d9d04743d31d7d8315d164daa434e23d15c1a86da723')

def start(host_ip,ids,container_ip,container_gw,mount_dev,mount_path):
    test_str = 'sudo pipework em2 -i eth2 %s %s@%s && sudo mount %s %s' % (ids,container_ip,container_gw,mount_dev,mount_path)
    print test_str
    ssh_c = pexpect.spawn('ssh -p21987  zeusadmin@%s "%s"' % (host_ip, 'sudo pipework em2 -i eth2 %s %s@%s && sudo mount %s %s' % (ids,container_ip,container_gw,mount_dev,mount_path)))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'charset=utf-8'}
        req_start = urllib2.Request("http://%s:5555/containers/%s/start" %(host_ip,ids), '{}', headers)
        response_start = urllib2.urlopen(req_start)
        out_start = response_start.read()

        i = ssh_c.expect(['password:', 'continue connecting (yes/no)?'])

        if i == 0:
            print "i=0"
            ssh_c.sendline(zeusadmin_pwd)
        elif i == 1:
            ssh_c.sendline('yes\n')
            ssh_c.expect('password: ')
            ssh_c.sendline(zeusadmin_pwd)
            ssh_c.sendline()
        ssh_c.sendline()
        return (json.dumps({'code':200,'status':'start ok'},sort_keys=True,indent=4))

    except urllib2.URLError,e:
        return (json.dumps({'code':201,'status':'Restart has been successful, no need to restart'},sort_keys=True,indent=4))
    except pexpect.EOF:
        ssh_c.close()
        return (json.dumps({'code':300,'status':'SSH connection error!'},sort_keys=True,indent=4))
    except pexpect.TIMEOUT:
        return (json.dumps({'code':301,'status':'SSH connection TimeOut!'},sort_keys=True,indent=4))




#print start('10.125.110.12','d8059bb05c7937168f55d9d04743d31d7d8315d164daa434e23d15c1a86da723','10.125.110.182/24','10.125.110.254','/dev/cloud_nvme0n1/python-docker182','/docker_data/cloud_nvme0n1/python-docker182')


def remove(host_ip,ids,mount_dev,mount_path):
  def ssh_umonlt():

      ssh_c = pexpect.spawn('ssh -p21987  zeusadmin@%s "%s"' % (host_ip, 'sudo umount -lf %s' %(mount_path)))
      i = ssh_c.expect(['password:', 'continue connecting (yes/no)?'])
      if i == 0:
            ssh_c.sendline(zeusadmin_pwd)
      elif i == 1:
            ssh_c.sendline('yes\n')
            ssh_c.expect('password: ')
            ssh_c.sendline(zeusadmin_pwd)
      ssh_c.sendline()

  def ssh_lvremove():
#    list_all = []
#    try:
      ssh_c = pexpect.spawn('ssh -p21987  zeusadmin@%s "%s"' % (host_ip, 'sudo echo "yes"|sudo lvremove %s' %(mount_dev)))
      i = ssh_c.expect(['password:', 'continue connecting (yes/no)?'])
      if i == 0:
            ssh_c.sendline(zeusadmin_pwd)
      elif i == 1:
            ssh_c.sendline('yes\n')
            ssh_c.expect('password: ')
            ssh_c.sendline(zeusadmin_pwd)
      ssh_c.sendline()

  try:
     URL="http://%s:5555/containers/json?all=1" %(host_ip)
     response = urllib2.urlopen(URL).read()
     response_dict = eval(response)
     for i in response_dict:
        status = {'ID':[i.get("Id"),i.get('Status')]}
        if status["ID"][0] == "%s" %(ids):
           if re.search('Exit',status["ID"][1]):
                   ssh_umonlt()
                   request = urllib2.Request("http://%s:5555/containers/%s?v=1" %(host_ip,ids))
                   request.get_method = lambda: 'DELETE'
                   response = urllib2.urlopen(request)
                   ssh_lvremove()
                   return  (json.dumps({'code':200,'status':'Successfully deleted containers_id:%s' %(ids)},sort_keys=True,indent=4))
           else:


                    try:
                        headers = {'Content-type': 'application/json', 'Accept': 'charset=utf-8'}
                        req_stop = urllib2.Request("http://%s:5555/containers/%s/kill" %(host_ip,ids),'{}',headers)
                        try:
                             response_stop = urllib2.urlopen(req_stop)
                             ssh_umonlt()
                             request = urllib2.Request("http://%s:5555/containers/%s?v=1" %(host_ip,ids))
                             request.get_method = lambda: 'DELETE'
                             response = urllib2.urlopen(request)
                             ssh_lvremove()
                             return  (json.dumps({'code':200,'status':'Successfully deleted containers_id:%s' %(ids)},sort_keys=True,indent=4))
                        except urllib2.URLError,e:
                             return  (json.dumps({'code':500,'status':'URL TimeOut or containers_id:%s 404 Not Found' %(ids)},sort_keys=True,indent=4))


                    except Exception,e:
                            request = urllib2.Request("http://%s:5555/containers/%s?v=1" %(host_ip,ids))
                            request.get_method = lambda: 'DELETE'
                            try:
                                ssh_lvremove()
                                response = urllib2.urlopen(request)
                                return  (json.dumps({'code':200,'status':'Successfully deleted containers_id:%s' %(ids)},sort_keys=True,indent=4))
                            except urllib2.URLError,e:
                                return  (json.dumps({'code':500,'status':'URL TimeOut or containers_id:%s 404 Not Found' %(ids)},sort_keys=True,indent=4))
  except urllib2.URLError,e:
    return  (json.dumps({'code':500,'status':'URL TimeOut or containers_id:%s 404 Not Found' %(ids)},sort_keys=True,indent=4))

#print remove('10.125.111.12','3bc96c49090fce704766adf7975509176f34cbe4f84d145726bc47f70ee58f29','/dev/cloud_nvme0n1/python-docker180','/docker_data/cloud_nvme0n1/python-docker180')

def status_info(host_ip):
    lists = []
    try:

        URL="http://%s:5555/containers/json?all=1" %(host_ip)
        response = urllib2.urlopen(URL).read()
        response_dict = eval(response)
        for i in response_dict:
          try:
            if re.search('Up',i.get("Status")):
               status = 'Up'
#               print status

            elif re.search('Exit',i.get("Status")):
               status = 'Exit'
#               print status

            elif re.search('Create',i.get("Status")):
               status = 'Create'
            lists.append({"ID":i.get('Id'),'Status':status})
          except UnboundLocalError,e:
              pass



        return (json.dumps({'message':lists,'code':'200'},sort_keys=True,indent=4))


    except urllib2.URLError,e:
#        return (json.dumps({'message':lists,'code':'200'},sort_keys=True,indent=4))
        pass


#           return (json.dumps({'code':201,'message':'Container host state failure'},sort_keys=True,indent=4))
#print status_info('10.125.111.12')



def docker_all(host_ip):
    try:
        URL="http://%s:5555/info" %(host_ip)
        response = urllib2.urlopen(URL,timeout=120).read()
        response_dict = json.loads(response).get('DriverStatus')
        for i in response_dict:
#            print i[0],i[1]
            if re.search('Data Space Total',i[0]):
               total = {"total_status":i[1].replace('.','').replace('TB','')}

            elif re.search('Data Space Used',i[0]):
                if re.search('GB',i[1]):
#                    print i[1].replace('GB','')
#                    print len(i[1].replace('.','').replace('GB',''))
                    a = i[1].replace('GB','')
                    floats_integer = round(float(a),0)
#                    print len('%s' %int(round(float(floats_integer),0)))
                    if len('%s' %int(round(float(floats_integer),0))) == 1:
                        users = {"users_status":int(round(float(floats_integer),0)) * 1000}

                    elif len('%s' %int(round(float(floats_integer),0)))  == 2:

                        users = {"users_status":int(round(float(floats_integer),0)) * 1000}
                    elif len('%s' %int(round(float(floats_integer),0)))  == 3:
                        users = {"users_status":int(round(float(floats_integer),0)) * 1000}
                    elif len('%s' %int(round(float(floats_integer),0)))  == 4:
                        users = {"users_status":int(round(float(floats_integer),0)) * 1000}

                    else:
                        return (json.dumps({'code':'500','message':'docker data Storage is Full '},sort_keys=True,indent=4))

                elif  re.search('MB',i[1]):
                    b = i[1].replace('MB','')
#                    print b
                    floats_integers = round(float(b),0)
#                    print floats_integers

                    if len('%s' %int(round(float(floats_integers),0))) == 1:
                        users = {"users_status":int(round(float(floats_integers),0))}

                    elif len('%s' %int(round(float(floats_integers),0)))  == 2:

                        users = {"users_status":int(round(float(floats_integers),0))}
                    elif len('%s' %int(round(float(floats_integers),0)))  == 3:

                        users = {"users_status":int(round(float(floats_integers),0))}
                else:

                    pass
#        print users.get('users_status')
#        print int(float(total.get('total_status'))) * 1000
        if int(users.get('users_status'))  >= int(float(total.get('total_status'))) * 1000000 * 0.85:
            return (json.dumps({'code':'500','message':'docker data Storage is Full '},sort_keys=True,indent=4))
        else:
            return (json.dumps({'code':'200','message':'docker Data_Pool Storage is Available'},sort_keys=True,indent=4))

    except urllib2.URLError,e:
        return (json.dumps({'code':'404','message':'Url Http_Request Error'},sort_keys=True,indent=4))

#print docker_all('10.69.111.11')



def docker_monitor(host_ip,container_id,network_card):
  try:
    lists=[]
    network_alls=[]
    memory_alls=[]
    cpu_alls=[]
    io_alls=[]
    times = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    datetimes = int(time.mktime(time.strptime(times,'%Y-%m-%d %H:%M:%S')))
#    datetimes = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
#    timeStamp = int(time.mktime(datatimes))
    cli = Client(base_url='tcp://%s:5555' %(host_ip),version='1.20')
    stats_obj = cli.stats('%s' %(container_id))
    for i in stats_obj:
        lists.append(i)
        break
    for i in lists:
        i_json = json.loads(i)
        for k,v in i_json.items():
#            print k
            if re.search('network',k):
               network = {'network_stats':[v]}
               network_alls.append(network)
            if re.search('memory_stats',k):
               memory = {'memory_stats':[v]}
#               print memory
               for memory_i in memory.get('memory_stats'):
                   memory_stats = {'mem_usage':str(round(memory_i.get('usage')) / 1000000),'mem_limit':str(memory_i.get('limit') / 1000000000 * 1000)}

#               memory_alls.append(memory)
            if re.search('cpu_stats',k):
               cpu = {'cpu_stats':[v]}
               for cpu_i in cpu.get('cpu_stats'):
#                    print cpu
#                   for k,v in cpu_i.items():
#                       print v
#                   if re.search('throttling_data',cpu_i.get('cpu_usage').get('throttling_data')):
   #                 print cpu_i
#                    print cpu_i.get('cpu_usage').get('total_usage')
#                    print cpu_i.get('cpu_usage').get('percpu_usage')
                    if  int(cpu_i.get('cpu_usage').get('total_usage')) != 0 and cpu_i.get('cpu_usage').get('total_usage') != None:
                        #stats = cpu_i.get('cpu_usage').get('total_usage') / cpu_i.get('cpu_usage').get('percpu_usage')[0]
                        cpu_stats = str(float(cpu_i.get('cpu_usage').get('total_usage') / cpu_i.get('cpu_usage').get('percpu_usage')[0])  / 100) + '%'
#                        print stats
#                        print cpu_i.get('cpu_usage').get('total_usage')
#                        print cpu_i.get('cpu_usage').get('percpu_usage')[0]
#                        print stats
                    else:
                        pass

#               cpu_alls.append(cpu)
            if re.search('blkio_stats',k):
               io = {'io_stats':[v]}
               io_alls.append(io)

    linux='python /home/zeusadmin/monitor/monitor_flow.py %s' %network_card
    cli = docker.Client(base_url='tcp://%s:5555' %(host_ip),version='1.20',timeout=10)
    ex = cli.exec_create(container=container_id, cmd=linux,user='root')
    ls = cli.exec_start(exec_id=ex["Id"], tty=True).strip('\r\n')
    if len(ls) == 0:
        flow =  u"监控无数据"

    else:
        flow = eval(ls)
#        print ls

#    print memory_stats
#    print cpu_stats
#    print io_alls
#    print flow
    all_stats = {'code':200,'monitor_time':datetimes,'message':[{'memory_stats':memory_stats},{'flow_stats':flow},{'cpu_stats':{'cpu_usage':cpu_stats}}]}
    return (json.dumps(all_stats,sort_keys=True,indent=4))
#    print stats
 #   status = {'code':200,'message': [network_alls,memory_alls,cpu_alls,io_alls]}
#    return (json.dumps(status,sort_keys=True,indent=4))
  except docker.errors.NotFound,e:
      return e
  except Exception,e:
      return e
#    print network_alls
#    print memory_alls
#    print cpu_alls
#    print io_alls
#        print cpu
#print docker_monitor('10.69.111.11','33389c20e698','eth2')



def flow(host_ip,container_id,network_card):
     try:
            linux='python /home/zeusadmin/monitor/monitor_flow.py %s' %network_card
            cli = docker.Client(base_url='tcp://%s:5555' %(host_ip),version='1.20',timeout=10)
            ex = cli.exec_create(container=container_id, cmd=linux,user='root')
            ls = cli.exec_start(exec_id=ex["Id"], tty=True).strip('\n')
            if len(ls) == 0:
               return u"监控无数据"
            else:
               return ls
     except Exception,e:
            return e




#print flow('10.69.111.11','919e734b2845','eth2')




def start_test(host_ip,ids,container_ip,container_gw,mount_dev,mount_path):
    jcdata = '''
       {
       "HostConfig": {"Memory":%s,"MemorySwap":%s,"Binds":["/test:/opt"]}


      }
    '''  % (int('4800000000'),int('4800000000'))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'charset=utf-8'}
        req_start = urllib2.Request("http://%s:5555/containers/%s/start" %(host_ip,ids), jcdata, headers)
        response_start = urllib2.urlopen(req_start)
        out_start = response_start.read()

        ssh_c = pexpect.spawn('ssh -p21987  zeusadmin@%s "%s"' % (host_ip, 'sudo pipework em2 -i eth2 %s %s@%s && sudo mount %s %s' %(ids,container_ip,container_gw,mount_dev,mount_path)))
        i = ssh_c.expect(['password:', 'continue connecting (yes/no)?'])

        if i == 0:
            ssh_c.sendline(zeusadmin_pwd)
        elif i == 1:
            ssh_c.sendline('yes\n')
            ssh_c.expect('password: ')
            ssh_c.sendline(zeusadmin_pwd)
            ssh_c.sendline()
        ssh_c.sendline()
        return (json.dumps({'code':200,'status':'start ok'},sort_keys=True,indent=4))

    except urllib2.URLError,e:
        return (json.dumps({'code':201,'status':'Restart has been successful, no need to restart'},sort_keys=True,indent=4))
    except pexpect.EOF:
        ssh_c.close()
        return (json.dumps({'code':300,'status':'SSH connection error!'},sort_keys=True,indent=4))
    except pexpect.TIMEOUT:
        return (json.dumps({'code':301,'status':'SSH connection TimeOut!'},sort_keys=True,indent=4))

#print start_test('10.69.111.12','d38de718a806d6123f5cfe37a7a8f6491215f5935f60263fbac3652b7e3a8f1f','10.69.112.199/24','10.69.112.254','/dev/cloud_sdd/python-docker190','/docker_data/cloud_sdd/python-docker190')


