
# -*- coding: utf-8 -*-
#!/usr/bin/python3
import os
import json
import time
import mimetypes
import requests

wikipediaDir = os.path.join(os.environ['HOME'], 'docs')

htmlDir = os.path.join(os.environ['HOME'], 'docs/A')

fileHashs = dict()

def pad(num, length):
  bits = oct(num).encode(encoding='utf-8')[2:]

  length = len(bits) + 11 - length

  return b'00000000000'[length:] + bits

def addChecksum(fileHeader):
  sum = 0
  for vals in fileHeader.values():
    for d in vals:
      sum = sum + d
  return sum
  

def addHeader(filename, length):
  
  fileHeader = {
    'fileName': filename.encode(encoding = 'utf-8'),
    'fileMode': b'0000777',
    'uid': b'0000000',
    'gid': b'0000000',
    'fileSize': pad(length, 11),
    'mtime': pad(int(time.time()), 11),
    'checksum': b'        ',
    'type': b'0',
    'ustar': b'ustar  ',
    'owner': b'',
    'group': b''
  }
  
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
  
  checksum = addChecksum(fileHeader)
  
  fileHeader['checksum'] = pad(checksum, 6) + '\u0000 '

  return buffer

def appendTarFile(buffer, filename, content):
  if len(buffer) > 0:
    buffer = buffer + b'.'

  buffer = buffer + addHeader(filename, len(content))

  buffer = buffer + content

  return buffer

def addMetaFile(filename, length):

  metafile = 'swarmgatewaymeta.json'

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

  content = json.dumps(metadata).encode(encoding = 'utf-8')

  return [metafile, content]

def jsTarFile(filename, content):

  data = appendTarFile(b'', filename, content)

  metafile, metadata = addMetaFile(filename, len(content))

  data = appendTarFile(data, metafile, metadata)

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
  
  data = jsTarFile(filename, open(filepath, 'rb').read())
  
  headers = {
              "accept":"application/json, text/plain, */*",
              "content-type": "application/x-tar",
              "swarm-collection": "true",
              "swarm-index-document": filename,
              "swarm-postage-batch-id": "0000000000000000000000000000000000000000000000000000000000000000"
            }
  
  print(headers)
  print(data)
                                     
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
    print('\n')                        
                                     
                                     
                                     
  
