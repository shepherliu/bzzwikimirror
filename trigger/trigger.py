#!/usr/bin/python3 
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import time
import re
import getopt
import logging
import urllib.parse

from threading import Thread

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = None
Session = None

class ZimStatus(Base):
	__tablename__ = 'zim_status'
	__table_args__ = {"extend_existing": True}
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(256), index = True)
	size = Column(Integer)
	status = Column(String(32), index = True)
	timestamp = Column(Integer, index = True)

class DbStatus(Base):
	__tablename__ = 'db_status'
	__table_args__ = {"extend_existing": True}
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(256), index = True)
	reference = Column(String(256))
	timestamp = Column(Integer, index = True)	

class FileStatus(Base):
	__tablename__ = 'file_status'
	__table_args__ = {"extend_existing": True}
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(256), index = True)
	ext = Column(String(32), index = True)
	md5 = Column(String(256))
	reference = Column(String(256))

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

WAITING_STATUS = "waitting"
DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"
UPLOADED_STATUS = "uploaded"

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
		size /= 1024.0

	if size < 1024.0:
		return '{0} KB'.format(round(size, 2))
	else:
		size /= 1024.0

	if size < 1024:
		return '{0} MB'.format(round(size, 2))
	else:
		size /= 1024.0

	if size < 1024:
		return '{0} GB'.format(round(size, 2))
	else:
		size /= 1024.0

	if size < 1024:
		return '{0} TB'.format(round(size, 2))
	else:
		size /= 1024.0		

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

		res.append([name, size, parse_timestamp(timestamp)])
	
	return sorted(res, key = lambda x: x[2])

#update zim dump list
def update_zim_dump_list():
	while True:

		try:
			dumps = parse_wikipedia_dumps(get_wikipedia_dumps())

			for d in dumps:
				session = Session()
				name, size, timestamp = d

				try:
					zimInfo = session.query(ZimStatus).filter(ZimStatus.name == name).first()
					if zimInfo is None:
						session.add(ZimStatus(name = name, size = size, timestamp = timestamp, status = WAITING_STATUS))
						session.commit()
						logging.info(f"add new zim file: {name}, size: {parse_size(size)}, time:{timestamp}, status: {WAITING_STATUS}")
					elif zimInfo.timestamp > timestamp or zimInfo.size != size:
						session.query(ZimStatus).filter(ZimStatus.name == name).update({ZimStatus.size: size, ZimStatus.timestamp: timestamp, ZimStatus.status: WAITING_STATUS})
						session.commit()
						logging.info(f"update new zim file: {name}, size: {parse_size(size)}, time:{timestamp}, status: {WAITING_STATUS}")
				except:
					logging.error(f"update zim file: {name} status failed")
				finally:
					session.close()
		except:
			time.sleep(3600)

		#update every day
		time.sleep(86400)

#trigger a zim file to downloading status
def trigger_wikipedia_downloading():
	session = Session()

	try:
		zimInfos = session.query(ZimStatus).order_by(ZimStatus.timestamp).all();
		if zimInfos is None:
			session.close()
			return

		for info in zimInfos:
			if info.status == UPLOADED_STATUS:
				continue
			elif info.status == WAITING_STATUS:
				session.query(ZimStatus).filter(ZimStatus.name == info.name).update({ZimStatus.status: DOWNLOADING_STATUS})
				session.commit()
				logging.info(f"trigger zim file: {info.name} status to {DOWNLOADING_STATUS}")
				break
			else:
				logging.info(f"zim file: {info.name} status now is {info.status}")
				break
	except:
		session.rollback()
	finally:
		session.close()

if __name__ == '__main__':
	argv = sys.argv[1:]

	dbname = '/tmp/wikipedia/wikipedia.db'
	#parse args
	try:
		opts, args = getopt.getopt(argv, "d:", [
            "dbname="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--dbname','-d']:
			dbname = arg

	#create new sqlite engine
	engine = create_engine(f"sqlite:///{dbname}?check_same_thread=False", echo=False)

	#create tables if not exists
	Base.metadata.create_all(engine, checkfirst=True)

	#create Session maker
	Session = sessionmaker(bind = engine)

	#start a thread to update zim list from dumps.wikimedia.org
	Thread(target = update_zim_dump_list).start()

	#trigger a zim file to uploading status
	while True:

		trigger_wikipedia_downloading()

		time.sleep(120)