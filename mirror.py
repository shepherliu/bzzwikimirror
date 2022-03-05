#!/usr/bin/python 
# -*- coding: utf-8 -*-
import os
import json
import time
import mimetypes
import requests

wikipediaDir = os.path.join(os.environ['HOME'], 'docs')

htmlDir = os.path.join(os.environ['HOME'], 'docs/A')

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
  
headPatch = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

fileHashs = dict()

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
  
  buffer = ''
  
  for head in fileHeader:
    if len(fileHeader[head]) > 0:
      buffer = buffer + fileHeader[head]
    
    patch = headFormat[head] - len(fileHeader[head])
    
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

  content = json.dumps(metadata)

  return [metafile, content]

def jsTarFile(filename, content):

  data = appendTarFile('', filename, content)

  metafile, metadata = addMetaFile(filename, len(content))

  data = appendTarFile(data, metafile, metadata)

  blocks = int(len(data)/512)
    
  if blocks < 20:
    for i in range(0, 20-blocks):
        data = data + headPatch

  return data

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

def uploadToSwarm(filepath):
  swarmUrl = 'https://gateway-proxy-bee-4-0.gateway.ethswarm.org/bzz'
  
  filename = filepath.split('/')[-1]
  
  data = jsTarFile(filename, open(filepath, 'rb', encoding="utf-8").read()

  data = data.encode("utf-8")
  
  headers = {
              "accept":"application/json, text/plain, */*",
              "content-type": "application/x-tar",
              "swarm-collection": "true",
              "swarm-index-document": filename,
              "swarm-postage-batch-id": "0000000000000000000000000000000000000000000000000000000000000000"
            }
                                     
  r = requests.post(swarmUrl, headers = headers,  data = data)
  
  if r.status_code < 200 or r.status_code > 299:
    r = requests.post(swarmUrl, headers = headers,  data = data)
    
  if r.status_code < 200 or r.status_code > 299:
    return r.text
  
  reference = json.loads(r.text).get('reference')
  fileHashs[filepath] = reference
  
  return reference

if __name__ == '__main__':
  for file in getFiles(wikipediaDir):
    print(file)
    result = uploadToSwarm(file) 
    print(result)
                                     
                                     
                                     
  
