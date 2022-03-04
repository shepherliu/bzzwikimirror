FROM ubuntu

RUN cd ~ \
    && apt-get update \
    && apt-get install wget python3 -y \
    && wget https://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-3.1.0.tar.gz \
    && tar xzvf zim-tools_linux-x86_64-3.1.0.tar.gz \
    && rm zim-tools_linux-x86_64-3.1.0.tar.gz

COPY entry.sh ~/entry.sh
COPY mirror.py ~/mirror.py

ENTRYPOINT ["sh","~/entry.sh"]

CMD ["https://download.kiwix.org/zim/wikipedia/wikipedia_bm_all_maxi_2022-02.zim"]
