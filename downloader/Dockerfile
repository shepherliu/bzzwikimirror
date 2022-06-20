FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install git python3 python3-pip -y \
    && pip3 install requests requests_toolbelt \
    && git clone https://github.com/shepherliu/FairOsTools.git \
    && cd FairOsTools \
    && python3 setup.py install \
    && cd ~   

COPY downloader.py downloader.py

ENTRYPOINT ["python3", "/downloader.py"]