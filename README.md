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


How it Works?

1. the zim file is a collection of files(html/js/css .etc) of wikipedia docs, we need first download it and decompress it to a local folder.

   the decompressed zim file has tree main subfolder: "./A/", "./I/", "./-/". 
  
   the "./A" folder stores all the html files
   
   the "./I/" folder stores all the pitures files
   
   the "./-/" folder stores all the js/css files
   
2. we use the swarm gateway to upload the whole folder files to the swarm, so we can visit the wikipedia docs on the swarm. but we need something to fix.
   
   first, the swarm gateway has a limit of 10M size to upload. so the zim folder size need a little less than 10M. For that we may drop some pictures to upload.
   
   second, the swarm surport upload the whole website folder, but the folder must has an index.html so that we can visit it on swarm directly. So that we need move the "./A/index" file to "./" and rename it to "index.html", and we also need to modify the index.html content to change url redirect to "./A/" folder.
   
3. after we have solved these problems, we can use our program in the docker image we build to download the zim file and decompress it and upload the folder to swarm automatic. then use the hash content the swarm return to visit the wikipedia docs on swarm gateway.

   first, we use entry.sh to download the zim file , and decompress it to a folder, and them modify the "./A/index" file to "./index.html", and modify the url in the "index.html" file.
   
   second, we use a python script to collect the folder files to an application/x-tar collection, and then upload the collection data to swarm gateway, finally we get the reference return by the swarm gateway. Then we can visit our wikipedia website on swarm by the reference. 
