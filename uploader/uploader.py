#!/usr/bin/python3 
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import time
import re
import getopt
import enum
import logging
import urllib.parse
import hashlib
import etcd3
from fairos.fairos import Fairos

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

FAIROS_HOST = "https://fairos.fairdatasociety.org"

FAIROS_VERSION = 'v1'

POD_NAME = 'wikimedia_zim'

DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)
#init fairos module
def init_fairos(username, password, host = FAIROS_HOST, version = FAIROS_VERSION, podname = POD_NAME):

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

	#check pod presnet
	podPresent = False

	res = fs.pod_present(podname)

	if res['message'] != 'success':
		logging.error(f"get pod: {podname} status error: {res['message']}")
		return None
	else:
		podPresent = res['data']['present']

	#create a new pod if not exists
	if not podPresent:

		res = fs.new_pod(podname)

		if res['message'] != 'success':
			logging.error(f"create new pod: {podname} error: {res['message']}")
			return None
		else:
			logging.info(f"create new pod: {podname} success")

	#open pod
	res = fs.open_pod(podname)

	if res['message'] != 'success':
		logging.error(f"open pod: {podname} error: {res['message']}")
		return None
	else:
		logging.info(f"open pod: {podname} success")
	
	return fs

#upload all files of the dirs to fairos
def upload_files(name:str, dirs:str, timestamp:int, etcd, fs, podname = POD_NAME):
	totalcnt = 0
	filelist = []

	path = os.path.join(dirs, name)

	#collect file list for the dir
	for root, dirs, files in os.walk(path):
		relpath = os.path.relpath(root, path)
		relpath = os.path.join('/', relpath)

		res = fs.dir_present(podname, relpath)
		if res['message'] != 'success':
			fs.update_cookie()
			logging.error(f"check fairos dir: {relpath} present error: {res['message']}")
			continue

		if res['data']['present'] == False:
			res = fs.make_dir(podname, relpath)

		if res['message'] != 'success':
			fs.update_cookie()
			logging.error(f"create fairos dir: {relpath} error: {res['message']}")
			continue

		for file in files:
			filepath = os.path.join(root, file)
			filelist.append(filepath)

	#upload file list
	for filepath in filelist:
		#check if already upload or not
		md5sum = ''
		with open(filepath, 'rb') as f:
			md5sum = hashlib.md5(f.read()).hexdigest()
		if check_file_status(filepath, md5sum, etcd):
			continue

		#upload file until it is success
		while True:
			relpath = os.path.relpath(os.path.dirname(filepath), path)
			relpath = os.path.join('/', relpath)
			res = fs.upload_file(podname, relpath, filepath)
			if res['message'] != 'success':
				fs.update_cookie()
				logging.error(f"upload fairos file: {filepath} error: {res['message']}")
				continue
			else:
				break

		#update file status until it is success
		while True:
			if update_file_status(filepath, md5sum, etcd) == False:
				logging.error(f"update fairos file: {filepath} status failed")
				continue
			else:
				totalcnt += 1
				logging.info(f"upload fairos file: {filepath} success, total process: {totalcnt}/{len(filelist)}")
				break

	#if all files upload success, update the status of the zim file status
	if totalcnt < len(filelist):
		return False
	else:
		return update_wikipedia_zim_status(name, timestamp, etcd)

#check file status
def check_file_status(filepath:str, md5sum:str, etcd):

	keyname = hashlib.md5(filepath.encode('utf-8')).hexdigest()

	res, _ = etcd.get(keyname)

	if res is None:
		return False
	else:
		res = res.decode('utf-8')		

	return str(res) == md5sum

#update file status
def update_file_status(filepath:str, md5sum:str, etcd):

	keyname = hashlib.md5(filepath.encode('utf-8')).hexdigest()

	etcd.put(keyname, md5sum)

	res, _ = etcd.get(keyname)

	if res is None:
		return False
	else:
		res = res.decode('utf-8')		

	return str(res) == md5sum

#update zim file status
def update_wikipedia_zim_status(name:str, timestamp:int, etcd):

	keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

	etcd.put(keyname, str(timestamp))

	res, _ = etcd.get(keyname)

	if res is None:
		return False
	else:
		res = res.decode('utf-8')		

	return str(res) == str(timestamp)

#check zim status
def check_zim_status(name, etcd):

	res, _ = etcd.get(name)

	if res is None:
		return (None, 'success')
	else:
		res = res.decode('utf-8')		

	try:
		return (int(res), 'success')
	except:
		return (str(res), 'success')	

#parse timestamp
def parse_timestamp(timestamp, timeformat = '%d-%b-%Y %H:%M'):

	t = time.strptime(timestamp, timeformat)

	return int(time.mktime(t))

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

		res.append([name, size, parse_timestamp(timestamp)])
	
	return sorted(res, key = lambda x: x[2])	

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	etcdhost = ''
	dirs = '/tmp/wikipedia/doc'

	#parse args
	try:
		opts, args = getopt.getopt(argv, "h:e:v:u:p:d:", [
			"host=",
			"etcd=",
			"version=",
            "user=",
            "password=",
            "dirs="
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
		elif opt in ['--dirs', '-d']:
			dirs = arg

	while True:

		fs = init_fairos(user, password, host, version)

		if fs is None:
			sys.exit(-1)

		etcd = etcd3.client(host = etcdhost)

		#get all zim file list from the dump website
		dumps = parse_wikipedia_dumps(get_wikipedia_dumps())
		logging.info(f"get wikipedia dumps success, count: {len(dumps)}")

		#check zim file one by one based on the zim timestamp from oldest to newest
		for d in dumps:

			name, size, timestamp = d

			keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

			status, err = check_zim_status(keyname, etcd)

			if err != 'success':
				logging.error(f"check zim: {name} status error: {err}")
				break
			elif status == UPLOADING_STATUS:
				res = upload_files(name, dirs, timestamp, etcd, fs, POD_NAME)
				if res == False:
					logging.warning(f"upload zim: {name} to {dirs} failed")
					break
				else:
					logging.info(f"upload zim: {name} to {dirs} success")
					continue
			elif status == '' or status is None:
				break
			else:
				continue

		time.sleep(300)