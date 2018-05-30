from .BaseClass import Block, Transaction, Node
import datetime
from Config import ip, port, transaction_limit
from hashlib import sha256
import json
import os
import time
import threading
from urllib3 import PoolManager
import requests
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


###
# register node
###
def register_node(addr, data):
    timestamp = datetime.datetime.now()
    node_new = Node(addr, data, timestamp)
    node.append(node_new)


###
# create genesis block
###
def create_genesis_block():
    index = 0
    timestamp = str(datetime.datetime.now())
    data = 'Genesis Block'
    previous_hash = None
    block = Block(index, timestamp, data, previous_hash)
    block.have_sync = True
    block_chain_have_sync.append(block)
    parse_block_to_file(new_block=block_chain_have_sync, filename="genesis", block_size=1)


###
# create new block and this block is not sync
###
def create_new_block():
    if block_chain_not_sync:
        block_last = block_chain_not_sync[-1]
    else:
        block_last = block_chain_have_sync[-1]
    index = block_last.index + 1
    timestamp = None
    data = "this is %s block" % index
    previous_hash = block_last.hash
    global block_new
    block_new = Block(index, timestamp, data, previous_hash)


###
# submit a transaction in transaction cache
###
def submit_transaction(data, gas_price):
    timestamp = datetime.datetime.now()
    transaction = Transaction(timestamp, data, gas_price)
    transaction_cache.append(transaction)
    return transaction.hash


###
# parse a block and return a map
###
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


###
# parse a map and return a block
###
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


###
# parse a transaction and return a map
###
def parse_transaction(tran_one):
    return {
        "timestamp": str(tran_one.timestamp),
        'data': tran_one.data,
        'gas_price': tran_one.gas_price,
        'hash': tran_one.hash,
    }


###
# parse a map and return a transaction
###
def load_transaction(tran_dict):
    temp = Transaction(None, None, None)
    temp.timestamp = tran_dict['timestamp']
    temp.data = tran_dict['data']
    temp.gas_price = tran_dict['gas_price']
    temp.hash = tran_dict['hash']
    return temp


###
# method of calculate when worker miner
###
def proof_pow(y):
    x = 5
    while sha256(f'{x*y}'.encode()).hexdigest()[:5] != "00000":
        y += 1


###
# add synchronized block in the end of block_chain
###
def add_sync_block(new_block):
    global block_chain_have_sync
    block_chain_have_sync.extend(new_block)


###
# parse all block, and be purpose to storage or send to other node
###
def parse_all_block(block=[]):
    map_block = []
    for i in block:
        map_block.append(json.dumps(obj=i, default=parse_block))
    return map_block


###
# parse dicts to block_chain
###
def load_all_block(block_list):
    return [json.loads(i, object_hook=load_block) for i in block_list]


###
# storage block_chain on disk
###
def parse_block_to_file(new_block, filename, block_size):
    map_a = parse_all_block(block=new_block[:block_size])
    f_dump = open(os.path.join(os.path.abspath('.') + "/temp/", filename), 'w')
    json.dump(obj=map_a, fp=f_dump)
    f_dump.close()
    global block_chain_have_sync
    if block_size == 1:
        insert_into_file(name=filename, last_block_index=block_chain_have_sync[0].index)
    else:
        insert_into_file(name=filename, last_block_index=block_chain_have_sync[block_size - 1].index)
        block_chain_have_sync = block_chain_have_sync[block_size:]


###
# boot block_chain with history file.
###
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


###
# inspect hash is exists in block
###
def compare_hash(hash, block_hash):
    for i in block_hash.transaction:
        if i.hash == hash:
            return i
    return None


###
# get a transaction message base from hash
###
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


###
# miner method
###
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
            requests.get('http://%s/block/sync' % node[0].addr)
            print("create new block !!")
            time.sleep(.3)
        else:
            time.sleep(10)


###
# when a node register, we will send it all block
###
def block_get_all():
    return json.dumps({
        'block_chain_have_sync': parse_all_block(block=block_chain_have_sync),
        'block_chain_not_sync': parse_all_block(block=block_chain_not_sync),
        'ip': ip,
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
# decompress a file
###
def unzip_file(zfile_path):
    try:
        with zipfile.ZipFile(zfile_path) as zfile:
            zfile.extractall(path='')
    except zipfile.BadZipFile as e:
        print(zfile_path+" is a bad zip file ,please check!")


###
# get data file from network
###
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


###
# boot method
###
if __name__ == 'Chain_Setting.BaseUtils':
    filename = get_last_file() or 'No File'
    if 'No File' in filename:
        start_chain_block(filename=None)
    else:
        start_chain_block(filename=filename)
    threading.Thread(target=miner_continue).start()
