# bzzwikimirror
wiki mirror based on swarm

*How to Run it On local?

1. make sure that you are using x86_64 computer and using a linux system like ubuntu, install git and docker on your system first.

2. clone this project to the local

    git clone https://github.com/shepherliu/bzzwikimirror.git

3. cd to this project and build the docker image: 
   
    cd bzzwikimirror && docker build -t ubuntu/bzzwikimirror:v1 .

3. run the docker image like this, you can also choose the zim file on https://download.kiwix.org/zim/wikipedia, the size of zim file needs less than 10M: 

    docker run ubuntu/bzzwikimirror:v1 https://download.kiwix.org/zim/wikipedia/wikipedia_en_100_mini_2022-03.zim
    
    advantage usage:  
    
        docker run ubuntu/bzzwikimirror:v1 [zim_file_url] [your_swarm_gateway_url] [your_swarm_postage_batch_id]
    
    if you has your own bee node and run your own swarm gateway proxy on the local with no limit size, you can just run the docker like this:
    
       docker run ubuntu/bzzwikimirror:v1 https://download.kiwix.org/zim/wikipedia/wikipedia_en_100_mini_2022-03.zim http://localhost:3000/bzz f1e4ff753ea1cb923269ed0cda909d13a10d624719edf261e196584e9e764e50   

4. get the hash content that the docker output after excuting done, the hash content is like this: 5db5e9940b5edec5363a8248efbee063c80da25369e0c10bca8e27e9b1e5644a

5. then you can visit Wikimedia docs on the swarm, just replace the hash content as real output: https://gateway-proxy-bee-1-0.gateway.ethswarm.org/bzz/5db5e9940b5edec5363a8248efbee063c80da25369e0c10bca8e27e9b1e5644a.

   if you have your own swarm gateway, remember replace the gateway url of your own.

6. we make a demo video on  https://www.youtube.com/watch?v=C6uQgeA_VPw

*Tips When You Use This Docker Image:
   
   1. For quickly use for everyone, I use the offical swarm gateway as default which has a limit size of upload files that about 10M. So if you choose a zim file more bigger, you need run your own bee node and swarm gateway, other wise, it will drop some pictures and doc files to satisfy the upload limit. 
   
   2. When you access the swarm gateway, it may get some erros such as 503 error, just refresh the website for some times. For a better experience, you can run your own swarm gateway on the local.
   
   3. The wikipedia website itself may have many outside web links which are not storaged in the zim file. So if you click some of the outside links, the browser will redirect to the new website. Remember that is not a bug of the program, haha!

*How it Works?

1. the wikipedia offline zim file is a collection of files(html/js/css .etc) of wikipedia docs, we can download it and decompress it to a local folder.

   the decompressed zim file has tree main subfolder: "./A/", "./I/", "./-/". 
  
   the "./A" folder stores all the html files
   
   the "./I/" folder stores all the pitures files
   
   the "./-/" folder stores all the js/css files
   
2. we can use the swarm gateway apis to upload the whole folder files to the swarm, then we can visit the wikipedia docs on the swarm. but we need something to fix.
   
   first, the swarm gateway has a limit of 10M size to upload. so the zim folder size need a little less than 10M. For that we may drop some pictures to upload. if you have your own swarm gateway with your own bee node, then the limit will be set to 1G.
   
   second, the swarm surport upload the whole website folder, but the folder must has an index.html so that we can visit it on swarm directly. So that we need move the "./A/index" file to "./" and rename it to "index.html", and we also need to modify the index.html content to change url redirect to "./A/" folder.
   
3. after we have solved these problems, we can use our program in the docker image we build to download the zim file and decompress it and upload the folder to swarm automatic. then use the hash content the swarm return to visit the wikipedia docs on swarm gateway.

   first, we use entry.sh to download the zim file , and decompress it to a folder, and them modify the "./A/index" file to "./index.html", and modify the url in the "index.html" file.
   
   second, we use a python script to collect the folder files to an application/x-tar collection, and then upload the collection data to swarm gateway, finally we get the reference return by the swarm gateway. Then we can visit our wikipedia website on swarm by the reference. if you get some warong when visit the website on swarm, just refresh the url sometimes.
