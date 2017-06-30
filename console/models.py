# coding: utf-8
from django.db import models


# Create your models here.
class Config(models.Model):
    name = models.CharField(max_length=50, unique=True)
    cpu = models.CharField(max_length=50)
    memory = models.CharField(max_length=50)
    disk = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name


class Server(models.Model):
    hostname = models.CharField(max_length=100, unique=True)
    container_ip = models.IPAddressField()
    parent_host = models.IPAddressField()

    def __unicode__(self):
        return self.hostname


class User(models.Model):
    PERM = (
        ('A', u'申请者'),
        ('R', u'审核者'),
        ('M', u'管理者')
    )

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    perm = models.CharField(max_length=1, choices=PERM)

    def __unicode__(self):
        return self.username


class Application(models.Model):
    STATUS = (
        (1, u'审核中'),
        (2, u'审核通过, 正在执行'),
        (3, u'执行成功'),
        (4, u'执行失败, 正在进行人工干预'),
        (5, u'驳回')
    )
    username = models.CharField(max_length=50)
    apply_time = models.DateTimeField(auto_now_add=True)
    config = models.ForeignKey(Config)
    os = models.CharField(max_length=50)
    server_num = models.IntegerField()
    users_add = models.CharField(max_length=500)
    status = models.IntegerField(choices=STATUS)
    result = models.TextField()
    result_error = models.TextField()
    reviewer = models.ForeignKey(User, blank=True, null=True)
    resolver = models.CharField(max_length=50, blank=True, null=True)
    leader_email = models.EmailField()
    apply_reason = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.username


class Host(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ip = models.IPAddressField()
    gateway = models.IPAddressField()
    netmask = models.IPAddressField()
    disk_used = models.CharField(max_length=100)
    ip_range = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.ip


class Container(models.Model):
    hostname = models.CharField(max_length=100)
    host_ip = models.IPAddressField()
    container_ip = models.IPAddressField()
    container_id = models.CharField(max_length=256)
    mount_dev = models.CharField(max_length=512)
    mount_path = models.CharField(max_length=512)
    cpu = models.CharField(max_length=100)
    memory = models.CharField(max_length=100)
    disk = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    application = models.ForeignKey(Application)

    def __unicode__(self):
        return self.hostname

class Ipdb(models.Model):
    STATUS = (
        (0, u'未使用'),
        (1, u'运行使用'),
        (2, u'暂停使用')
    )

    ipaddr = models.CharField(max_length=100)
    hostname = models.CharField(max_length=100)
    type_id = models.IntegerField(choices=STATUS)

    def __unicode__(self):
        return self.hostname


class Monitor(models.Model):
    hostname = models.CharField(max_length=100)
    item = models.CharField(max_length=100)
    unix_time = models.IntegerField()
    value = models.FloatField()

    def __unicode__(self):
        return self.hostname


class Atest(models.Model):
    apply_time = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100)



class container_auditLogs(models.Model):
      STATUS = (
        (0, u'启动'),
        (1, u'停止'),
        (2, u'删除'),
        (3, u'重建'),
        (4, u'详情'),
        (5, u'批量启动'),
        (6, u'批量停止'),
        (7, u'批量删除'),
        (8, u'批量重建')
      )
      unix_time = models.DateTimeField(auto_now_add=True)
      login_user = models.CharField(max_length=100)
      host_ip = models.TextField()
      hostname = models.CharField(max_length=100000)
      action = models.IntegerField(choices=STATUS)

      def __unicode__(self):
          return self.login_user






