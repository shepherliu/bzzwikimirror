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
import _pickle as pickle
from threading import Thread

from fairos.fairos import Fairos

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

FAIROS_HOST = "https://fairos.fairdatasociety.org"

FAIROS_VERSION = 'v1'

POD_NAME = 'wikimedia_zim'

DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"

ZIM_STATUS = "zim.pik"
FILE_STATUS = "file.pik"

fs = None

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

		res.append([name, parse_size(float(size)), parse_timestamp(timestamp)])
	
	return sorted(res, key = lambda x: x[2])

#check zim status
def check_zim_status(name, dirs):
	pikfile = os.path.join(dirs, ZIM_STATUS)

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f) 
	except:
		res = {}

	if res is None:
		return (None, 'success')

	if name not in res:
		return (None, 'success')

	try:
		return (int(res[name]), 'success')
	except:
		return (str(res[name]), 'success')

def download_zim_status_file(dirs, fs, podname = POD_NAME):
	pikfile = os.path.join(dirs, ZIM_STATUS)
	if os.path.isfile(pikfile):
		return True

	zimpath = os.path.join('/', ZIM_STATUS)

	res = fs.dir_present(podname, zimpath)
	if res['message'] != 'success':
		return False

	if res['data']['present'] == False:
		return True

	res = fs.download_file(podname, zimpath)
	if res['message'] != 'success':
		return False

	try:
		with open(pikfile, 'wb') as f:
			f.write(res['content'])
		return True
	except:
		return False


#update zim file status to DOWNLOADING_STATUS
def trigger_wikipedia_update(name, dirs):

	pikfile = os.path.join(dirs, ZIM_STATUS)

	if not os.path.isfile(pikfile):
		res = {name: DOWNLOADING_STATUS}
		try:
			with open(pikfile, 'wb') as f:
				pickle.dump(res, f)
			return True
		except:
			return False

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f)
			res[name] = DOWNLOADING_STATUS
		with open(pikfile, 'wb') as f:
			pickle.dump(res, f)
		return True
	except:
		return False

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
	dirs = '/tmp/wikipedia/zim'
	#parse args
	try:
		opts, args = getopt.getopt(argv, "h:v:u:p:d:", [
			"host=",
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
		elif opt in ['--version','-v']:
			version = arg
		elif opt in ['--user','-u']:
			user = arg
		elif opt in ['--password','-p']:
			password = arg
		elif opt in ['--dirs', '-d']:
			dirs = arg

	fs = init_fairos(user, password, host, version)

	if fs is None:
		sys.exit(-1)			

	thread = Thread(target = update_fairos).start()

	while True:

		if download_zim_status_file(dirs, fs, POD_NAME)	== False:
			continue

		#get all zim file list from the dump website
		dumps = parse_wikipedia_dumps(get_wikipedia_dumps())
		logging.info(f"get wikipedia dumps success, count: {len(dumps)}")

		#check zim file one by one based on the zim timestamp from oldest to newest
		for d in dumps:

			name, size, timestamp = d

			keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

			status, err = check_zim_status(keyname, dirs)

			if err != 'success':
				logging.error(f"check zim: {name} status error: {err}")
				break
			elif status == '' or status is None:
				res = trigger_wikipedia_update(keyname, dirs)
				if res:
					logging.info(f"trigger zim: {name} to update to downloading success")
				else:
					logging.warning(f"trigger zim: {name} to update to downloading failed")
				break				
			elif status == DOWNLOADING_STATUS:
				logging.info(f"zim: {name} status now is {status}")
				break
			elif status == EXTRACTING_STATUS:
				logging.info(f"zim: {name} status now is {status}")
				break
			elif status == UPLOADING_STATUS:
				logging.info(f"zim: {name} status now is {status}")
				break
			elif type(status) == int and status < timestamp:
				res = trigger_wikipedia_update(keyname, dirs)
				if res:
					logging.info(f"trigger zim: {name} to update to downloading success")
				else:
					logging.warning(f"trigger zim: {name} to update to downloading failed")
				break				
			else:
				continue

		time.sleep(120)