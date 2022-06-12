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

def upload_files(name:str, dirs:str, timestamp:int, fs, podname = POD_NAME):
	totalcnt = 0
	filelist = []

	path = os.path.join(dirs, name.split('.')[0])

	res = fs.open_table(podname, TABLE_FILE)
	if res['message'] != 'success':
		logging.error(f"open fairos table: {TABLE_FILE}" error: {res['message']})
		return False

	for root, dirs, files in os.walk(path):
		relpath = os.path.relpath(root, path)
		relpath = os.path.join('/', relpath)

		res = fs.dir_present(podname, relpath)
		if res['message'] != 'success':
			logging.error(f"check fairos dir: {relpath} present error: {res['message']}")
			continue

		if res['data']['present'] == False:
			res = fs.make_dir(podname, relpath)

		if res['message'] != 'success':
			logging.error(f"create fairos dir: {relpath} error: {res['message']}")
			continue

		for file in files:
			filepath = os.path.join(root, file)
			filelist.append(filepath)

	for filepath in filelist:
		md5sum = ''
		with open(filepath, 'rb') as f:
			md5sum = hashlib.md5(f.read()).hexdigest()
		if check_file_status(filepath, md5sum, fs, podname, TABLE_FILE):
			continue
		res = fs.upload_file(podname, relpath, filepath)
		if res['message'] != 'success':
			logging.error(f"upload fairos file: {filepath} error: {res['message']}")
			continue
		if update_file_status(filepath, md5sum, fs, podname, TABLE_FILE) == False:
			logging.error(f"update fairos file: {filepath} status failed")
			continue
		else:
			totalcnt += 1
			logging.info(f"upload fairos file: {filepath} success, total process: {totalcnt}/{len(filelist)}")
			continue

	if totalcnt < len(filelist):
		return False
	else:
		return update_wikipedia_zim_status(name, timestamp, fs, podname, TABLE_ZIM)

def check_file_status(filepath:str, md5sum:str, fs, podname = POD_NAME, tablename = TABLE_FILE):

	keyname = urllib.parse.quote(filepath)	

	res = fs.get_value(podname, tablename, keyname)

	if res['message'] != 'success':
		return False

	if len(res['data']['values']) < 1:
		return False

	return res['data']['values'] == md5sum

def update_file_status(filepath:str, md5sum:str, fs, podname = POD_NAME, tablename = TABLE_FILE):

	keyname = urllib.parse.quote(filepath)	

	fs.put_key_value(podname, tablename, keyname, md5sum)

	res = fs.get_value(podname, tablename, keyname)

	if res['message'] != 'success':
		return False

	if len(res['data']['values']) < 1:
		return False

	return res['data']['values'] == md5sum

def update_wikipedia_zim_status(name:str, timestamp:int, fs, podname = POD_NAME, tablename = TABLE_ZIM):

	res = fs.open_table(podname, tablename)
	if res['message'] != 'success':
		logging.error(f"open fairos table: {tablename}" error: {res['message']})
		return False

	keyname = urllib.parse.quote(name)	
	fs.put_key_value(podname, tablename, keyname, str(timestamp))

	res = fs.get_value(podname, tablename, keyname)

	if res['message'] != 'success':
		return False

	if len(res['data']['values']) < 1:
		return False

	if res['data']['values'] == str(timestamp):
		return True

	return False	

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = FAIROS_HOST
	version = FAIROS_VERSION
	user = ''
	password = ''
	dirs = '/tmp/wikipedia/zim'

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
			elif status.startswith(UPLOADING_STATUS):
				res = upload_files(name, dirs, timestamp, fs, POD_NAME)
				if res == False:
					logging.warning(f"upload zim: {name} to {dirs} failed")
					break
				else:
					logging.info(f"upload zim: {name} to {dirs} success")
					continue
			else:
				logging.info(f"zim: {name} status now is {status}")
				continue

		time.sleep(300)		