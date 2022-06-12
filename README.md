# bzzwikimirror
wiki mirror based on swarm

*How to Run it On local?

1. make sure that you are using x86_64 computer and using a linux system like ubuntu, install git, docker and docker-compose on your system first.

2. clone this project to the local

    git clone https://github.com/shepherliu/bzzwikimirror.git

3. cd to this project and build the docker image: 
   
    cd bzzwikimirror && sh build.sh

4. run the docker-compose service: 

    sh run.sh