#!/usr/bin/env python
# encoding: utf-8

from console.models import User
import json


def add_users(username,email,perm):
    try:
        user = User(username=username, email=email, perm=perm)
        user.save()
        return (json.dumps({'message':[{'add_user':'success'}],'code':'200'},sort_keys=True,indent=4))
    except Exception,e:
        return (json.dumps({'message':[{'add_user':'error'}],'code':'500'},sort_keys=True,indent=4))




