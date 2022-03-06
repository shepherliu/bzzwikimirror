#change to homework dir
cd ~

#download the zim file from the input url
wget -qO wiki.zim $1

#clean the wikipedia dir
rm -rf ./docs

#dump the zim file to html/js/css files etc.
./zim-tools_linux-x86_64-3.1.0/zimdump dump --dir=./docs --ns A wiki.zim

#clean the zim file
rm -f wiki.zim

#move index file to root path and rename to html type
mv docs/A/index docs/index.html

#modify the index.html to redirect to the correct url
sed -i 's#url=#url=A/#g' docs/index.html

#fix python3 http client encode to utf-8
sed -i 's#latin-1#utf-8#g' /usr/lib/python3.8/http/client.py

#run the script to mirror the wikipedia files to swarm and output the index.html file hash content on the swarm
python3 -u /mirror.py
