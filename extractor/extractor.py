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
import subprocess

from fairos.fairos import Fairos

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

FAIROS_HOST = "https://fairos.fairdatasociety.org"

FAIROS_VERSION = 'v1'

POD_NAME = 'wikimedia_zim'

TABLE_ZIM = 'zim_status'

TABLE_FILE = 'file_status'

TABLE_INDEX = 'index_status'


DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
ENHANCING_STATUS = "enhancing"
UPLOADING_STATUS = "uploading"


logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)
#init fairos module
def init_fairos(username, password, host = FAIROS_HOST, version = FAIROS_VERSION, podname = POD_NAME, tablename = TABLE_ZIM):

	fs = Fairos(host, version)

	#login user
	res = fs.login_user(username, password)

	if res['message'] != 'success':
		logging.error(f"login user: {username} error: {ret['message']}")
		return None
	else:
		logging.info(f"login user: {username} success")

	#open pod
	res = fs.open_pod(podname)

	if res['message'] != 'success':
		logging.error(f"open pod: {podname} error: {ret['message']}")
		return None
	else:
		logging.info(f"open pod: {podname} success")
	
	#open table
	res = fs.open_table(podname, tablename)

	if res['message'] != 'success':
		logging.error(f"open table: {tablename} error: {ret['message']}")
		return None
	else:
		logging.info(f"open table: {tablename} success")
	
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
def check_zim_status(name, fs, podname = POD_NAME, tablename = TABLE_ZIM):

	keyPresent = False
	
	res = fs.key_present(podname, tablename, name)
	if res['message'] != 'success':
		return (None, ret['message'])

	keyPresent = res['data']['present']
	if not keyPresent:
		return (None, 'success')

	res = fs.get_value(podname, tablename, name)
	if res['message'] != 'success':
		return (None, ret['message'])

	if res['data']['values'] is None:
		return (None, 'success')

	try:
		return (int(res['data']['values']), 'success')
	except:
		return (res['data']['values'], 'success')

def extract_wikipedia_zim(name, src, dst, fs, podname = POD_NAME, tablename = TABLE_ZIM):

	srcpath = os.path.join(src, name)

	if not os.path.exists(srcpath):
		return False

	if re.match('^[a-zA-Z0-9]', name) is None:
		return False

	dstpath = os.path.join(dst, name.split('.')[0])
	if os.path.exists(dstpath):
		os.removedirs(dstpath)

	cmd = '~/zim-tools_linux-x86_64-3.1.1/zimdump dump --dir={0} {1}'.format(dstpath, srcpath)
	res = subprocess.Popen(cmd, shell = True, stdout = None, stderr = None).wait()

	if res != 0:
		return False

	keyname = urllib.parse.quote(name)
	return update_wikipedia_zim_status(keyname, fs, podname, tablename)

def update_wikipedia_zim_status(name, fs, podname = POD_NAME, tablename = TABLE_ZIM):

	fs.put_key_value(podname, tablename, name, ENHANCING_STATUS)

	res = fs.get_value(podname, tablename, name)

	if res['message'] != 'success':
		return False

	if len(res['data']['values']) < 1:
		return False

	if res['data']['values'] == ENHANCING_STATUS:
		return True

	return False

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	src = '/tmp/wikipedia/zim'
	dst = '/tmp/wikipedia/doc'

	try:
		opts, args = getopt.getopt(argv, "h:v:u:p:d:s:", [
			"host=",
			"version=",
            "user=",
            "password=",
            "src=",
            "dst="
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
		elif opt in ['--src', '-s']:
			src = arg
		elif opt in ['--dst', '-d']:
			dst = arg

	try:
		os.makedirs(dst)
	except:
		if not os.path.exists(dst):
			logging.error(f"make extract dirs: {dst} failed")
			sys.exit(-1)

	while True:

		fs = init_fairos(user, password, host, version)

		if fs is None:
			sys.exit(-1)

		#get all zim file list from the dump website
		dumps = parse_wikipedia_dumps(get_wikipedia_dumps())
		logging.info(f"get wikipedia dumps success, count: {len(dumps)}")

		for d in dumps:

			name, size, timestamp = d

			keyname = urllib.parse.quote(name)

			status, err = check_zim_status(keyname, fs)

			if err != 'success':
				logging.error(f"check zim: {name} status error: {err}")
				break
			elif status == EXTRACTING_STATUS:
				res = extract_wikipedia_zim(name, src, dst, fs)
				if res:
					logging.info(f"extract zim: {name} to {dst} success")
				else:
					logging.warning(f"extract zim: {name} to {dst} failed")
				break
			else:
				logging.info(f"zim: {name} status now is {status}")
				continue

		time.sleep(300)