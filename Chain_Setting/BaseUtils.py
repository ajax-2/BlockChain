from .BaseClass import Block, Transaction, Node
import datetime
from Config import ip, port, file_port, transaction_limit
from hashlib import sha256
import json
import os
import time
import threading
import socket
import socketserver
from urllib3 import PoolManager
import requests
import struct
from DB_Setting.DB_utils import insert_into_file, get_last_file
import zipfile
import requests.packages.urllib3
import logging

block_chain_have_sync = []
block_chain_not_sync = []
node = []
block_new = None
transaction_cache = []
miner_flag = False
httpRequest = PoolManager()


def register_node(addr, data):
    timestamp = datetime.datetime.now()
    node_new = Node(addr, data, timestamp)
    node.append(node_new)


def create_genesis_block():
    index = 0
    timestamp = str(datetime.datetime.now())
    data = 'Genesis Block'
    previous_hash = 0
    block = Block(index, timestamp, data, previous_hash)
    block.have_sync = True
    block_chain_have_sync.append(block)
    parse_block_to_file(new_block=block_chain_have_sync, filename="genesis", block_size=1)


def create_new_block():
    if block_chain_not_sync:
        block_last = block_chain_not_sync[-1]
    else:
        block_last = block_chain_have_sync[-1]
    index = block_last.index + 1
    timestamp = str(datetime.datetime.now())
    data = "this is %s block" % index
    previous_hash = block_last.hash
    global block_new
    block_new = Block(index, timestamp, data, previous_hash)


def submit_transaction(data, gas_price):
    timestamp = datetime.datetime.now()
    transaction = Transaction(timestamp, data, gas_price)
    transaction_cache.append(transaction)
    return transaction.hash


def parse_block(block_one):
    map_parse_block = {
            'index': block_one.index,
            'timestamp': str(block_one.timestamp),
            'data': block_one.data,
            'previous_hash': block_one.previous_hash,
            'transaction': [json.dumps(j, default=parse_transaction) for j in block_one.transaction],
            'contract_data': json.dumps(block_one.contract_data),
            'gas_limit': block_one.gas_limit,
            'block_size': block_one.block_size,
            'have_sync': block_one.have_sync,
            'hash': block_one.hash,
            }
    return map_parse_block


def load_block(dict):
    b = Block(None, None, None, None)
    b.index = dict['index']
    b.timestamp = dict['timestamp']
    b.data = dict['data']
    b.previous_hash = dict['previous_hash']
    b.gas_limit = dict['gas_limit']
    b.block_size = dict['block_size']
    b.hash = dict['hash']
    b.have_sync = dict['have_sync']
    b.contract_data = json.loads(dict['contract_data'])
    b.transaction = [json.loads(j, object_hook=load_transaction) for j in dict['transaction']]
    return b


def parse_transaction(tran_one):
    return {
        "timestamp": str(tran_one.timestamp),
        'data': tran_one.data,
        'gas_price': tran_one.gas_price,
        'hash': tran_one.hash,
    }


def load_transaction(tran_dict):
    temp = Transaction(None, None, None)
    temp.timestamp = tran_dict['timestamp']
    temp.data = tran_dict['data']
    temp.gas_price = tran_dict['gas_price']
    temp.hash = tran_dict['hash']
    return temp


def proof_pow(y):
    x = 5
    while sha256(f'{x*y}'.encode()).hexdigest()[:5] != "00000":
        y += 1


def add_sync_block(new_block):
    global block_chain_have_sync
    block_chain_have_sync.extend(new_block)


def parse_all_block(block=[]):
    map_block = []
    for i in block:
        map_block.append(json.dumps(obj=i, default=parse_block))
    return map_block


def load_all_block(block_list):
    return [json.loads(i, object_hook=load_block) for i in block_list]


def parse_block_to_file(new_block, filename, block_size):
    map_a = parse_all_block(block=new_block[:block_size])
    f_dump = open(os.path.join(os.path.abspath('.') + "/temp/", filename), 'w')
    json.dump(obj=map_a, fp=f_dump)
    f_dump.close()
    global block_chain_have_sync
    #
    if block_size == 1:
        insert_into_file(name=filename, last_block_index=block_chain_have_sync[0].index)
    else:
        insert_into_file(name=filename, last_block_index=block_chain_have_sync[block_size - 1].index)
        block_chain_have_sync = block_chain_have_sync[block_size:]


