FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install git python3 python3-pip -y \
    && pip3 install requests requests_toolbelt twisted sqlalchemy

COPY httpserver.py httpserver.py

COPY dist dist

ENTRYPOINT ["python3", "/httpserver.py"]