cd ~
wget -qO wiki.zim $1

rm -rf ./docs

./zim-tools_linux-x86_64-3.1.0/zimdump dump --dir=./docs --ns A wiki.zim

rm -f wiki.zim

ls /mirror.py

python3 ~/mirror.py
