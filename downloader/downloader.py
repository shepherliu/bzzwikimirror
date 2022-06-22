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
from urllib.request import urlretrieve
import _pickle as pickle

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"

ZIM_STATUS = "zim.pik"
FILE_STATUS = "file.pik"


logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)
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
		return (None, 'open zim status file failed')

	if res is None:
		return (None, 'success')

	if name not in res:
		return (None, 'success')

	try:
		return (int(res[name]), 'success')
	except:
		return (str(res[name]), 'success')

#download zim file from the wikidumps website
def download_wikipedia_zim(name, dirs):

	filepath = os.path.join(dirs, name)

	if os.path.exists(filepath):
		os.remove(filepath)

	url = WIKIPEDIA_HOST + name

	def callbackfunc(blocknum, blocksize, totalsize):

		percent = 100.0 * blocknum * blocksize / totalsize

		if percent > 100:
			percent = 100

		percent = round(percent, 2)

		logging.info(f"downloading {name} to {dirs} in process {percent}%")


	try:
		urlretrieve(url, filepath, callbackfunc)
	except:
		return False

	if not os.path.exists(filepath):
		return False

	keyname = hashlib.md5(name.encode('utf-8')).hexdigest()
	
	return update_wikipedia_zim_status(keyname, dirs)

#update wiki zim file status to EXTRACTING_STATUS
def update_wikipedia_zim_status(name, etcd):

	pikfile = os.path.join(dirs, ZIM_STATUS)

	try:
		with open(pikfile, 'rb') as f:
			res = pickle.load(f)
			res[name] = EXTRACTING_STATUS
		with open(pikfile, 'wb') as f:
			pickle.dump(res, f)
		return True
	except:
		return False

if __name__ == '__main__':
	argv = sys.argv[1:]

	dirs = '/tmp/wikipedia/zim'

	#parse args
	try:
		opts, args = getopt.getopt(argv, "d:", [
            "dirs="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--dirs', '-d']:
			dirs = arg

	#make download dirs
	try:
		os.makedirs(dirs)
	except:
		if not os.path.exists(dirs):
			logging.error(f"make download dirs: {dirs} failed")
			sys.exit(-1)

	while True:

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
			elif status == DOWNLOADING_STATUS:
				res = download_wikipedia_zim(name, dirs)
				if res:
					logging.info(f"download zim: {name} to {dirs} success")
				else:
					logging.warning(f"download zim: {name} to {dirs} failed")
				break
			elif status == '' or status is None:
				break
			else:
				continue

		time.sleep(300)