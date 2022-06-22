FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install git python3 python3-pip -y \
    && pip3 install requests requests_toolbelt protobuf==3.20.0 etcd3

COPY downloader.py downloader.py

ENTRYPOINT ["python3", "/downloader.py"]