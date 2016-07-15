import os
import sys
import time
import socket
import commands

"""
	This file will be downloaded and installed on the client side
	after AGREEING on Vtech ftp server .

	some notes may be usefull:

		STATICS IP's were used
		STATICS log files and log directory
		Server system not customized

	This file should implement singleton pattern as it's only allowed to establish
	one connection from client to the server.

	The following will be excuted when starting 'FTP vtech.com'.

"""

HOST = '192.167.168.10'
PORT = 1111
local_dir = "/home"
# get the Client host IP address
local_host = commands.getoutput("/sbin/ifconfig | grep -E 'addr:192' | awk {'print $2'} | sed -ne 's/addr\:/ /p'")
local_port = 1112

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT)) # client-side, connects to a host

#s.send(local_host)
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.bind((local_host,local_port))
c.listen(5)

def lcd(*args):
	'''cd           change remote working directory'''
	#dir=data
	global local_dir
	if argsi[0].startswith('/'):
		if os.path.isdir(args[0]):
			local_dir=args[0]
			print local_dir
	else:
		if os.path.isdir(local_dir+'/'+data):
			local_dir+='/'+args[0]
			print local_dir

def lpwd():
    print local_dir

def ldir(*args):
    '''dir          list contents of remote directory '''
    if args:
        dir=args[0]
        list_items(dir)
    else:
        list_items(local_dir)

def list_items(*args):
    dir=args[0]
    if os.path.isdir(dir):
		dirs=os.listdir(dir)
	for files in dirs:
		if os.path.isdir(local_dir+"/"+files):
			print "\033[94m"+files+"\033[0m"
		else:
			print files

def put(*args):
	# Client might send: put /home/user/file.txt /server/home/users
	# OR put /home/user/file.txt
	# OR put file.txt /server/home
	# OR put file.txt
    file_name=args[0]
	# If client sent a PATHS
    if len(args)==2:
        dir=args[1]
	# If Client sent PATH on Server check if it exist
    elif len(args)==1:
        file_name=args[0]
        dir=s.recv(1024)
        print "dir from server is "+dir
	# If Client directly sent file name directly
    if not file_name.startswith('/'):
        file_path=local_dir+"/"+file_name
        print "file to upload is  "+'\033[91m'+file_path+'\033[0m'
	# Client sent a file name as a PATH (on Client Side)
    else:
        file_path=file_name

    name='\033[91m'+file_name+'\033[0m'
    if os.path.exists(file_path):
        answer=s.recv(1024)
        if answer == "YES":
            data_to_upload=open(file_path,'rb')
            data=data_to_upload.readline(1024)
            print "Uploading :local file "+name+"("+\
                    str(os.path.getsize(file_path))+")bytes"+" to remote:"\
                    +'\033[91m'+dir+'\033[0m'
			co,ad=c.accept()
			while data:
				co.send(data)
				data=data_to_upload.readline(1024)
				time.sleep(0.1)
				sys.stdout.write('=')
				sys.stdout.flush()
			print "\n Upload Finished"
			data_to_upload.close()
			co.close()
    else:
        print ("file "+name+" not found")
        print ("you will be disconcted")
        s.close()

def bye():
    que=s.sendall("bye")
    ans=s.recv(1024)
    print ans
    s.close()
    print "221 Goodbye \r\n"

def get(*args):

	file_name=args[0]
	if len(args)==2:
		dir=args[1]
	elif len(args)==1:
		file_name=args[0]
		dir=self.conn.recv(1024)
    if os.path.isdir(dir):
        print s.recv(1024)
        answer=raw_input("Do you want to download the file Y/N:")
        s.send(answer)
        print s.recv(1024)
        co,ad=c.accept()
        data_recieved=open(dir+"/"+file_name,'w+')
        data=co.recv(1204)
        while data:
            data_recieved.write(data)
            data=co.recv(1024)
            time.sleep(0.1)
            sys.stdout.write('=')
            sys.stdout.flush()
        data_recieved.close()
        co.close()
    else:
        s.send(dir+" Does not exist")

client_commands = ['lcd', 'lpwd', 'ldir', 'get', 'put']
while True:
    command = raw_input(s.recv(1024))
    if command in ("bye","quit","exit"):
        bye()
        break
	elif command in client_commands:
        s.send(command)
		command()