def start_chain_block(filename):
    # load or create genesis block and create new block
    node.append(Node(addr=(ip + ':' + str(port)), data='main_node', timestamp=datetime.datetime.now()))
    if filename:
        f_load = open(os.path.join(os.path.abspath('.') + "/temp/", filename), 'r')
        load_a = json.load(fp=f_load)
        f_load.close()
        list_a = load_all_block(load_a)
        global block_chain_have_sync
        block_chain_have_sync = list_a[:]
        create_new_block()

    else:
        create_genesis_block()
        create_new_block()


def save_data(address, data):
    data = json.dumps(obj=data)
    block_new.contract_data[address] = data


def get_data(address, block):

    i = len(block)
    while i >= 1:
        i -= 1
        if address in block[i].contract_data:
            return json.loads(block[i].contract_data[address])
    if block[0].index == 0:
        return 'Error: your address is not valid !!'
    else:
        f_load = open(os.path.join(os.path.abspath('.') + "/temp/", str(block[0].index - 1)), 'r')
        load_a = json.load(fp=f_load)
        f_load.close()
        list_a = load_all_block(load_a)
        block_list1 = list_a[:]
        return get_data(address=address, block=block_list1[:])


###
# inspect hash is exists in block
###
def compare_hash(hash, block_hash):
    for i in block_hash.transaction:
        if i.hash == hash:
            return i
    return None


def get_transaction(hash, block):
    verify_number = len(block_chain_not_sync) - 1
    while verify_number >= 0 and not compare_hash(hash, block_chain_not_sync[verify_number]):
        verify_number -= 1
    if verify_number >= 0:
        return 'the transaction is verifying !!'
    history_number = len(block) - 1
    while history_number >= 0 and not compare_hash(hash, block[history_number]):
        history_number -= 1
    if history_number >= 0:
        return compare_hash(hash, block[history_number])
    if block[0].index == 0:
        return 'Error: your hash is not correct !!'
    else:
        if not os.path.join(os.path.abspath('.') + "/temp/", str(block[0].index - 1)):
            return 'Error: history data file error, maybe somebody delete it!!'
        f_load = open(os.path.join(os.path.abspath('.') + "/temp/", str(block[0].index - 1)), 'r')
        load_a = json.load(fp=f_load)
        f_load.close()
        list_a = load_all_block(load_a)
        block_list1 = list_a[:]
        return get_transaction(hash=hash, block=block_list1[:])


def dumps_transaction(transaction):
    data = json.loads(transaction.data)
    if 'address' in data:
        address = data['address']
        if data['event'] == 'deploy':
            return address, None, None, None
        if data['event'] == 'change':
            t_data = json.loads(data['data'])
            project = t_data['project']
            value = t_data['value']
            name = t_data['name']
            operator = t_data['operator']
            if operator == 'add':
                value = + value
            elif operator == 'minus':
                value = - value
            return address, project, name, value
    return None, None, None, None


def flush_data_cache(block_chain_calculate):
    block_chain_calculate_number = len(block_chain_calculate)
    if block_chain_calculate_number > 7:
        transaction_temp_list = block_chain_calculate[-7].transaction
    else:
        return {}
    transaction_all = {}
    contract_change = {}
    for i in transaction_temp_list:
        address, project, name, value = dumps_transaction(i)
        if address and not value:
            contract_change[address] = json.loads(i.data)['data']
            continue
        if address and value:
            if address in transaction_all:
                transaction_all[address]['value'] += value
            else:
                transaction_all[address] = {}
                transaction_all[address]['value'] = value
                transaction_all[address]['name'] = name
                transaction_all[address]['project'] = project
    keys = transaction_all.keys()
    for i in keys:
        data = json.loads(get_data_from_address(i, block_list=block_chain_calculate[:]))
        project_one = transaction_all[i]['project']
        name_one = transaction_all[i]['name']
        data_project = json.loads(data[project_one])
        data_project[name_one] += transaction_all[i]['value']
        data[project] = json.dumps(data_project)
        contract_change[i] = json.dumps(data)
    return contract_change


def get_data_from_address(address, block_list):
    i = len(block_list) - 1
    while i >= 0 and address not in block_list[i].contract_data:
        i -= 1
    if i >= 0:
        return block_list[i].contract_data[address]
    elif block_list[0].index == 0:
        return 'Error: address is no valid !!'
    else:
        f_load = open(os.path.join(os.path.abspath('.') + "/temp/", str(block_list[0].index - 1)), 'r')
        load_a = json.load(fp=f_load)
        f_load.close()
        list_a = load_all_block(load_a)
        block_list1 = list_a[:]
        return get_data_from_address(address=address, block_list=block_list1[:])


