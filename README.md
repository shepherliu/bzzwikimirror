# bzzwikimirror
wiki mirror based on swarm

***How to Run it On local?***

1. make sure that you are using x86_64 computer and using a linux system like ubuntu, install git, docker and docker-compose on your system first.

2. clone this project to the local

        git clone https://github.com/shepherliu/bzzwikimirror.git

3. cd to this project

        cd bzzwikimirror

4. change the docker-compose.yml configures with your own bee nodes.

5. run the docker-compose service: 
   
        sh run.sh

6. we build a daemon website with swarm test network at http://141.94.55.59:8080/

7. see our daemon video at: 

8. if you only want to run the http server on your local system without upload the zim files duplicated.
    
    (1) download the latest db file through your bee node: 

        wget http://141.94.55.59:8080/api/database -O wikipedai.db
    
    (2) build resources on local

        npm install && npm build

    (3) start the httpserver on local system: 

        python3 httpserver.py -h http://localhost:1633 -r ./dist -d ./wikipedai.db

***Features***

1. Support to show all the zim files status(waitting, downloading, extracting, uploading and uploaded).

2. Support paginations and search title for the wikis

3. Support run a python httpserver locally with your own bee nodes to view and search the wikis.

4. Using sqlite3 to store the files references and to support search functions. the sqlite file also will be uploaded to swarm for backup. 

***Future Plan***

1. Suport fulltext search for wiki content

2. Replace sqlite3 database to fairos (when fairos is stable enough to support large amount of files)
    
***How It Works***

There are five components to make the wikis on the swarm.

1. trigger component 

    (1) get the latest wiki dumps list from https://dumps.wikimedia.org/other/kiwix/zim/wikipedia

    (2) trigger zim to downloading status if any news update

2. downloader component

    (1) download the zim file from https://dumps.wikimedia.org/other/kiwix/zim/wikipedia

    (2) set zim file status to extracting

3. extractor component

    (1) extract the zim file to the folders

    (2) set zim file status to uploading

4. uploader component

    (1) upload all the extracted files to swarm

    (2) set zim file status to uploaded

    (3) backup the sqlite db file to swarm to make it the newest

5. httpserver component

    (1) prepare your own bee nodes on the local system

    (2) download the latest sqlite db http://141.94.55.59:8080/api/database (if not exist on local)

    (3) run http server on local, and then can view and search wikis through your web browser. 

    (4) for none developers, you can also visit the public daemon website http://141.94.55.59:8080/

<img width="965" alt="snapshot" src="https://user-images.githubusercontent.com/84829620/175287522-9b9a96b2-0c71-417c-a87e-1a65b8b58f3a.png">
