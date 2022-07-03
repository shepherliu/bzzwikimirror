#!/usr/bin/python3 
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import re
import getopt
import logging
import mimetypes
import requests
import hashlib
import pathlib
import urllib.parse
from functools import lru_cache

from twisted.web import server, resource
from twisted.internet import reactor, endpoints

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, and_

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

SWARM_HOST = 'http://127.0.0.1:1635'

WIKIPEDIA_HOST = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/"

WAITING_STATUS = "waitting"
DOWNLOADING_STATUS = "downloading" 
EXTRACTING_STATUS = "extracting"
UPLOADING_STATUS = "uploading"
UPLOADED_STATUS = "uploaded"

root = '/dist'

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', level=logging.INFO)

class Resquest(resource.Resource):
	isLeaf = True

	def render_GET(self, request):
		global root

		path = request.path.decode('utf-8').split('?')[0]

		path = urllib.parse.unquote(path)

		if path.startswith('/api/'):

			if path.startswith('/api/zimlist'):
				request.responseHeaders.addRawHeader(b"content-type", b"application/json")
				return self.getZimListInfo()
			elif path.startswith('/api/database'):
				request.responseHeaders.addRawHeader(b"content-type", b"application/octet-stream")
				return self.getDatabase()
			elif path.startswith('/api/filelist'):
				request.responseHeaders.addRawHeader(b"content-type", b"application/json")
				relpath = os.path.relpath(path, '/api/filelist')
				return self.getFileList(relpath)
			elif path.startswith('/api/filesearch'):
				request.responseHeaders.addRawHeader(b"content-type", b"application/json")
				relpath = os.path.relpath(path, '/api/filesearch')
				return self.getFileSearch(relpath)
			elif path.startswith('/api/contentsearch'):
				request.responseHeaders.addRawHeader(b"content-type", b"application/json")
				relpath = os.path.relpath(path, '/api/contentsearch')
				return self.getContentSearch(relpath)

		if path == '/':
			path = '/index.html'

		localpath = os.path.join(root, path[1:])

		types, encoding = mimetypes.guess_type(path)
		if types is None:
			types = 'text/plain'
			
		request.responseHeaders.addRawHeader(b"content-type", types.encode('utf-8'))

		if os.path.isfile(localpath):
			return self.getFileFromLocal(localpath)
		else:
			return self.getFileFromSwarm(path)

	#read file from local system
	def getFileFromLocal(self, filepath:str):
		try:
			with open(filepath, 'rb') as f:
				content = f.read()
			return content
		except:
			return self.notFoundPage()

	#read file from swarm
	@lru_cache(maxsize=1024, typed=False)
	def getFileFromSwarm(self, filepath:str):
		session = Session()

		try:
			fileInfo = session.query(FileStatus).filter(FileStatus.name == filepath).first()
			if fileInfo is None:
				session.close()
				return self.notFoundPage()

			url = f"{SWARM_HOST}/bytes/{fileInfo.reference}"

			res = requests.get(url)
			
			if res.status_code >= 200 and res.status_code < 300:
				session.close()
				return res.content
			else:
				logging.error(f"read {filepath} from swarm error: {res.text}")
				session.close()
				return self.notFoundPage()
		except:
			session.close()
			return self.notFoundPage()

	#get zim list info
	def getZimListInfo(self):
		zimlist = []
		session = Session()

		try:
			zimInfos = session.query(ZimStatus).order_by(ZimStatus.timestamp).all()
			if zimInfos is not None:
				for info in zimInfos:
					zimlist.append({
						'name': info.name,
						'size': parse_size(info.size),
						'timestamp': parse_timestamp(info.timestamp),
						'status': info.status
					})
		except:
			zimlist = []
		finally:
			session.close()
		
		return json.dumps(zimlist).encode('utf-8')

	#get latest database 
	def getDatabase(self):
		session = Session()

		try:
			dbInfo = session.query(DbStatus).order_by(desc(DbStatus.timestamp)).first()
			if dbInfo is None:
				session.close()
				return self.notFoundPage()
			else:
				session.close()

				url = f"{SWARM_HOST}/bytes/{dbInfo.reference}"

				res = requests.get(url)
				
				if res.status_code >= 200 and res.status_code < 300:
					session.close()
					return res.content
				else:
					logging.error(f"read database from swarm error: {res.text}")
					session.close()
					return self.notFoundPage()				
		except:
			session.close()
			return self.notFoundPage()

	#get file list
	def getFileList(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		if len(params) > 0:
			try:
				pageSize = int(params[0])
			except:
				pageSize = 100
		if len(params) > 1:
			try:
				pageCount = int(params[1])
			except:
				pageCount = 0

		offset = pageCount * pageSize

		fileList = []
		session = Session()

		try:
			fileInfos = session.query(FileStatus).filter(FileStatus.ext == 'document').order_by(FileStatus.name).offset(offset).limit(pageSize).all()
			if fileInfos is not None:
				for info in fileInfos:
					fileList.append({
						'name':  pathlib.Path(info.name).stem,
						'link': info.name
					})
		except:
			fileList = []
		finally:
			session.close()

		return json.dumps(fileList).encode('utf-8')

	#get file search
	def getFileSearch(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		search = ''
		if len(params) > 0:
			search = params[0]
		if len(params) > 1:
			try:
				pageSize = int(params[1])
			except:
				pageSize = 100
		if len(params) > 2:
			try:
				pageCount = int(params[2])
			except:
				pageCount = 0
		offset = pageCount * pageSize

		fileList = []
		session = Session()

		try:
			fileInfos = session.query(FileStatus).filter(and_(FileStatus.ext == 'document', FileStatus.name.like(f"%{search}%"))).order_by(FileStatus.name).offset(offset).limit(pageSize).all()
			if fileInfos is not None:
				for info in fileInfos:
					fileList.append({
						'name':  pathlib.Path(info.name).stem,
						'link': info.name
					})
		except:
			fileList = []
		finally:
			session.close()		

		return json.dumps(fileList).encode('utf-8')

	#get content search
	def getContentSearch(self, path):
		params = path.split('/')
		pageSize = 100
		pageCount = 0
		search = ''
		if len(params) > 0:
			search = params[0]
		if len(params) > 1:
			try:
				pageSize = int(params[1])
			except:
				pageSize = 100
		if len(params) > 2:
			try:
				pageCount = int(params[2])
			except:
				pageCount = 0
		offset = pageCount * pageSize

		fileList = []
		session = Session()

		try:
			fileInfos = session.query(FileStatus).filter(and_(FileStatus.ext == 'document', FileStatus.name.like(f"%{search}%"))).order_by(FileStatus.name).offset(offset).limit(pageSize).all()
			if fileInfos is not None:
				for info in fileInfos:
					fileList.append({
						'name':  pathlib.Path(info.name).stem,
						'link': info.name
					})
		except:
			fileList = []
		finally:
			session.close()		

		return json.dumps(fileList).encode('utf-8')

	#not found page
	def notFoundPage(self):

		return b"file is not found"

#parse timestamp
@lru_cache(maxsize=10240, typed=False)
def parse_timestamp(timestamp):

	return time.strftime("%d-%b-%Y %H:%M", time.localtime(timestamp))

#parse file size
@lru_cache(maxsize=10240, typed=False)
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

if __name__ == '__main__':
	argv = sys.argv[1:]

	root = '/dist'
	dbname = '/tmp/wikipedia/wikipedia.db'

	try:
		opts, args = getopt.getopt(argv, "d:h:r:", [
			"dbname",
			"host=",
			"root="
        ])
	except:
		logging.error("parse arguments failed")
		sys.exit(-1)

	for opt, arg in opts:
		if opt in ['--root', '-r']:
			root = arg
		elif opt in ['--host', '-h']:
			SWARM_HOST = arg				
		elif opt in ['--dbname', '-d']:
			dbname = arg			

	if not os.path.exists(root):
		os.makedirs(root)

	#create new sqlite engine
	engine = create_engine(f"sqlite:///{dbname}?check_same_thread=False", echo=False)

	#create Session maker
	Session = sessionmaker(bind = engine)

	site = server.Site(Resquest())
	endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
	endpoint.listen(site)
	reactor.run()