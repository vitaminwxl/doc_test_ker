#!/usr/bin/env python
# encoding: utf-8
import os, sys, json
path = os.getcwd()
parent_path = os.path.dirname(path)
sys.path.append(parent_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'judy.settings'


from console.models import Container, Monitor
from interface.api import docker_monitor


container_all = Container.objects.all()
for container in container_all:
    monitor_result = docker_monitor(container.host_ip, container.container_id, "eth2")
    monitor_result = json.loads(monitor_result)
    if int(monitor_result['code']) == 200:
        mem_usage = monitor_result['message'][0]['memory_stats']['mem_usage']
        cpu_usage = monitor_result['message'][2]['cpu_stats']['cpu_usage'][:-1]
        network_rx = monitor_result['message'][1]['flow_stats']['RX']
        network_tx = monitor_result['message'][1]['flow_stats']['TX']
        unix_time = monitor_result['monitor_time']
        mem_item = Monitor(hostname=container.hostname, item='memory', unix_time=unix_time, value=mem_usage)
        mem_item.save()
        cpu_item = Monitor(hostname=container.hostname, item='cpu', unix_time=unix_time, value=cpu_usage)
        cpu_item.save()
        rx_item = Monitor(hostname=container.hostname, item='network_rx', unix_time=unix_time, value=network_rx)
        rx_item.save()
        tx_item = Monitor(hostname=container.hostname, item='network_tx', unix_time=unix_time, value=network_tx)
        tx_item.save()

        print mem_usage, cpu_usage, network_rx, network_tx

