# bzzwikimirror
wiki mirror based on swarm

how to run?

1. clone this project to the local

    git clone https://github.com/shepherliu/bzzwikimirror.git

2. cd to this project and build the docker image: 
   
    cd bzzwikimirror && docker build -t ubuntu/bzzwikimirror:v1 .

3. run the docker image for example: 

    docker run ubuntu/bzzwikimirror:v1 https://download.kiwix.org/zim/wikipedia/wikipedia_bm_all_maxi_2022-02.zim 

4. get the result hash context for example: 0c144d7f76ba9ae7b110664508bf8f458971b215f36d0f73d954e5386fbe0c59

5. then visit the offline Wikimedia on swarm: https://gateway-proxy-bee-1-0.gateway.ethswarm.org/bzz/0c144d7f76ba9ae7b110664508bf8f458971b215f36d0f73d954e5386fbe0c59/.
