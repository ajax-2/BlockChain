#!/usr/bin/env python3
# coding: utf-8

import socket
import urllib3
import logging
import json
import os
from hashlib import sha256

path = os.path.abspath('../log')
filename = 'error.log'

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)
handle = logging.FileHandler(os.path.join(path, filename))
handle.setLevel(level=logging.INFO)
logger.addHandler(handle)

socket.setdefaulttimeout(360)
httpRequest = urllib3.PoolManager()


##
# about contract, HODO
##
class Donate(object):

    def __init__(self, project):

        if not type(project) == self.Project:
            print('your parameters is not correct !')
            return None
        self.author = 'AllenCe'
        self.project = project

    def get_author(self):
        return self.author

    def donate(self, amount):
        self.project.have += amount
        print('you have donate %s , and the project have %s, we need %s to finish aim ! ' %
              (amount, self.project.have, self.project.aim - self.project.have))

    class Project:
        def __init__(self, name, aim):
            self.name = name
            self.aim = aim
            self.have = 0

        def __repr__(self):
            return '<Project.project>'

    @staticmethod
    def parse_project(obj):
        return {
            'name': obj.name,
            'aim': obj.aim,
            'have': obj.have,
        }

    @staticmethod
    def load_project(dict):
        p = Donate.Project(name=dict['name'], aim=dict['aim'])
        p.have = dict['have']
        return p

# over


def deploy_contract(address, url, name, aim):
    p = Donate.Project(name=name, aim=aim)
    c = Donate(project=p)
    hash = sha256()
    hash.update(str(c).encode())
    data = {
        'address': address,
        'event': 'deploy',
        'data': json.dumps({
            'author': c.author,
            'project': json.dumps(c.project, default=Donate.parse_project),
            'hash': hash.hexdigest(),
        }),
    }
    result = httpRequest.request(method='POST', url=url, body=json.dumps(data)).data.decode()
    return result


def change_contract(address, url, baseurl, amount, timeoutcount=0):
    ##
    # check data
    ##
    if timeoutcount > 2:
        logging.info('Error: this operation is timeout..')
        return 'Error: this operation is timeout. please check error log!'
    try:
        contract_have_data = httpRequest.\
            request(method='GET', url=baseurl + 'contract/get?address=%s' % address).data.decode()
        if 'Error' in contract_have_data:
            return contract_have_data
        # contract_have_data = json.loads(contract_have_data)
        # project = json.loads(contract_have_data['project'], object_hook=Donate.load_project)
        # if project.aim < project.have + amount:
        #   return 'donate aim have finish !!'
        data = {
            'address': address,
            'event': 'change',
            'data': json.dumps({
                'project': 'project',
                'name': 'have',
                'value': amount,
                'operator': 'add',
            }),
        }
        result = httpRequest.request(method='POST', url=url, body=json.dumps(data)).data.decode()
        return result
    except Exception as e:
        logging.exception(e)
        timeoutcount += 1
        return change_contract(address, url, baseurl, amount, timeoutcount)

