#!/usr/bin/env python3
# coding: utf-8

from gevent import monkey
from gevent import pywsgi
from Config import ip, port
monkey.patch_all()
from Flask_Setting import app

if __name__ == '__main__':
    server = pywsgi.WSGIServer((ip, port), app)
    server.serve_forever()
