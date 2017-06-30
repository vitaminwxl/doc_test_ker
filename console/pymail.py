#!/usr/bin/env python
#-*- coding: utf-8 -*-
from email.mime.text import MIMEText
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders


def send_email(receiver, subject, body):

    username = 'zeus'
    password ='j,M;{e|zK1`9'
    host = 'mail.gomeplus.com'
    port = 25
    sender = "zeus@gomeplus.com"
    # receiver = ['lixiaokai@gomeplus.com']

    msg = MIMEMultipart()
    # utf-8解决邮件乱码问题####
    jc = MIMEText(body, "html", 'utf-8')
    # 这2行代码解决邮件乱码问题####
    jc["Accept-Language"] = "zh-CN"
    jc["Accept-Charset"] = "ISO-8859-1,utf-8"
    # 这2行代码解决邮件乱码问题####
    msg.attach(jc)
    msg["subject"] = subject
    msg["from"] = sender
    msg["to"] = ",".join(receiver)

    s = smtplib.SMTP(host)
    #s.starttls()

    s.login(username, password)
    s.sendmail(sender, receiver, msg.as_string())
    s.quit()

