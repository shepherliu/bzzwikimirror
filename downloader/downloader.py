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

	return True


if __name__ == '__main__':
	argv = sys.argv[1:]

	src = '/tmp/wikipedia/zim'
	dbname = '/tmp/wikipedia/wikipedia.db'

	#parse args
	try:
		opts, args = getopt.getopt(argv, "d:r:", [
            "dbname=",
            "src="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--dbname', '-d']:
			dbname = arg
		elif opt in ['--src', '-s']:
			src = arg			

	#make download src dirs
	try:
		os.makedirs(src)
	except:
		if not os.path.exists(src):
			logging.error(f"make download dirs: {src} failed")
			sys.exit(-1)

	#create new sqlite engine
	engine = create_engine(f"sqlite:///{dbname}?check_same_thread=False", echo=False)

	#create Session maker
	Session = sessionmaker(bind = engine)			

	while True:

		session = Session()

		try:
			zimInfo = session.query(ZimStatus).filter(ZimStatus.status == DOWNLOADING_STATUS).order_by(ZimStatus.timestamp).first();
			if zimInfo is None:
				session.close()
				logging.info("no zim files need to download")
				time.sleep(120)
				continue
			else:
				res = download_wikipedia_zim(zimInfo.name, src)
				if res:
					zimInfo.status = EXTRACTING_STATUS
					session.commit()
					logging.info(f"update zim file: {zimInfo.name} status to {zimInfo.status} success")
				else:
					logging.error(f"update zim file: {zimInfo.name} status to {zimInfo.status} failed")
		except:
			session.rollback()
		finally:
			session.close()

		time.sleep(120)