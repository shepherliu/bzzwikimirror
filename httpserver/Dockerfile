FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install git python3 python3-pip -y \
    && pip3 install requests \
    && git clone https://github.com/shepherliu/FairOsTools.git \
    && cd FairOsTools \
    && python3 setup.py install \
    && cd ~  

COPY httpserver.py httpserver.py

ENTRYPOINT ["python3", "/httpserver.py"]