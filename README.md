# bzzwikimirror
wiki mirror based on swarm

How to Run it On local?
1. make sure that you are using x86_64 computer and using a linux system like ubuntu, install git and docker on your system first.

2. clone this project to the local

    git clone https://github.com/shepherliu/bzzwikimirror.git

3. cd to this project and build the docker image: 
   
    cd bzzwikimirror && docker build -t ubuntu/bzzwikimirror:v1 .

3. run the docker image like this, you can also choose the zim file on https://download.kiwix.org/zim/wikipedia, the size of zim file needs less than 10M: 

    docker run ubuntu/bzzwikimirror:v1 https://download.kiwix.org/zim/wikipedia/wikipedia_bm_all_maxi_2022-02.zim 

4. get the hash content that the docker output after excuting done, the hash content is like this: a4d312adc8ff530c1609bc363a4750d52fc8ecd967c3e4697e218a295f38a0ba

5. then you can visit Wikimedia docs on the swarm, just replace the hash content as real output: https://gateway-proxy-bee-1-0.gateway.ethswarm.org/bzz/a4d312adc8ff530c1609bc363a4750d52fc8ecd967c3e4697e218a295f38a0ba.

6. we make a demo video on  https://github.com/shepherliu/bzzwikimirror/blob/main/demo.mp4
