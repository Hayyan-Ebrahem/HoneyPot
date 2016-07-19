import os
import socket
import threading
import sys
import time
import subprocess
from functools import wraps
from collections import namedtuple

# server static IP
HOST = '192.168.178.16'
# server port to open socket connection
PORT = 1111
# get the server user name
sudo_username = os.getenv("USER")

"""
DEFAULT_DIR is the log files folder which will contain two other folders
'log' and 'read_log' ,If these folders does not exist on the server the folowwing
code will check and create them
"""

DEFAULT_DIR = '/home/oracle/HP'

if not os.path.exists(DEFAULT_DIR):
    os.mkdir(DEFAULT_DIR+'/log')
    os.mkdir(DEFAULT_DIR+'/read_log')

LOG_DIR=DEFAULT_DIR+'/log'

# this dictoinary will holds the namedtuples for each occurance of method (command) call
# {'command':(occurance, 'IP')}
# {'rmdir': (3,  '192.168.178.16'),  'mkdir': (1,  '192.168.178.16'),  'ls': (4,'192.168.178.16'),  'cd': (2,  '192.168.178.16')}
occurance_dict = {}

class VtechThread(threading.Thread):

    def __init__(self,(conn,addr)):
        self.conn = conn
        self.addr = addr
        self.deleted_items = []
        self.temp_dir = '/home/oracle'

        threading.Thread.__init__(self)

    def occurance_decorator(func):
        '''
        this decorator will decorate the calls of each command and add the
        command name and its occurances to the occurance_dict
        '''
        occurance = namedtuple(str(func.__name__), 'occ ip')
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            wrapper.called+=1
            # put: (3,  '192.168.178.16')
            func_occurance = occurance(wrapper.called, self.addr[0])
            occurance_dict.update({occurance.__name__:(func_occurance.occ, func_occurance.ip)})
            return func(self, *args, **kwargs)
        wrapper.called = 0
        return wrapper

    def args_decorator(func):
        '''
        this decorator will decorate the arguments  of each command call
        '''
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            file_name=args[0]
            destination = self.temp_dir if len(args)==1 else args[1]
            return func(self, file_name, destination)
        return wrapper

    def client_connect(self):
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.connect((self.host, 1112))

    @occurance_decorator
    @args_decorator
    def get(self,file_name, destination):
        """ get  command used to download files from the server to Client """
        # override the destination 'Sent from the client'
        destination=self.conn.recv(1024)
        name='\033[91m'+file_name+'\033[0m'
        destination_path='\033[91m'+destination+'\033[0m'
        file_path=str(os.path.join(self.temp_dir,file_name))
        if os.path.exists(file_path) and file_name not in self.deleted_items:
            self.conn.sendall("The file: "+name+" Exist on the server\n")
            client_response=self.conn.recv(1024)
            # Check the confermation response from Client
            if client_response == 'Y':
                print "file path is :"+file_path
                self.conn.sendall("remote: "+name+\
                 "   local: "+destination_path+"\n"
                +"200 PORT command successful.\r\n"+\
                "150 Opening BINARY mode data connection for "+\
                 name+"("+str(os.path.getsize(file_path))+\
                "bytes)\n 150 Opening data connection .\n")
                data_to_download=open(file_path,'rb')
                #self.conn.sendall(file_name)
                data=data_to_download.readline(1024)
                self.client_connect()
                while data:
                    self.servsock.send(data)
                    data=data_to_download.readline(1024)
                self.conn.sendall("\n Download Finished \n")
                data_to_download.close()
                self.servsock.close()
            else:
                self.conn.sendall("Canceling "+file_name+" Downloading")
        else:
            self.conn.sendall("No such file or directory you will be disconnected")

    @occurance_decorator
    @args_decorator
    def put(self, file_name, destination):
        """ put  command used to upload files from Client to the server"""
        if os.path.isdir(destination):
            # confirm destination to the client
            self.conn.sendall("YES")
            self.client_connect()
            if  '/' in file_name:
                file_name = file_name[file_name.rfind('/')+1:]
            data_recieved = open(destination+"/"+file_name,'w+')
            data=self.servsock.recv(1204)
            # Start reading and writting data
            while data:
                data_recieved.write(data)
                data = self.servsock.recv(1024)
            data_recieved.close()
            self.servsock.close()
        else:
            self.conn.sendall(destination+" Does not exist")

    def bye(self):
        """
        The count_dict dictionry should be saved to the file withh be shown by Tkinter
        this dictionary contains the commands and thier occurrance that will be used
        to visualize the data and show simple advices.

        To do this occurrance_dict will be sent via the socket to be captured and written
        in the Server.

        """
        self.conn.sendall(str(occurance_dict))
        self.conn.close()

    @occurance_decorator
    def pwd(self):
        '''pwd          print working dir on Vtech server'''
        self.conn.sendall('257 '+ self.temp_dir+"\n")

    @occurance_decorator
    def cd(self,destination):
        '''cd           change remote working dir'''
        # absolute path
        if destination.startswith('/'):
            if os.path.isdir(destination):
                self.temp_dir = destination
                self.conn.sendall("250 directory successfuly changed to "+destination+"\n")
            else:
                self.conn.sendall(destination+" no such file or dir\n ")
        # Relative path
        elif os.path.isdir(self.temp_dir+"/"+destination):
            self.temp_dir+='/'+destination
            self.conn.sendall("250 directory successfully changed to "+self.temp_dir+"\n")

    @occurance_decorator
    @args_decorator
    def delete(self, file_name, destination):
        '''delete       delete remote file and dir '''
        # No deletion will be excuted on the server its just addition to
        # deletion list to not be shown when listing dirctories
        if '/' in file_name:
            file_name = file_name[file_name.rfind('/')+1:]
        file_to_delete = '\033[91m'+file_name+'\033[0m'
        if (os.path.exists(os.path.join(self.temp_dir,file_name)) or os.path\
            .exists(destination) ) and file_name not in self.deleted_items:
            self.deleted_items.append(file_name)
            delete_time=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.conn.sendall('250 the file  '+file_to_delete+' is deleted. on '+delete_time+"\r\n")
        else :
            self.conn.sendall("ERROR the file "+file_to_delete+" Does not exist on the server\n")


    @occurance_decorator
    def ls(self,*args):
        '''ls          list contents of remote dir  '''
        if args:
            destination = args[0]
        else:
            destination = self.temp_dir

        self.list_items(destination)

    def list_items(self,destination):
        if os.path.isdir(destination):
            dirs = os.listdir(destination)
            self.conn.sendall("250 listing files in "+destination+"\n")
            for files in dirs:
                if  not ( files.startswith('.') or files in self.deleted_items):
                    if os.path.isdir(self.temp_dir+"/"+files):
                        self.conn.sendall("\033[94m"+files+"\033[0m \r\n")
                    else:
                        self.conn.sendall(files+"\n")
        else:
            self.conn.sendall(destination+" no such file or dir")

    def status(self):
        '''status       show current --static-- status '''
        self.conn.sendall("Connected  to "+ HOST+ ''' No proxy connection.
        Connecting using address family: any.
        Mode: stream; Type: binary; Form: non-print; Structure: file
        Verbose: on; Bell: off; Prompting: on; Globbing: on
        Store unique: off; Receive unique: off
        Case: off; CR stripping: on
        Quote control characters: on
        Ntrans: off
        Nmap: off
        Hash mark printing: off; Use of PORT cmds: on
        Tick counter printing: off''')

    @occurance_decorator
    @args_decorator
    def mkdir(self,file_name, destination):
        '''mkdir       make dir on the remote machine'''
        dir_name = destination+"/"+file_name
        os.mkdir(dir_name)
        dir_name = '\033[91m'+dir_name+'\033[0m'
        self.conn.sendall('257 directory '+dir_name+' created \r\n')

    @occurance_decorator
    @args_decorator
    def rmdir(self, file_name, destination):
        dir_name = destination+"/"+file_name
        if os.path.isdir(dir_name):
            os.rmdir(dir_name)
            dir_name = '\033[91m'+dir_name+'\033[0m'
            self.conn.sendall('250 directory '+dir_name+ '  deleted.\r\n')
        else:
            self.conn.sendall('251 directory '+dir_name+ '  does not exist.\r\n')

    def run(self):
        # Naming the log files
        self.host = self.addr[0]
        log_file=time.strftime("%Y-%m-%d%H:%M:%S", time.gmtime())
        print "client is : "+self.addr[0]
        # send the default message to the client
        self.conn.sendall(
           '''\033[94m
             This Server system is for authorized users only. Individuals using this
             system without authority or in excess of their authority are subject to
             having all their activities on this system monitored and recorded or
             examined by any authorized person, including law enforcement, as system
             personnel deem appropriate. In the course of monitoring individuals
             improperly using the system or in the course of system maintenance, the
             activities of authorized users may also be monitored and recorded. Any
             material so recorded may be disclosed as appropriate. Anyone using this
             system consents to these terms. \n
             Welcome to\033[0m \033[91mVTech FTP Server \033[0m \n
             for help type \033[91m?\033[0m and for commands documentation type \033[91m
             help <<command>> \033[0m \r\n'''
             )
        """
        changing the server current directory to LOG_DIR and start sniffing the network
        and save the sniffing files.

        """
        # change directory to where the server will write log files and start
        # sniffer there
        os.chdir(LOG_DIR)
        # sniffer command that will be executed on the server background and
        # will write the data into log files under LOG_DIR
        sniffer = '/usr/bin/tcpflow -i any -C host '+HOST+' > '+HOST+log_file+'&'
        os.system(sniffer)
        time.sleep(1)
        self.conn.sendall("connected to: " + HOST+"\n")
        self.conn.sendall("220 (VSFTPd 3.0.2)"+"\n")
        self.conn.sendall("Name("+HOST+":anonymous): "+"\n")
        try:
            # changing the current directory to default
            os.chdir(DEFAULT_DIR)
            while True:
                self.conn.sendall("\033[94mVTechftp>\033[0m ")
                data = self.conn.recv(1024)
                command = data.split()
                # commands that the server expect when user asking for help
                # '?' or '? pwd' or 'help' or 'help pwd'
                if command[0] in ('?', 'help'):
                    if len(command) == 1:
                        # if user send '?' or 'help' the server will send the available commands
                        self.conn.sendall (' '.join(self.commands_dict.keys()))
                    # asking for particular command help : ? pwd OR help pwd
                    # the server will send the client the command doc string
                    elif len(command) == 2  and command[1] in self.commands_dict:
                        self.conn.sendall(self.commands_dict[command[1]].func_doc)
                elif command[0] in self.commands_dict:
                    # if the sent command is in command_dict  take the command
                    # and add () to execute the corresponding method
                    if len(command) == 1:
                        # ls, pwd, mkdir, rmdir
                        self.commands_dict[command[0]](self)
                    elif len(command) == 2:
                        # put, get, ls, delete,
                        self.commands_dict[command[0]](self,command[1])
                    elif len(command) == 3:
                        # put, get
                        self.commands_dict[command[0]](self,command[1],command[2])
                else:
                    self.conn.sendall(command[0]+" : No such Command")

        except Exception, e:
            print "Error ",e
            self.conn.sendall("Something went wrong ")

        # this 'commands_dict' values are the server commands to be excuted
    commands_dict = {'pwd':pwd,'cd':cd,'delete':delete,'ls':ls,'status':status,'get':get,'put':put,'mkdir':mkdir,'rmdir':rmdir,'bye':bye}
# commands_dict = [method for method in dir(VtechThread) if callable(getattr(VtechThread, method)) and not method.startswith('_')]
class VtechServer(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST,PORT))
        threading.Thread.__init__(self)

    def run(self):
        self.sock.listen(5)
        while True:
            th = VtechThread(self.sock.accept())
            th.daemon = True
            th.start()

    def stop(self):
        self.sock.close()

if __name__=='__main__':
    ftp = VtechServer()
    ftp.daemon = True
    ftp.start()
    print 'On', HOST, ':', PORT
    raw_input('Server Vtech is runinng')
    ftp.stop()
