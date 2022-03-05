
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

def checksum(data):
  sum = 0
  for d in data:
    sum = sum + d

  return sum

def addHeader(filename, length):
  mod = b'0000777'
  uid = b'0000000'
  gid = b'0000000'

  buffer = filename.encode(encoding = 'utf-8')

  buffer = buffer + mod

  buffer = buffer + uid

  buffer = buffer + gid

  buffer = buffer + pad(length, 11)

  buffer = buffer + pad(int(time.time()), 11)

  sum = checksum(buffer) + 10*32
  
  sum = sum + checksum(b'0ustar')

  buffer = buffer + pad(sum, 6)

  buffer = buffer + b'\u0000 0ustar  '

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
                                     
  r = requests.post(swarmUrl, headers = headers,  data = data)
  
  if r.status_code < 200 or r.status_code > 299:
    r = requests.post(swarmUrl, headers = headers,  data = data)
    
  if r.status_code < 200 or r.status_code > 299:
    print(filepath, r.text)
    return r.text
  
  reference = json.loads(r.text).get('reference')
  fileHashs[filepath] = reference
  
  return reference

if __name__ == '__main__':
  for file in getFiles(wikipediaDir):
    result = uploadToSwarm(file)
    #print(file, result)                                 
                                     
                                     
                                     
  
