# coding: utf-8
from django import template
import time

register = template.Library()


@register.filter("timestamp")
def timestamp(timestamp):
    try:
        ts = float(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except AttributeError:
        return ''


@register.filter("prefix_12")
def prefix_12(words):
    return words[:12]


@register.filter("container_status")
def container_status(cid, all_status):
    keys_all = all_status.keys()
    if cid in keys_all:
        return all_status[cid]
    else:
        return 'Unknown'
