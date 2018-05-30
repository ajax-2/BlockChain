#!/usr/bin/env python3
# coding: utf-8

import socketserver
from Config import ip, port, socket_port
from Contract import Contract1
import datetime
import requests
import random
import json

server_port = socket_port
miner_true = False
baseurl = 'http://%s:%s/' % (ip, port)


def use_contract(data):
    if data['command'] == 'miner_start':
        result = requests.get(url=baseurl + 'miner?flag=start').text

    elif data['command'] == 'miner_stop':
        result = requests.get(url=baseurl + 'miner?flag=stop').text

    elif data['command'] == 'deploy':
        address = data['address']
        name = data['name']
        aim = int(data['aim'])
        url = baseurl + 'transaction/create/%s/' % (random.random())
        result = Contract1.deploy_contract(address, url, aim=aim, name=name)

    elif data['command'] == 'donate':
        address = data['address']
        amount = int(data['amount'])
        url = baseurl + 'transaction/create/%s/' % (random.random())
        result = Contract1.change_contract(address, url, baseurl, amount)

    elif data['command'] == 'getContract':
        address = data['address']
        result = requests.get(url=baseurl + 'contract/get?address=' + address).text

    return result


class TcpHandle(socketserver.BaseRequestHandler):

    def handle(self):
        recv = self.request.recv(1024).strip().decode()
        data = json.loads(recv)
        result = use_contract(data)
        result += 'execute time: %s ' % datetime.datetime.now()
        self.request.sendall(result.encode())


if __name__ == '__main__':
    server = socketserver.TCPServer((ip, server_port), TcpHandle)
    server.serve_forever()
