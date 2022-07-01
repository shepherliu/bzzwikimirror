FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install wget git sed python3 python3-pip -y \
    && pip3 install requests requests_toolbelt sqlalchemy \
    && wget https://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-3.1.1.tar.gz \
    && tar xzvf zim-tools_linux-x86_64-3.1.1.tar.gz \
    && rm zim-tools_linux-x86_64-3.1.1.tar.gz

COPY extractor.py extractor.py

ENTRYPOINT ["python3", "/extractor.py"]