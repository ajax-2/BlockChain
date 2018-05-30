from Flask_Setting import app
from Chain_Setting import BaseUtils
from flask import request, jsonify, send_from_directory
import requests
from Config import base_block_cap
import json
import threading
from sys import getsizeof
from urllib3 import PoolManager
import os
import zipfile
httpRequest = PoolManager()
path = os.path.abspath('.')


@app.route('/miner', methods=['GET', 'POST'])
def miner():
    data = request.args.get('flag')
    if data == 'start':
        BaseUtils.miner_flag = True
    elif data == 'stop':
        BaseUtils.miner_flag = False
    elif data == 'get':
        return 'Result: miner flag is ' + str(BaseUtils.miner_flag)
    else:
        return 'Error: you cannot access it with your request url !'
    return data + ' miner!!'


@app.route('/transaction/create/<random>/', methods=['POST'])
def submit_transaction(random):
    data = request.data.decode()
    hash = BaseUtils.submit_transaction(data=data, gas_price=0)
    return json.dumps({"Success": {'hash': hash,
                                   },
                       })


@app.route('/transaction/get', methods=['GET', 'POST'])
def get_transaction():
    values = request.values
    if 'hash' not in values:
        return 'Error: you must offer a hash of this request!!'
    hash = values['hash']
    return json.dumps(BaseUtils.get_transaction(
        hash, block=BaseUtils.block_chain_have_sync[:]), default=BaseUtils.parse_transaction)


@app.route("/download/whoisyourdaddy", methods=['GET'])
def downloader():
    f = zipfile.ZipFile('data.zip', 'w', zipfile.ZIP_DEFLATED)
    startdir = "temp"
    for dirpath1, dirnames, filenames in os.walk(startdir):
        for filename in filenames:
            f.write(os.path.join(dirpath1, filename))
    f.close()
    return send_from_directory(path, 'data.zip', as_attachment=True)


@app.route('/node/register', methods=['GET', 'POST'])
def register_node():
    values = request.values
    if 'addr' not in values or 'data' not in values or 'first' not in values:
        return 'Error: you must offer address and data in this request !!'
    addr = values['addr']
    data = values['data']
    first = values['first']
    for i in BaseUtils.node:
        if i.addr == addr:
            return 'you have register!!'
    BaseUtils.register_node(addr=addr, data=data)
    httpRequest.request('GET', url='http://%s/node/register?addr=%s&data=%s&first=0'
                                   % (addr, BaseUtils.node[0].addr, BaseUtils.node[0].data))
    for i in BaseUtils.node:
        httpRequest.request('GET', url='http://%s/node/register?data=%s&addr=%s&first=0' % (i.addr, data, addr))
    result = json.loads(requests.get('http://%s/block/sync/first' % addr).text)
    if first == '1':
        threading.Thread(target=BaseUtils.get_data_to_nodeByHttp, args=(result['ip'],)).start()
        BaseUtils.block_chain_have_sync = BaseUtils.load_all_block(result['block_chain_have_sync'])
        BaseUtils.block_chain_not_sync = BaseUtils.load_all_block(result['block_chain_not_sync'])
    return 'Success: you have added in the network-link !!'


@app.route('/node/get', methods=['GET', 'POST'])
def get_all_node():
    response = {}
    for i, node in enumerate(BaseUtils.node):
        response[str(i)] = str(node)
    return jsonify(response)


@app.route('/block/sync', methods=['GET', 'POST'])
def sync_block():
    length = 0
    block_chain_new = None
    for column, i in enumerate(BaseUtils.node):
        message = BaseUtils.parse_node_valid(url='http://%s/block/sync/get' % i.addr, column=column)
        if not message:
            continue
        block_chain = BaseUtils.load_all_block(json.loads(message))
        if len(block_chain) > length:
            length = len(block_chain)
            block_chain_new = block_chain[:]
    if block_chain_new:
        for i in block_chain_new:
            i.have_sync = True
        for i in BaseUtils.node:
            data = json.dumps(BaseUtils.parse_all_block(block=block_chain_new[:]))
            BaseUtils.parse_node_valid(url='http://%s/block/add/new' % i.addr, data=data, column=column, method='post')
        if getsizeof(json.dumps(BaseUtils.parse_all_block(block=BaseUtils.block_chain_have_sync)))\
                / 1024 / 1024 > base_block_cap:
            block_size = len(BaseUtils.block_chain_have_sync) - 7
            BaseUtils.parse_block_to_file(new_block=BaseUtils.block_chain_have_sync,
                                          filename=str(BaseUtils.block_chain_have_sync[block_size - 1].index),
                                          block_size=block_size)
    if BaseUtils.block_chain_not_sync:
        BaseUtils.block_chain_not_sync[0].index = BaseUtils.block_chain_have_sync[-1].index + 1
        BaseUtils.block_chain_not_sync[0].previous_hash = BaseUtils.block_chain_have_sync[-1].hash
    else:
        BaseUtils.block_new.index = BaseUtils.block_chain_have_sync[-1].index + 1
        BaseUtils.block_new.previous_hash = BaseUtils.block_chain_have_sync[-1].hash
    return 'sync block success, and the sync block_link\'s length is %s' % length


@app.route('/block/sync/first', methods=['POST', 'GET'])
def sync_block_all():
    return BaseUtils.block_get_all()


@app.route('/block/add/new', methods=['POST', 'GET'])
def add_new_sync():
    block_chain_new_str = json.loads(request.data.decode())
    block_chain_new = BaseUtils.load_all_block(block_chain_new_str)
    if block_chain_new[0].previous_hash == BaseUtils.block_chain_have_sync[-1].hash:
        BaseUtils.block_chain_have_sync.extend(block_chain_new)
        block_new_hash = [i.hash for i in block_chain_new]
        while BaseUtils.block_chain_not_sync:
            if BaseUtils.block_chain_not_sync[0].hash not in block_new_hash:
                break
            else:
                BaseUtils.block_chain_not_sync.pop(0)
    if BaseUtils.block_chain_not_sync:
        BaseUtils.block_chain_not_sync[0].previous_hash = BaseUtils.block_chain_have_sync[-1].hash
    return 'Success: sync finish!'


@app.route('/block/get', methods=['GET', 'POST'])
def get_block_chain():
    return json.dumps(BaseUtils.parse_all_block(block=BaseUtils.block_chain_have_sync))


@app.route('/block/sync/get', methods=['GET', 'POST'])
def get_sync_block_chain():
    return json.dumps(BaseUtils.parse_all_block(block=BaseUtils.block_chain_not_sync[:]))
