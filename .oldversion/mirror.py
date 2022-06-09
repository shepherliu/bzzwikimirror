#!/usr/bin/python 
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import mimetypes
import requests
import urllib
import urllib.parse

#wiki docs dir is set to $HOME/docs, see entry.sh, we dump zim file to the $HOME/docs dir
wikipediaDir = os.path.join(os.environ['HOME'], 'docs')

# a little less than 10M, this is because the swarm gateway has a limit of upload size of 10M
maxUploadSize = 10230*1024 

swarmGateways = [
  'https://gateway-proxy-bee-0-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-1-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-2-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-3-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-4-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-5-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-6-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-7-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-8-0.gateway.ethswarm.org/bzz',
  'https://gateway-proxy-bee-9-0.gateway.ethswarm.org/bzz'
]

swarmPostageBatchId = "0000000000000000000000000000000000000000000000000000000000000000"

#the file header info for application/x-tar, the number is the length of each item should be.
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

#the file header list for application/x-tar
headList = ['fileName', 'fileMode', 'uid', 'gid', 'fileSize', 'mtime', 'checksum', 'type', 'linkName', 'ustar', 'owner', 'group', 'majorNumber', 'minorNumber', 'filenamePrefix','padding']

#using to patch content length
headPatch = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

#create index.html
def createIndexHtml(files):
  html = '''<html><head><meta charset="UTF-8"><title>Wikipedia</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><script>function importScript() { return 1 } // this is to avoid the error from site.js</script><script src="./-/masonry.min.js"></script><script src="./-/script.js"></script><link href="./-/mobile_main_page.css" rel="stylesheet" type="text/css"><link href="./-/style.css" rel="stylesheet" type="text/css"><script src="./-/images_loaded.min.js"></script><script src="./-/masonry.min.js"></script><script src="./-/article_list_home.js"></script><link rel="canonical" href="https://en.wikipedia.org/wiki/"></head><body class="article-list-home mw-body-content nojs"><ul id="list">'''
  
  for file in files:
    if file.startswith('./A/'):
      filename = os.path.basename(file)
      html = html + '<li style="width:100%; height: auto; word-wrap:break-word; word-break:break-all;"><a></a><a href="A/{0}">{1}</a><a></a></li><a></a>'.format(urllib.parse.quote(filename), filename)

  html = html + '</ul></body></html>'

  return html.encode('utf-8')

#create index file for search
def createIndex(files):
  indexs = []

  for file in files:
    if file.startswith('./A/'):
      filename = os.path.basename(file)
      indexs.append(urllib.parse.quote(filename))

  return json.dumps(indexs).encode('utf-8')

#pad number to fix length in oct
def pad(num, length):
  bits = oct(num)[2:]

  length = len(bits) + 11 - length

  return '00000000000'[length:] + bits

#return the checksum of the file header struct
def addChecksum(fileHeader):
  sum = 0
  for vals in fileHeader.values():
    if len(vals) > 0:
      data = vals.encode(encoding = 'utf-8')
      for d in data:
        sum = sum + d
  return sum  

#return the header info of a given file
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
  
  #caculate the checksum
  checksum = addChecksum(fileHeader)
  
  #pad the checksum 
  fileHeader['checksum'] = pad(checksum, 6) + '\u0000 '
  
  buffer = b''
  
  for head in fileHeader:
    if len(fileHeader[head]) > 0:
      buffer = buffer + fileHeader[head].encode('utf-8')
    
    #patch each header item to its fix length
    patch = headFormat[head] - len(fileHeader[head].encode('utf-8'))
    
    if patch > 0:
      buffer = buffer + headPatch[0:patch]

  return buffer

#using a buffer to append a file to the application/x-tar collection
def appendTarFile(buffer, filename, content):
  buffer = buffer + addHeader(filename, len(content))

  buffer = buffer + content
  
  #fix the size to 512bytes block size
  patch = 512 - len(buffer)%512
  
  if patch < 512:
    buffer = buffer + headPatch[0:patch]

  return buffer

