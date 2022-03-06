#!/usr/bin/python 
# -*- coding: utf-8 -*-
import os
import json
import time
import mimetypes
import requests

wikipediaDir = os.path.join(os.environ['HOME'], 'docs')

maxUploadSize = 10230*1024 # a little less than 10M

headFormat = {
    'fileName': 100,
    'fileMode': 8,
    'uid': 8,
    'gid': 8,
    'fileSize': 12,
    'mtime': 12,
    'checksum': 8,
    'type': 1,
    'linkName':100,
    'ustar': 8,
    'owner': 32,
    'group': 32,
    'majorNumber': 8,
    'minorNumber': 8,
    'filenamePrefix': 155,
    'padding': 12
}
  
headList = ['fileName', 'fileMode', 'uid', 'gid', 'fileSize', 'mtime', 'checksum', 'type', 'linkName', 'ustar', 'owner', 'group', 'majorNumber', 'minorNumber', 'filenamePrefix','padding']
  
headPatch = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

def pad(num, length):
  bits = oct(num)[2:]

  length = len(bits) + 11 - length

  return '00000000000'[length:] + bits

def addChecksum(fileHeader):
  sum = 0
  for vals in fileHeader.values():
    if len(vals) > 0:
      data = vals.encode(encoding = 'utf-8')
      for d in data:
        sum = sum + d
  return sum  

def addHeader(filename, length):
  
  fileHeader = {
    'fileName': filename,
    'fileMode': '0000777',
    'uid': '0000000',
    'gid': '0000000',
    'fileSize': pad(length, 11),
    'mtime': pad(int(time.time()), 11),
    'checksum': '        ',
    'type': '0',
    'linkName': '',
    'ustar': 'ustar  ',
    'owner': '',
    'group': '',
    'majorNumber': '',
    'minorNumber': '',
    'filenamePrefix': '',
    'padding': ''
  }
    
  checksum = addChecksum(fileHeader)
  
  fileHeader['checksum'] = pad(checksum, 6) + '\u0000 '
  
  buffer = b''
  
  for head in fileHeader:
    if len(fileHeader[head]) > 0:
      buffer = buffer + fileHeader[head].encode('utf-8')
    
    patch = headFormat[head] - len(fileHeader[head].encode('utf-8'))
    
    if patch > 0:
      buffer = buffer + headPatch[0:patch]

  return buffer

def appendTarFile(buffer, filename, content):
  buffer = buffer + addHeader(filename, len(content))

  buffer = buffer + content
    
  patch = 512 - len(buffer)%512

  buffer = buffer + headPatch[0:patch]

  return buffer

def addMetaFile(filename, length):

  metafile = '.swarmgatewaymeta.json'

  metadata = {
    'name': filename,
    'size': length,
    'type': ''
  }

  fileType = '.' + filename.split('.')[-1]

  try:
    metadata['type'] = mimetypes.types_map[fileType]
  except:
    metadata['type'] = ''

  content = json.dumps(metadata, ensure_ascii=False).encode(encoding = 'utf-8')

  return [metafile, content]

def getFiles(path):
  items = os.listdir(path)
  files = []
  
  for item in items:
    item = os.path.join(path, item)
    if os.path.isdir(item):
      files.extend(getFiles(item))
    elif os.path.isfile(item):
      files.append(item)
  
  return files    

def collectFilesData(files):
  data = b''
  sum = 0

  metaName = 'website'

  if len(files) == 0:
    return None
  elif len(files) == 1:
    metaName = os.path.basename(files[0])

  for file in files:
    content = open(file, 'rb').read()
    sum = sum + len(content)

    if len(content) == 0:
      continue
    
    if len(data) + len(content) > maxUploadSize:
	break
    
    if len(files) == 1:
      file = os.path.basename(file)
    else:
      file = file[2:]
    
    data = appendTarFile(data, file, content)

  metafile, metadata = addMetaFile(metaName, sum)
	
  data = appendTarFile(data, metafile, metadata)

  blocks = int(len(data)/512)
  if blocks < 20:
    for i in range(0, 20-blocks):
      data = data + headPatch
  
  return data

def uploadToSwarm(files):
  swarmUrl = 'https://gateway-proxy-bee-4-0.gateway.ethswarm.org/bzz'
  
  data = collectFilesData(files)

  index = 'index.html'
  if len(files) == 1:
      index = os.path.basename(files[0])
    
  headers = {
              "accept":"application/json, text/plain, */*",
              "content-type": "application/x-tar",
              "swarm-collection": "true",
              "swarm-index-document": index,
              "swarm-postage-batch-id": "0000000000000000000000000000000000000000000000000000000000000000"
            }

  r = requests.post(swarmUrl, headers = headers,  data = data)
    
  if r.status_code < 200 or r.status_code > 299:
    return r.text
  
  reference = json.loads(r.text).get('reference')
  
  return reference

if __name__ == '__main__':
  #change to wiki docs dir	
  os.chdir(wikipediaDir)
  
  #files need to upload to swarm, for now swarm gateway has a limit of max 10M to upload, so we need to select some importent files to upload
  files = ["./index.html"]
	
  #dir A stores html files, and dir - stores js,css files	
  for file in getFiles('.'):
    #swarm gateway has a limit file name to less than 100bytes		
    if len(file.encode(encoding = 'utf-8')) - 2 > headFormat['fileName']:
      continue
    
    if file.startswith('./A/') or file.startswith('./-/'):
      files.append(file)

  # dir I stores pictures
  for file in getFiles('.'):
    if len(file.encode(encoding = 'utf-8')) - 2 > headFormat['fileName']:
      continue
    
    if file.endswith('./I/'):
      files.append(file)

  # upload files to swarm    
  result = uploadToSwarm(files)
  
  #print the 'reference' of the files stored in swarm
  #we can visit the website on https://gateway-proxy-bee-8-0.gateway.ethswarm.org/bzz/reference, remember replace the real reference
  print(result)
                                     
                                     
                                     
  
