
# -*- coding: utf-8 -*-
#!/usr/bin/python3

wikipediaDir="~/docs"

htmlDir="~/docs/A"

def getFiles(path):
  items = os.listdir(path)
  files = []
  
  for item in items:
    item = os.path.join(path,item)
    if os.path.isdir(item):
      files.extend(getFiles(item))
    elif os.path.isfile(item):
      files.append(item)
  
  return files    

if __name__ == '__main__':
  for file in getFiles(wikipediaDir):
    print(file)
  
