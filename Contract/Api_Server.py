from flask import Flask, request
from gevent import pywsgi
from Contract.Contract1 import change_contract
from Config import port, ip, api_port
import json

app = Flask(__name__)


@app.route('/donate/<random>', methods=['POST', 'GET'])
def donate(random):
    data = request.data.decode()
    data = json.loads(data)
    address = data['address']
    amount = int(data['amount'])
    baseurl = 'http://%s:%s/' % (ip, port)
    url = baseurl + 'transaction/create/%s/' % random
    change_contract(address=address, amount=int(amount), baseurl=baseurl, url=url)
    return 'true'


if __name__ == '__main__':
    server = pywsgi.WSGIServer((ip, api_port), app)
    server.serve_forever()
