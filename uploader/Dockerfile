FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install git python3 python3-pip -y \
    && pip3 install requests requests_toolbelt sqlalchemy

COPY uploader.py uploader.py

ENTRYPOINT ["python3", "/uploader.py"]