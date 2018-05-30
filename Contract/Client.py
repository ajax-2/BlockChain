#!/usr/bin/env python3
# coding: utf-8

import socket
import json
from multiprocessing import Pool
import datetime
from Config import socket_port as port, ip
p = None


def donate(data):
    times = int(input('please times:'))
    print('exec time:', datetime.datetime.now())
    for i in range(times):
        p.apply_async(send_recv, args=(data,))


def send_recv(data):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        data = json.dumps(data)
        client.sendall(data.encode())
        result = client.recv(1024).decode()
        print(result)
    finally:
        client.close()


if __name__ == '__main__':

        while True:
            p = Pool(4)
            print('1 : start miner . 2 : stop miner . 3 : deploy contract . 4 : donate . 5 : get contract')
            enter = input('Please you choice :')
            if enter == '1':
                data = {
                    'command': 'miner_start',
                }
            elif enter == '2':
                data = {
                    'command': 'miner_stop',
                }
            elif enter == '3':
                data = {
                    'command': 'deploy',
                    'address': input('contract address:'),
                    'name': input('project name:'),
                    'aim': input('donate aim:'),
                }
            elif enter == '4':
                data = {
                    'command': 'donate',
                    'address': input('contract address:'),
                    'amount': input('donate amount:'),
                }
                donate(data)
                continue

            elif enter == '5':
                data = {
                    'command': 'getContract',
                    'address': input('contract address:'),
                }
            else:
                break
            send_recv(data)
