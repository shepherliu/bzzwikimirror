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
import shutil

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

#extract zim file to dst dirs using zimdump
def extract_wikipedia_zim(name, src, dst):

	srcpath = os.path.join(src, name)

	if not os.path.exists(srcpath):
		return False

	if re.match('^[a-zA-Z0-9]', name) is None:
		return False

	dstpath = os.path.join(dst, name)
	if os.path.exists(dstpath):
		shutil.rmtree(dstpath)

	cmd = '~/zim-tools_linux-x86_64-3.1.1/zimdump dump --dir={0} {1}'.format(dstpath, srcpath)
	res = subprocess.Popen(cmd, shell = True, stdout = None, stderr = None).wait()

	if res != 0:
		return False

	return True

if __name__ == '__main__':
	argv = sys.argv[1:]

	src = '/tmp/wikipedia/zim'
	extract = '/tmp/wikipedia/doc'
	dbname = '/tmp/wikipedia/wikipedia.db'

	#parse agrs
	try:
		opts, args = getopt.getopt(argv, "d:e:s:", [
            "src=",
            "extract=",
            "dbname"
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--src', '-s']:
			src = arg
		elif opt in ['--extract', '-e']:
			extract = arg
		elif opt in ['--dbname', '-d']:
			dbname = arg			

	#make dst dirs
	try:
		os.makedirs(extract)
	except:
		if not os.path.exists(extract):
			logging.error(f"make extract dirs: {extract} failed")
			sys.exit(-1)

	#create new sqlite engine
	engine = create_engine(f"sqlite:///{dbname}?check_same_thread=False", echo=False)

	#create Session maker
	Session = sessionmaker(bind = engine)

	while True:

		session = Session()

		try:
			zimInfo = session.query(ZimStatus).filter(ZimStatus.status == EXTRACTING_STATUS).order_by(ZimStatus.timestamp).first();
			if zimInfo is None:
				session.close()
				logging.info("no zim files need to extract")
				time.sleep(120)
				continue
			else:
				res = extract_wikipedia_zim(zimInfo.name, src, extract)
				if res:
					zimInfo.status = UPLOADING_STATUS
					session.commit()
					shutil.rmtree(os.path.join(src, zimInfo.name))
					logging.info(f"update zim file: {zimInfo.name} status to {UPLOADING_STATUS} success")
				else:
					logging.error(f"update zim file: {zimInfo.name} status to {UPLOADING_STATUS} failed")
		except:
			session.rollback()
		finally:
			session.close()

		time.sleep(120)