def miner_continue():
    while True:
        if miner_flag:
            proof_pow(0)
            block_new.timestamp = str(datetime.datetime.now())
            size = transaction_limit
            if len(transaction_cache) < transaction_limit:
                size = len(transaction_cache)
            block_new.transaction = transaction_cache[:size]
            for i in range(size):
                transaction_cache.pop(0)
            block_chain_not_sync.append(block_new)
            create_new_block()
            block_chain_flush = block_chain_have_sync[:]
            block_chain_flush.extend(block_chain_not_sync)
            block_new.contract_data = flush_data_cache(block_chain_flush)
            requests.get('http://%s/block/sync' % node[0].addr)
            print("create new block !!")
            time.sleep(.3)
        else:
            time.sleep(10)


def block_get_all():
    return json.dumps({
        'block_chain_have_sync': parse_all_block(block=block_chain_have_sync),
        'block_chain_not_sync': parse_all_block(block=block_chain_not_sync),
        'ip': ip,
        'port': file_port,
    })


###
# parameters: url is request url, column is node index
# return: text,
###
def parse_node_valid(url, column, data=None ,method='get'):
    try:
        if method == 'post':
            if data:
                response = requests.post(url, data=data, timeout=30)
            else:
                response = requests.post(url, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
        node.pop(column)
    except Exception as e:
        logging.exception(e)
        node.pop(column)


###
# socket send & recv file
###
def parse_pack_data(recv):
    print(len(recv))
    info_unpack = struct.unpack('2048s', recv)[0].decode()
    message = ''
    for column, i in enumerate(info_unpack):
        if column <= info_unpack.rindex('}'):
            message = message + i
        else:
            break
    data_recv = json.loads(message)
    return data_recv


def unzip_file(zfile_path):
    '''
    function:解压
    params:
        zfile_path:压缩文件路径
        unzip_dir:解压缩路径
    description:
    '''
    try:
        with zipfile.ZipFile(zfile_path) as zfile:
            zfile.extractall(path='')
    except zipfile.BadZipFile as e:
        print(zfile_path+" is a bad zip file ,please check!")


def get_data_to_nodeByHttp(httpip):
    url = "http://"+httpip+":7779/download/whoisyourdaddy"
    response = requests.request("GET", url, stream=True, data=None, headers=None)
    save_path = "data.zip"
    total_length = int(response.headers.get("Content-Length"))
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    unzip_file(save_path)


def get_data_to_node(t_ip, t_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((t_ip, t_port))
        client.send('get_file_data'.encode())
        while True:
            recv = client.recv(2048)
            data_recv = parse_pack_data(recv)
            file_name = data_recv['file_name']
            file_first = data_recv['file_first']
            file_message = data_recv['file_message']
            if file_name == 'FINISH':
                break
            if file_first:
                file_flag = 'w'
            else:
                file_flag = 'a'
            with open(os.path.join(os.path.abspath('./temp'), file_name), file_flag) as f:
                f.write(file_message)
            client.send('CONTINUE'.encode())
    finally:
        client.close()


class TcpHandle(socketserver.StreamRequestHandler):

    def handle(self):
        if self.request.recv(20).decode() == 'get_file_data':
            list_file = os.listdir(os.path.join(os.path.abspath('.'), 'temp'))
            for i in list_file:
                with open(os.path.join(os.path.abspath('./temp'), i), 'r') as f:
                    first = 0
                    read = f.read(1000)
                    while read:
                        file_first = False
                        if first == 0:
                            file_first = True
                            first = 1
                        info = {
                            'file_name': i,
                            'file_first': file_first,
                            'file_message': read,
                                }
                        info_pack = json.dumps(info)
                        server_info = struct.pack('2048s', info_pack.encode())
                        self.request.send(server_info)
                        if self.request.recv(10).decode() == 'CONTINUE':
                            read = f.read(1000)
                        else:
                            time.sleep(1)
                            break
            info = {
                'file_name': 'FINISH',
                'file_first': False,
                'file_message': 0,
            }
            info_pack = json.dumps(info)
            eof_info = struct.pack('2048s', info_pack.encode())
            print(eof_info)
            self.request.sendall(eof_info)


if __name__ == 'Chain_Setting.BaseUtils':
    filename = get_last_file() or 'No File'
    if 'No File' in filename:
        start_chain_block(filename=None)
    else:
        start_chain_block(filename=filename)
    threading.Thread(target=miner_continue).start()
    server = socketserver.TCPServer((ip, file_port), TcpHandle)
    threading.Thread(target=server.serve_forever).start()

