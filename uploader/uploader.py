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

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)
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

#upload all files of the dirs to fairos
def upload_files(name:str, dirs:str, timestamp:int, src, fs, podname = POD_NAME):
	totalcnt = 0
	filelist = []

	fs.make_dir(podname, '/'+name)

	path = os.path.join(dirs, name)

	status = load_wikipedia_file_status(src, fs, podname)

	#collect file list for the dir
	for root, _, files in os.walk(path):
		relpath = os.path.relpath(root, dirs)
		relpath = os.path.join('/', relpath)

		res = fs.dir_present(podname, relpath)
		if res['message'] != 'success':
			fs.update_cookie(podname)
			logging.error(f"check fairos dir: {relpath} present error: {res['message']}")
			continue

		if res['data']['present'] == False:
			res = fs.make_dir(podname, relpath)

		if res['message'] != 'success':
			fs.update_cookie(podname)
			logging.error(f"create fairos dir: {relpath} error: {res['message']}")
			continue

		for file in files:
			filepath = os.path.join(root, file)
			filelist.append(filepath)

	#upload file list
	for filepath in filelist:
		#check if already upload or not
		relpath = os.path.relpath(os.path.dirname(filepath), dirs)
		relpath = os.path.join('/', relpath)	
		basename = os.path.basebame(filepath)
		relname = os.path.join(relpath, basebame)	

		md5sum = ''
		with open(filepath, 'rb') as f:
			md5sum = hashlib.md5(f.read()).hexdigest()
		if check_file_status(relname, md5sum, status):
			continue

		#upload file until it is success
		while True:
			res = fs.upload_file(podname, relpath, filepath)
			if res['message'] != 'success':
				fs.update_cookie(podname)
				logging.error(f"upload fairos file: {filepath} error: {res['message']}")
				continue
			else:
				break

		#update file status until it is success
		while True:
			if update_file_status(relname, md5sum, status) == False:
				logging.error(f"update fairos file: {filepath} status failed")
				continue
			else:
				totalcnt += 1
				logging.info(f"upload fairos file: {filepath} success, total process: {totalcnt}/{len(filelist)}")
				break

	#if all files upload success, update the status of the zim file status
	if totalcnt < len(filelist):
		return False

	if update_wikipedia_zim_status(name, timestamp, src, fs, podname):
		return update_wikipedia_file_status(src, fs, podname)

	return False

#check file status
def check_file_status(filepath:str, md5sum:str, status):

	# keyname = hashlib.md5(filepath.encode('utf-8')).hexdigest()

	if filepath not in status:
		return False

	return str(status[filepath]) == md5sum

#update file status
def update_file_status(filepath:str, md5sum:str, status):

	# keyname = hashlib.md5(filepath.encode('utf-8')).hexdigest()

	status[filepath] = md5sum

	return True

#update zim file status
def update_wikipedia_zim_status(name:str, timestamp:int, dirs, fs, podname = POD_NAME):

	keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

	pikfile = os.path.join(dirs, ZIM_STATUS)

	zimpath = os.path.join('/', ZIM_STATUS)

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f)
			res[name] = timestamp
		with open(pikfile, 'wb') as f:
			pickle.dump(res, f)
		res = fs.upload_file(podname, zimpath, pikfile)
		if res['message'] != 'success':
			fs.update_cookie(podname)
			return False
		return True
	except:
		return False

#update file status to fairos
def update_wikipedia_file_status(dirs, fs, podname = POD_NAME):

	pikfile = os.path.join(dirs, FILE_STATUS)

	filepath = os.path.join('/', FILE_STATUS)

	try:
		res = fs.upload_file(podname, filepath, pikfile)
		if res['message'] != 'success':
			fs.update_cookie(podname)
			return False
		return True
	except:
		return False

def load_wikipedia_file_status(dirs, fs, podname = POD_NAME):

	while True:
		pikfile = os.path.join(dirs, FILE_STATUS)
		if os.path.isfile(pikfile):
			with open(pikfile, 'rb') as f:
				return pikfile.load(f)

		filepath = os.path.join('/', FILE_STATUS)
		res = fs.dir_present(podname, filepath)
		if res['message'] != 'success':
			fs.update_cookie(podname)
			continue

		if res['data']['present'] == False:
			return {}

		res = fs.download_file(podname, filepath)
		if res['message'] != 'success':
			fs.update_cookie(podname)
			continue

		with open(pikfile, 'wb') as f:
			f.write(res['content'])

		with open(pikfile, 'rb') as f:
			return pickle.load(f)

#check zim status
def check_zim_status(name, dirs):

	pikfile = os.path.join(dirs, ZIM_STATUS)

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f) 
	except:
		return (None, 'open zim status file failed')

	if res is None:
		return (None, 'success')

	if name not in res:
		return (None, 'success')

	try:
		return (int(res[name]), 'success')
	except:
		return (str(res[name]), 'success')

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
	src = '/tmp/wikipedia/zim'
	dirs = '/tmp/wikipedia/doc'

	#parse args
	try:
		opts, args = getopt.getopt(argv, "h:v:u:p:d:s:", [
			"host=",
			"version=",
            "user=",
            "password=",
            "dirs=",
            "src="
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
		elif opt in ['--src', '-s']:
			src = arg

	while True:

		fs = init_fairos(user, password, host, version)

		if fs is None:
			sys.exit(-1)

		#get all zim file list from the dump website
		dumps = parse_wikipedia_dumps(get_wikipedia_dumps())
		logging.info(f"get wikipedia dumps success, count: {len(dumps)}")

		#check zim file one by one based on the zim timestamp from oldest to newest
		for d in dumps:

			name, size, timestamp = d

			keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

			status, err = check_zim_status(keyname, src)

			if err != 'success':
				logging.error(f"check zim: {name} status error: {err}")
				break
			elif status == UPLOADING_STATUS:
				res = upload_files(name, dirs, timestamp, src, fs, POD_NAME)
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

		time.sleep(120)