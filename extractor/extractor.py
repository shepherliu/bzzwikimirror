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

	res = etcd.get(name)

	try:
		return (int(res), 'success')
	except:
		return (res, 'success')

#extract zim file to dst dirs using zimdump
def extract_wikipedia_zim(name, src, dst, etcd):

	srcpath = os.path.join(src, name)

	if not os.path.exists(srcpath):
		return False

	if re.match('^[a-zA-Z0-9]', name) is None:
		return False

	dstpath = os.path.join(dst, name)
	if os.path.exists(dstpath):
		os.removedirs(dstpath)

	cmd = '~/zim-tools_linux-x86_64-3.1.1/zimdump dump --dir={0} {1}'.format(dstpath, srcpath)
	res = subprocess.Popen(cmd, shell = True, stdout = None, stderr = None).wait()

	if res != 0:
		return False

	keyname = hashlib.md5(name.encode('utf-8')).hexdigest()

	return update_wikipedia_zim_status(keyname, etcd)

#update zim file status to UPLOADING_STATUS
def update_wikipedia_zim_status(name, etcd):

	etcd.put(name, UPLOADING_STATUS)

	res = etcd.get(name)

	return res == UPLOADING_STATUS

if __name__ == '__main__':
	argv = sys.argv[1:]

	host = ''
	src = '/tmp/wikipedia/zim'
	dst = '/tmp/wikipedia/doc'

	#parse agrs
	try:
		opts, args = getopt.getopt(argv, "h:d:s:", [
			"host=",
            "src=",
            "dst="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--host','-h']:
			host = arg
		elif opt in ['--src', '-s']:
			src = arg
		elif opt in ['--dst', '-d']:
			dst = arg

	#make dst dirs
	try:
		os.makedirs(dst)
	except:
		if not os.path.exists(dst):
			logging.error(f"make extract dirs: {dst} failed")
			sys.exit(-1)

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
			elif status == EXTRACTING_STATUS:
				res = extract_wikipedia_zim(name, src, dst, etcd)
				if res:
					logging.info(f"extract zim: {name} to {dst} success")
				else:
					logging.warning(f"extract zim: {name} to {dst} failed")
				break
			elif status == '' or status is None:
				break
			else:
				continue

		time.sleep(300)