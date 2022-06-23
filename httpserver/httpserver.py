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
import _pickle as pickle
from threading import Thread
from twisted.web import server, resource
from twisted.internet import reactor, endpoints

from fairos.fairos import Fairos

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

FAIROS_HOST = "https://fairos.fairdatasociety.org"

FAIROS_VERSION = 'v1'

POD_NAME = 'wikimedia_zim'

ZIM_STATUS = "zim.pik"
FILE_STATUS = "file.pik"

fs = None
root = '~/dist'
dirs = '/tmp/wikipedia/zim'

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)

class Resquest(resource.Resource):
	isLeaf = True

	def render_GET(self, request):
		global root

		path = request.prepath.split('?')[0]

		if path.startswith('/api/zimlist'):
			request.responseHeaders.addRawHeader(b"content-type", b"application/json")
			return self.getZimListInfo()

		if path.startswith('/api/zimstatus'):
			relpath = os.path.relpath(path, '/api/zimstatus')
			request.responseHeaders.addRawHeader(b"content-type", b"application/json")
			return self.getZimFileStatus(relpath)

		if path == '/':
			path = '/index.html'

		localpath = os.path.join(root, path.split('/')[1])

		types, encoding = mimetypes.guess_type(path)
		if types is None:
			types = 'text/plain'
			
		request.responseHeaders.addRawHeader(b"content-type", types.encode('utf-8'))

		if os.path.isfile(localpath):
			return self.getFileFromLocal(localpath, types)
		else:
			return self.getFileFromFairOs(path, types)

	#read file from local system
	def getFileFromLocal(self, filepath:str, types:str):
		try:
			with open(filepath, 'rb') as f:
				content = f.read()
			return content
		except:
			return self.notFoundPage()

	#read file from fair os
	def getFileFromFairOs(self, filepath:str, types:str):
		global fs

		try:
			res = fs.download_file(POD_NAME, filepath)
			
			if res['message'] != 'success':
				logging.error(f"read {filepath} from fairos error: {res['message']}")
				return self.notFoundPage()
			
			return res['content']
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
		
		return json.dumps(zimlist).encode('utf-8')

	#get zim file status
	def getZimFileStatus(self, name:str):
		global dirs

		keyname = hashlib.md5(name.encode('utf-8')).hexdigest()
		status = {
			name: check_zim_status(keyname, dirs)
		}

		return json.dumps(status).encode('utf-8')

	#not found page
	def notFoundPage(self):
		return f"<html><body><h4>file is not found</h4></body></html>".encode('utf-8')

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
def check_zim_status(name, dirs):

	pikfile = os.path.join(dirs, ZIM_STATUS)

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f) 
	except:
		return 'waiting'

	if res is None:
		return 'waiting'

	if name not in res:
		return 'waiting'

	try:
		if int(res[name]) > 0:
			return 'uploaded'
		else:
			return 'waiting'
	except:
		return str(res[name])

def update_fairos():
	global fs

	time.sleep(60)

	while True:
		if fs is None:
			time.sleep(60)
			continue

		res = fs.dir_present(POD_NAME, '/')
		if res['message'] != 'success':
			fs.update_cookie(POD_NAME)
		
		fs.sync_pod(POD_NAME)

		time.sleep(20)
		continue		

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	etcdhost = ''
	root = '~/dist'
	dirs = '/tmp/wikipedia/zim'

	try:
		opts, args = getopt.getopt(argv, "h:d:v:u:p:r:", [
			"host=",
			"dirs=",
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
		elif opt in ['--dirs','-d']:
			dirs = arg			
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

	thread = Thread(target = update_fairos).start()

	site = server.Site(Resquest())
	endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
	endpoint.listen(site)
	reactor.run()