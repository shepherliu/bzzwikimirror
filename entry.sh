cd ~
wget $1

rm -rf ./docs

./zim-tools_linux-x86_64-3.1.0/zimdump dump --dir=./docs --ns A $1

python3 mirror.py
