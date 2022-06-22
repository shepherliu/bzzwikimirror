#!/usr/bin/python3 
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import re
import getopt
import enum
import logging
import mimetypes
import requests
import urllib.parse
import hashlib
import etcd3
from http.server import HTTPServer, BaseHTTPRequestHandler

from fairos.fairos import Fairos

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

FAIROS_HOST = "https://fairos.fairdatasociety.org"

FAIROS_VERSION = 'v1'

POD_NAME = 'wikimedia_zim'

fs = None
etcd = None
root = '~/dist'

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)

class Resquest(BaseHTTPRequestHandler):
	def do_GET(self):
		global root

		path = self.path.split('?')[0]

		if path.startswith('/api/zimlist'):
			return self.getZimListInfo()

		if path.startswith('/api/zimstatus'):
			relpath = os.path.relpath(path, '/api/zimstatus')
			return self.getZimFileStatus(relpath)

		if path == '/':
			path = '/index.html'

		localpath = os.path.join(root, path.split('/')[1])

		types, encoding = mimetypes.guess_type(path)
		if types is None:
			types = 'text/plain'

		if os.path.isfile(localpath):
			return self.getFileFromLocal(localpath, types)
		else:
			return self.getFileFromFairOs(path, types)

	#read file from local system
	def getFileFromLocal(self, filepath:str, types:str):
		try:
			content = open(filepath, 'rb').read()
			self.send_response(200)
			self.send_header('Content-type', types)
			self.end_headers()
			self.wfile.write(content)			
		except:
			return self.notFoundPage()

	#read file from fair os
	def getFileFromFairOs(self, filepath:str, types:str):
		global fs

		try:
			res = fs.download_file(POD_NAME, filepath)
			if res['message'] != 'success':
				#check cookie if need update
				# fs.update_cookie(POD_NAME)
				#sync pod and try again
				fs.sync_pod(POD_NAME)
				res = fs.download_file(POD_NAME, filepath)

			if res['message'] != 'success':
				logging.error(f"read {filepath} from fairos error: {res['message']}")
				return self.notFoundPage()
			
			self.send_response(200)
			self.send_header('Content-type', types)
			self.end_headers()
			self.wfile.write(res['content'])
		except:
			return self.notFoundPage()

	#get zim list info
	def getZimListInfo(self):
		zimlist = []
		dumps = parse_wikipedia_dumps(get_wikipedia_dumps())
		for d in dumps:
			name, size, timestamp = d
			zimlist.append({
				name:name,
				size:size,
				timestamp:timestamp
			})
		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		self.wfile.write(json.dumps(zimlist).encode())

	#get zim file status
	def getZimFileStatus(self, name:str):
		keyname = hashlib.md5(name.encode('utf-8')).hexdigest()
		status = {
			name: check_zim_status(keyname, etcd)
		}

		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		self.wfile.write(json.dumps(status).encode())		

	#not found page
	def notFoundPage(self):
		self.send_response(404)
		self.send_header('Content-type', 'text/html')	
		self.end_headers()
		self.wfile.write(f"<html><body><h4>file is not found</h4></body></html>".encode())		

#init fairos module
def init_fairos(username, password, host = FAIROS_HOST, version = FAIROS_VERSION, podname = POD_NAME):

	fs = Fairos(host, version)

	#login user
	res = fs.login_user(username, password)

	if res['message'] != 'success':
		logging.error(f"login user: {username} error: {res['message']}")
		return None
	else:
		logging.info(f"login user: {username} success")

	#open pod
	res = fs.open_pod(podname)

	if res['message'] != 'success':
		logging.error(f"open pod: {podname} error: {res['message']}")
		return None
	else:
		logging.info(f"open pod: {podname} success")
	
	return fs

#parse timestamp
def parse_timestamp(timestamp, timeformat = '%d-%b-%Y %H:%M'):

	t = time.strptime(timestamp, timeformat)

	return int(time.mktime(t))

#parse file size
def parse_size(size = 0.0):

	if size < 1024:
		return '{0} B'.format(round(size, 2))
	else:
		size /= 1024

	if size < 1024:
		return '{0} KB'.format(round(size, 2))
	else:
		size /= 1024

	if size < 1024:
		return '{0} MB'.format(round(size, 2))
	else:
		size /= 1024

	if size < 1024:
		return '{0} GB'.format(round(size, 2))
	else:
		size /= 1024

	if size < 1024:
		return '{0} TB'.format(round(size, 2))
	else:
		size /= 1024		

	return '{0} PB'.format(round(size, 2))

#get wiki zim list
def get_wikipedia_dumps(host = WIKIPEDIA_HOST):

	res = requests.get(host)

	if res.status_code >= 200 and res.status_code < 300:
		regexp = r'\>(wikipedia\S{1,}\.zim)\<\S{1,}\s{1,}(\S{1,}\s{1,}\S{1,})\s{1,}(\d{1,})'
		return re.findall(regexp, res.text)
	else:
		logging.error(f"get wikipedia dumps error: {res.text}")

	return None

#parse wiki dumps
def parse_wikipedia_dumps(data = []):

	res = []

	if data is None:

		return res

	for d in data:

		name, timestamp, size = d

		res.append([name, parse_size(float(size)), timestamp])
	
	return sorted(res, key = lambda x: parse_timestamp(x[2]))

#check zim status
def check_zim_status(name, etcd):

	res = etcd.get(name)

	if res == '' || res is None:
		return 'waiting'

	try:
		if int(res) > 0:
			return 'uploaded'
		else:
			return 'waiting'
	except:
		return res

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	etcdhost = ''
	root = '~/dist'

	try:
		opts, args = getopt.getopt(argv, "h:e:v:u:p:r:", [
			"host=",
			"etcd=",
			"version=",
            "user=",
            "password=",
            "root="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--host','-h']:
			host = arg
		elif opt in ['--etcd','-e']:
			etcdhost = arg			
		elif opt in ['--version','-v']:
			version = arg
		elif opt in ['--user','-u']:
			user = arg
		elif opt in ['--password','-p']:
			password = arg
		elif opt in ['--root', '-r']:
			root = arg

	if not os.path.exists(root):
		os.makedirs(root)

	fs = init_fairos(user, password, host, version)
	if fs is None:
		sys.exit(-1)

	etcd = etcd3.client(host = etcdhost)

	server = HTTPServer(('0.0.0.0', 8080), Resquest)
	server.serve_forever()