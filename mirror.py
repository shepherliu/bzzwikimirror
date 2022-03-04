
# -*- coding: utf-8 -*-
#!/usr/bin/python3
import os
import requests

wikipediaDir = os.path.join(os.environ['HOME'], 'docs')

htmlDir = os.path.join(os.environ['HOME'], 'docs/A')

fileHashs = dict()

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

def uploadToSwarm(filename):
  swarmUrl = 'https://gateway-proxy-bee-4-0.gateway.ethswarm.org/bzz'
  
  files = {filename: (filename, open('filename', 'rb'))}
                                     
  r = requests.post(url, files=files, data = None)
                                     
  return r.text

if __name__ == '__main__':
  for file in getFiles(wikipediaDir):
    result = uploadToSwarm(file)
    print(file, result)                                 
                                     
                                     
                                     
  
