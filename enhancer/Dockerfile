FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install python3 python3-pip -y \
    && pip3 install requests

COPY enhancer.py enhancer.py

ENTRYPOINT ["sh", "enhancer.py"]