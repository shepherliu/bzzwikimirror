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
root = '/dist'

zimStatus = {}
fileList = []

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)

class Resquest(resource.Resource):
	isLeaf = True

	def render_GET(self, request):
		global root

		path = request.path.decode('utf-8').split('?')[0]

		if path.startswith('/api/zimlist'):
			request.responseHeaders.addRawHeader(b"content-type", b"application/json")
			return self.getZimListInfo()
		elif path.startswith('/api/zimstatus'):
			relpath = os.path.relpath(path, '/api/zimstatus')
			request.responseHeaders.addRawHeader(b"content-type", b"application/json")
			return self.getZimFileStatus(relpath)
		elif path.startswith('/api/filelist'):
			relpath = os.path.relpath(path, '/api/filelist')
		elif path.startswith('/api/filesearch'):
			relpath = os.path.relpath(path, '/api/filesearch')
		elif path.startswith('/api/contentsearch'):
			relpath = os.path.relpath(path, '/api/contentsearch')


		if path == '/':
			path = '/index.html'

		localpath = os.path.join(root, path[1:])

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
				timestamp:timestamp,
				status: '',
			})
		
		return json.dumps(zimlist).encode('utf-8')

	#get zim file status
	def getZimFileStatus(self, name:str):

		keyname = hashlib.md5(name.encode('utf-8')).hexdigest()
		status = {
			name: check_zim_status(keyname)
		}

		return json.dumps(status).encode('utf-8')

	#get file list
	def getFileList(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		if len(params) > 0:
			try:
				pageSize = int(params[0])
			except:
				pageSize = 100
		if len(params) > 1:
			try:
				pageCount = int(params[1])
			except:
				pageCount = 0

		start = pageCount * pageSize
		end = start + pageSize

		if end > len(filelist):
			end = len(fileList)

		if start > end:
			start = end

		return json.dumps(fileList[start:end]).encode('utf-8')

	#get file search
	def getFileSearch(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		search = ''
		if len(params) > 0:
			search = params[0]
		if len(params) > 1:
			try:
				pageSize = int(params[1])
			except:
				pageSize = 100
		if len(params) > 2:
			try:
				pageCount = int(params[2])
			except:
				pageCount = 0
		start = pageCount * pageSize
		end = start + pageSize

		total = 0
		tmp = []
		for key in fileList:
			if search == '' or key.find(search) >= 0:
				tmp.append(key)
				total += 1
			if totalcnt >= end:
				break

		if end > len(tmp):
			end = len(tmp)

		if start > end:
			start = end		

		return json.dumps(tmp[start:end]).encode('utf-8')

	#get content search
	def getContentSearch(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		search = ''
		if len(params) > 0:
			search = params[0]
		if len(params) > 1:
			try:
				pageSize = int(params[1])
			except:
				pageSize = 100
		if len(params) > 2:
			try:
				pageCount = int(params[2])
			except:
				pageCount = 0
		start = pageCount * pageSize
		end = start + pageSize

		total = 0
		tmp = []		
		
		return json.dumps(tmp[start:end]).encode('utf-8')

	#not found page
	def notFoundPage(self):
		return f"file is not found".encode('utf-8')

#init fairos module
def init_fairos(username, password, host = FAIROS_HOST, version = FAIROS_VERSION, podname = POD_NAME, sharepod = ''):

	fs = Fairos(host, version)

	#check user present
	userPresent = False

	res = fs.user_present(username)

	if res['message'] != 'success':
		logging.error(f"get user: {username} status error: {res['message']}")
		return None
	else:
		userPresent = res['data']['present']

	#signup user if not exists
	if not userPresent:

		res = fs.signup_user(username, password)

		if res['message'] != 'success':
			logging.error(f"signup user: {username} error: {res['message']}")
			return None
		else:
			logging.info(f"signup user: {username} success")

	#login user
	res = fs.login_user(username, password)

	if res['message'] != 'success':
		logging.error(f"login user: {username} error: {res['message']}")
		return None
	else:
		logging.info(f"login user: {username} success")

	#receive shared pod
	if sharepod != '':
		res = fs.pod_receive(sharepod)

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
def check_zim_status(name):

	global zimStatus

	if zimStatus is None:
		return 'waiting'

	if name not in zimStatus:
		return 'waiting'

	try:
		if int(zimStatus[name]) > 0:
			return 'uploaded'
		else:
			return 'waiting'
	except:
		return str(zimStatus[name])

def update_fairos():
	global fs

	time.sleep(120)

	while True:

		try:
			res = fs.dir_present(POD_NAME, '/')
			if res['message'] != 'success':
				fs.update_cookie(POD_NAME)

			time.sleep(5)
		except:
			time.sleep(5)
			continue	

def update_status():
	global fs
	global zimStatus
	global fileList

	zimpath = os.path.join('/', ZIM_STATUS)
	filepath = os.path.join('/', FILE_STATUS)

	while True:
		try:
			fs.sync_pod(POD_NAME)

			res = fs.download_file(POD_NAME, zimpath)
			if res['message'] == 'success':
				zimStatus = json.loads(res['content'])

			res = fs.download_file(POD_NAME, filepath)
			if res['message'] == 'success':
				data = json.loads(res['content'])
				tmp = []
				for key in data.keys():
					if key.find('/A/') >= 0:
						tmp.append(key)
				fileList = tmp

			time.sleep(3600)
		except:
			time.sleep(120)
			continue

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	etcdhost = ''
	root = '/dist'
	sharepod = ''

	try:
		opts, args = getopt.getopt(argv, "h:v:u:p:r:s:", [
			"host=",
			"version=",
            "user=",
            "password=",
            "root=",
            "sharepod="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--host','-h']:
			host = arg		
		elif opt in ['--version','-v']:
			version = arg
		elif opt in ['--user','-u']:
			user = arg
		elif opt in ['--password','-p']:
			password = arg
		elif opt in ['--root', '-r']:
			root = arg
		elif opt in ['--sharepod', '-s']:
			sharepod = arg			

	if not os.path.exists(root):
		os.makedirs(root)

	fs = init_fairos(user, password, host, version, POD_NAME, sharepod)
	if fs is None:
		sys.exit(-1)

	Thread(target = update_fairos).start()
	Thread(target = update_status).start()

	site = server.Site(Resquest())
	endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
	endpoint.listen(site)
	reactor.run()