#the metafile info for application/x-tar collection using for swarm.
def addMetaFile(filename, length):

  metafile = '.swarmgatewaymeta.json'

  metadata = {
    'name': filename,
    'size': length,
    'type': ''
  }

  #find the file type, js/html/css .etc

  fileType = '.' + filename.split('.')[-1]

  try:
    metadata['type'] = mimetypes.types_map[fileType]
  except:
    metadata['type'] = ''

  content = json.dumps(metadata, ensure_ascii=False).encode(encoding = 'utf-8')

  return [metafile, content]

# return all the files in the given path
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

# collect the files data to an application/x-tar
def collectFilesData(files):
  data = b''
  sum = 0

  #we use the website type as default to upload files to swarm  
  metaName = 'website'

  if len(files) == 0:
    return None
  elif len(files) == 1:
    #the metaName is the file name itself when upload a sigle file    
    metaName = os.path.basename(files[0])

  #add index.html first 
  indexHtml = createIndexHtml(files)
  sum = sum + len(indexHtml)
  data = appendTarFile(data, 'index.html', indexHtml)

  #add index search second
  indexSearch = createIndex(files)
  sum = sum + len(indexSearch)
  data = appendTarFile(data, 'index', indexSearch)

  #add other files
  for file in files:
    content = open(file, 'rb').read()

    #caculate the total size of all files
    sum = sum + len(content)

    #skip the empty file
    if len(content) == 0:
      continue
    
    #make sure the total size if less than maxUploadSize, it will upload fail if bigger than maxUploadSize
    if len(data) + len(content) > maxUploadSize:
      break
    
    #for a sigle file, we use the base filename, for multi files we use relative path 
    if len(files) == 1:
      file = os.path.basename(file)
    else:
      file = file[2:]
    
    #add file header and file content to the collection
    data = appendTarFile(data, file, content)
  
  #get metafile info
  metafile, metadata = addMetaFile(metaName, sum)

  #add meta file info to the collection 
  data = appendTarFile(data, metafile, metadata)

  #make sure the data is not less than 20 blocks, each block is 512 bytes
  blocks = int(len(data)/512)
  if blocks < 20:
    for i in range(0, 20-blocks):
      data = data + headPatch
  
  return data

#upload files to swarm gateway, we use swarm gateway instead of fairdrive or fairos because the gateway is free for everyone
#but the gateway has a limit of 10M upload size, in future, we can use other api instead of it if we have real use for it.
def uploadToSwarm(files):
  
  data = collectFilesData(files)

  #swarm-index-document when visit the website folder on swarm we need an index.html
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

  reference = ""
  #try to all swarm gateways to upload  
  for swarmUrl in swarmGateways:
    try:
      r = requests.post(swarmUrl, data = data, headers = headers)
      
      if r.status_code < 200 or r.status_code > 299:
        reference = r.text
        continue
  
      reference = json.loads(r.text).get('reference')
      return reference
    except:
      continue  
  
  return reference

if __name__ == '__main__':
  # use your own swarm gateway instead  
  if len(sys.argv) > 1 and len(sys.argv[1]) > 0:
    swarmGateways = [sys.argv[1]]
    # if use your own swarm gateway and bee node, the upload size can be large by your own settings, so set it bigger
    maxUploadSize = 1024*1024*1024
  # use your own swarm gateway batch id instead 
  if len(sys.argv) > 2 and len(sys.argv[2]) > 0:
    swarmPostageBatchId = sys.argv[2]     
  #change to wiki docs dir  
  os.chdir(wikipediaDir)
  
  #files need to upload to swarm
  #for now swarm gateway has a limit of max 10M to upload, so we need to select some importent files to upload
  files = []
  
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
    
    if file.startswith('./I/'):
      files.append(file)

  # upload files to swarm
  result = uploadToSwarm(files) 
  
  #print the 'reference' of the files stored in swarm
  #we can visit the website on https://gateway-proxy-bee-8-0.gateway.ethswarm.org/bzz/reference, remember replace the real reference
  print(result)
                                     
                                     
                                     
  
