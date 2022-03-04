cd ~
wget -o wiki.zim $1

rm -rf ./docs

ls ~

./zim-tools_linux-x86_64-3.1.0/zimdump dump --dir=./docs --ns A wiki.zim

rm -f wiki.zim

python3 ~/mirror.py
