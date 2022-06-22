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

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"

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

#update zim file status to DOWNLOADING_STATUS
def trigger_wikipedia_update(name, etcd):

	etcd.put(name, DOWNLOADING_STATUS)

	res, _ = etcd.get(name)

	if res is None:
		return False
	else:
		res = res.decode('utf-8')		

	return str(res) == DOWNLOADING_STATUS

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = ''
	#parse args
	try:
		opts, args = getopt.getopt(argv, "h:", [
			"host="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--host','-h']:
			host = arg

	while True:

		etcd = etcd3.client(host = host)

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
			elif status == '' or status is None:
				res = trigger_wikipedia_update(keyname, etcd)
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
				res = trigger_wikipedia_update(keyname, etcd)
				if res:
					logging.info(f"trigger zim: {name} to update to downloading success")
				else:
					logging.warning(f"trigger zim: {name} to update to downloading failed")
				break				
			else:
				continue

		time.sleep(300)