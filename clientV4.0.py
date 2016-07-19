from threading import Thread
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
HOST = '192.168.178.16'
PORT =1111
local_dir="/home"
local_host = commands.getoutput("/sbin/ifconfig | grep -E 'addr:192' | awk {'print $2'} | sed -ne 's/addr\:/ /p'")
local_port=1112

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT)) # client-side, connects to a host

#s.send(local_host)
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.bind((local_host,local_port))
c.listen(5)

def args_decorator(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        file_name=args[0]
        destination = self.temp_dir if len(args)==1 else args[1]
        return func(self, file_name, destination)
    return wrapper

def lcd(data):
    '''cd           change local working directory'''
    #dir=data
    global local_dir
    if data.startswith('/'):
        if os.path.isdir(data):
            local_dir=data
            print local_dir
    else:
        if os.path.isdir(local_dir+'/'+data):
            local_dir+='/'+data
            print local_dir

def lpwd():
    print local_dir

def ldir(*args):
    '''dir          list contents of local directory '''
    if args:
        dir=args[0]
        list_items(dir)
    else:
        list_items(local_dir)

def list_items(*args):
    dir=args[0]
    if  os.path.isdir(dir):
            dirs=os.listdir(dir)
            for files in dirs:
                if os.path.isdir(local_dir+"/"+files):
                    print "\033[94m"+files+"\033[0m"
                else:
                    print files
@args_decorator
def put(file_name, destination):
    if not file_name.startswith('/'):
        file_path=local_dir+"/"+file_name
        print "file to upload is  "+'\033[91m'+file_path+'\033[0m'
    else:
        file_path=file_name

    name='\033[91m'+file_name+'\033[0m'
    if os.path.exists(file_path):
        answer=s.recv(1024)
        print "answer is "+answer
        if answer=="YES":
            print answer+" was recieved"
            data_to_upload=open(file_path,'rb')
            data=data_to_upload.readline(1024)
            print "Uploading :local file "+name+"("+\
                    str(os.path.getsize(file_path))+")bytes"+"      to remote:"\
                    +'\033[91m'+destination+'\033[0m'
            answer=raw_input("Do you want to Upload the file Y/N:")

            if answer=='Y':
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
            print 'nop'
            s.close()
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
@args_decorator
def get(file_name, destination):
    s.send(destination)
    if os.path.isdir(destination):
        print s.recv(1024)
        answer=raw_input("Do you want to download the file Y/N:")
        s.send(answer)
        print s.recv(1024)
        co,ad=c.accept()
        data_recieved=open(destination+"/"+file_name,'w+')
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
        s.send(destination+" Does not exist")

while True:
    message = raw_input(s.recv(1024))
    if message in ("bye","quit","exit"):
        bye()
        break
    elif:
        s.send(message)
        if message in ('lcd', 'lpwd', 'ldir'):
            message()
        if message in ('put', 'get'):
            data=message.split()
            if len(data)==3:
                message(data[1],data[2])
            else:
                message(data[1])
