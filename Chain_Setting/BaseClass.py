from Config import block_size_limit, block_gas_limit
import hashlib


class Block(object):
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.transaction = []
        self.gas_limit = block_gas_limit
        self.block_size = block_size_limit
        self.contract_data = {}
        self.have_sync = False
        self.hash = self.hash_block()

    def hash_block(self):
        sha = hashlib.sha256()
        sha.update((str(self.index) +
                    str(self.timestamp) +
                    str(self.data) +
                    str(self.previous_hash) +
                    str(self.gas_limit) +
                    str(self.block_size) +
                    str(self.contract_data)
                    ).encode())
        return sha.hexdigest()


class Transaction(object):
    def __init__(self, timestamp, data, gas_price):
        self.timestamp = timestamp
        self.data = data
        self.gas_price = gas_price
        self.hash = self.transaction_hash()

    def transaction_hash(self):
        sha = hashlib.sha256()
        sha.update((
            str(self.data) +
            str(self.timestamp) +
            str(self.gas_price)
        ).encode())
        return sha.hexdigest()


class Node(object):
    def __init__(self, addr, data, timestamp):
        self.addr = addr
        self.data = data
        self.timestamp = timestamp
        self.hash = self.node_hash()

    def node_hash(self):
        sha = hashlib.sha256()
        sha.update((
            str(self.addr) +
            str(self.timestamp) +
            str(self.data)
                   ).encode())
        return sha.hexdigest()

    def __str__(self):
        return '{\n' \
               'addr: %s \n data: %s \n hash: %s \n timestamp: %s' \
               '\n}' % (self.addr, self.data, self.hash, self.timestamp)

