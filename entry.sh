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

ls ~

#run the script to mirror the wikipedia files to swarm and output the index.html file hash content on the swarm
python3 /mirror.py
