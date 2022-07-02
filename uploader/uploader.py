#!/usr/bin/python3 
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import time
import re
import mimetypes
import getopt
import logging
import hashlib
import pathlib
import shutil
from requests_toolbelt import MultipartEncoder

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

SWARM_HOST = 'http://127.0.0.1:1635'
SWARM_BATCH_ID = ''

WAITING_STATUS = "waitting"
DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"
UPLOADED_STATUS = "uploaded"

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)

#upload all files to swarm
def upload_files(name:str, dirs:str):
	totalcnt = 0
	filelist = []

	rootpath = os.path.join(dirs, name)

	#collect file list for the dir
	for root, _, files in os.walk(rootpath):
		relpath = os.path.relpath(root, rootpath)
		relpath = os.path.join(fairpath, relpath)

		for file in files:
			filepath = os.path.join(root, file)
			filelist.append(filepath)

	#upload file list
	for filepath in filelist:
		#check if already upload or not
		relpath = os.path.relpath(os.path.dirname(filepath), rootpath)
		relpath = os.path.join('/', relpath)	

		basename = os.path.basename(filepath)

		relname = os.path.join(relpath, basename)

		ext = 'other'
		if relpath.find('/A/'):
			ext = 'html'	

		md5sum = ''
		with open(filepath, 'rb') as f:
			md5sum = hashlib.md5(f.read()).hexdigest()

		while True:
			session = Session()
			try:
				fileInfo = session.query(FileStatus).filter(FileStatus.name == relname).first()
				if fileInfo is not None and fileInfo.md5 == md5sum:
					totalcnt += 1
					session.close()
					break

				reference = upload_file_to_swarm(filepath)
				#try again
				if reference is None:
					logging.warning(f"upload file: {filepath} to swarm failed")
					session.close()
					time.sleep(5)
					continue

				if fileInfo is None:
					session.add(FileStatus(name = relname, ext = ext, md5 = md5sum, reference = reference))
				else:
					fileInfo.md5 = md5sum
					fileInfo.reference = reference
				
				session.commit()
				totalcnt += 1
				logging.info(f"upload file: {filepath} success, total process: {totalcnt}/{len(filelist)}")
			except:
				session.rollback()
			finally:
				session.close()

	#if all files upload success, update the status of the zim file status
	if totalcnt < len(filelist):
		return False

	return True

def upload_file_to_swarm(filepath):
	basename = os.path.basename(filepath)

	types, encoding = mimetypes.guess_type(filepath)

	m = MultipartEncoder(fields = {
		'name': basename,
		'file': (basename, open(filepath, 'rb'), types)
	})

	headers = {
		'Content-Type': m.content_type,
		'swarm-postage-batch-id': SWARM_BATCH_ID,
		'swarm-collection': False
	}

	res = requests.post(url = f"{SWARM_HOST}/bzz/", headers = headers , data = m)

	if res.status_code >= 200 and res.status_code < 300:
		try:
			return res.json().reference
		except:
			return None

	return None


if __name__ == '__main__':
	argv = sys.argv[1:]

	extract = '/tmp/wikipedia/doc'
	dbname = '/tmp/wikipedia/wikipedia.db'

	#parse agrs
	try:
		opts, args = getopt.getopt(argv, "b:d:e:h:", [
			"batchid=",
			"host=",
            "extract=",
            "dbname"
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--extract', '-e']:
			extract = arg
		elif opt in ['--dbname', '-d']:
			dbname = arg	
		elif opt in ['--batchid', '-b']:
			SWARM_BATCH_ID = arg	
		elif opt in ['--host', '-h']:
			SWARM_HOST = arg									

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
			zimInfo = session.query(ZimStatus).filter(ZimStatus.status == UPLOADING_STATUS).order_by(ZimStatus.timestamp).first();
			if zimInfo is None:
				session.close()
				logging.info("no zim files need to upload")
				time.sleep(120)
				continue
			else:
				res = upload_files(zimInfo.name, extract)
				if res:
					zimInfo.status = UPLOADED_STATUS
					session.commit()
					logging.info(f"update zim file: {zimInfo.name} status to {UPLOADED_STATUS} success")
					shutil.rmtree(os.path.join(extract, zimInfo.name))

					reference = upload_file_to_swarm(dbname)
					if reference is None:
						logging.error(f"update dbname: {dbname} to swarm failed")
					else:		
						session.add(DbStatus(name = dbname, reference = reference, timestamp = int(time.time())))
						logging.info(f"update dbname: {dbname} to swarm success, new reference is: {reference}")			
				else:
					logging.error(f"update zim file: {zimInfo.name} status to {UPLOADED_STATUS} failed")
		except:
			session.rollback()
		finally:
			session.close()

		time.sleep(120)			