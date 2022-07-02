# bzzwikimirror
wiki mirror based on swarm

***How to Run it On local?***

1. make sure that you are using x86_64 computer and using a linux system like ubuntu, install git, docker and docker-compose on your system first.

2. clone this project to the local

    git clone https://github.com/shepherliu/bzzwikimirror.git

3. cd to this project and run the docker-compose service: 
   
    cd bzzwikimirror && sh run.sh

4. you must change the docker-compose.yml file if you run with your own bee nodes.

5. we build a daemon website at http://141.94.55.59:8080/

6. if your want to run the http server only on your local system without upload the zim files duplicated.

    (1) get the latest reference for the sqlite db file by : 

        curl http://141.94.55.59:8080/api/dbname
    
    (2) download the db file through your bee node: 

        wget http://localhost:1633/bytes/{refernece} -O wikipedai.db
    
    (3) build resources on local

        npm install && npm build

    (4) start the httpserver on local system: 

        python3 httpserver.py -h http://localhost:1633 -r ./dist -d ./wikipedai.db

***Features***

1. Support to show all the zim files status(waitting, downloading, extracting, uploading and uploaded).

2. Support paginations and search title for the wikis

***Future Plan***

1. Suport fulltext search for wiki content
    
***How It Works***
<img width="965" alt="snapshot" src="https://user-images.githubusercontent.com/84829620/175287522-9b9a96b2-0c71-417c-a87e-1a65b8b58f3a.png">
