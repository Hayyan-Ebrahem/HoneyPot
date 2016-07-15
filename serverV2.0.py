import os
import socket
import threading
import sys
import time
import subprocess

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

DEFAULT_DIR = '/home/'+sudo_username+'/HP'

if not os.path.exists(DEFAULT_DIR):
	os.makedirs(DEFAULT_DIR+'/log')
	os.makedirs(DEFAULT_DIR+'/read_log')

LOG_DIR=DEFAULT_DIR+'/log'

# list holds the  number of times each function were excuted on the serve
# this list follows this order count_list[pwd,cd,delete,dir,dir,get,put,mkdir,rmdir]
count_list=[0,0,0,0,0,0,0,0,0]

class VtechThread(threading.Thread):

	def __init__(self,(conn,addr)):
		self.conn=conn
		self.addr=addr
		self.deleted_items=[]
		self.temp_dir='/home/'+sudo_username

		threading.Thread.__init__(self)

	def __str__(self):
		return 'I am STR'

	def client_connect(self):
		self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.servsock.connect((HOST, PORT))

	def run(self):
		# Naming the log files
		log_file=time.strftime("%Y-%m-%d%H:%M:%S", time.gmtime())

		print "client is : "+HOST
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
		time.sleep(2)
		self.conn.sendall("connected to  " + HOST+"\n")
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
					elif len(command) == 2  and command[1] in self.commands_dict:
						self.conn.sendall(self.commands_dict[command[1]].func_doc)
				elif command[0] in self.commands_dict:
					# if the command was sent without parameters take the command
					# and add () to execute the corresponding function
					if len(command) == 1:
						self.commands_dict[command[0]](self)
					elif len(command) == 2:
						self.commands_dict[command[0]](self,command[1])
					elif len(command) == 3:
						self.commands_dict[command[0]](self,command[1],command[2])
				else:
					self.conn.sendall(command[0]+" : No such Command")

		except Exception, e:
			print "Error ",e
			self.conn.sendall("Something went wrong ")

	# Starting with the Server commands (functions)
	# each function is the KEY and the Value in 'commands_dict'

	def bye(self):
		"""
		The count_dict dictionry should be safed to the file withh be shown by Tkinter
		this dictionary contains the commands and thier occurrance that will be used
		to visualize the data and show simple advices.

		To do this count_dict will be sent via the socket to be captured and written
		in the Server.

		"""
		occurrance=self.count_dict
		self.conn.sendall(str(occurrance))
		self.conn.close()

	def pwd(self):
		'''pwd          print working dir on Vtech server'''
		self.conn.sendall('257 '+ self.temp_dir+"\n")
		count_list[0]+=1
		self.count_dict['pwd'] = count_list[0]

	def cd(self,dir):
		'''cd           change remote working dir'''
		count_list[1]+=1
		self.count_dict['cd'] = count_list[1]
		#dir=data
		if dir.startswith('/'):
			if os.path.isdir(dir):
				self.temp_dir = dir
				self.conn.sendall("250 directory successfuly changed to "+dir+"\n")
			else:
				self.conn.sendall(dir+" no such file or dir\n ")
		elif os.path.isdir(self.temp_dir+"/"+dir):
			self.temp_dir+=dir
			self.conn.sendall("250 directory successfully changed to "+self.temp_dir+"\n")

	def delete(self,data):
		'''delete       delete remote file and dir '''
		count_list[2]+=1
		self.count_dict['delete'] = count_list[2]

		# if client didn't provides a PATH
		if not '/' in data:
			file_name = data
		# get the file name
		else:
			file_name = data[data.rfind('/')+1:]

		file_to_delete = '\033[91m'+file_name+'\033[0m'

		if (os.path.exists(os.path.join(self.temp_dir,file_name)) or os.path\
			.exists(data) ) and file_name not in self.deleted_items:
			self.deleted_items.append(file_name)
			delete_time=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
			self.conn.sendall('250 the file  '+file_to_delete+' is deleted. on '+delete_time+"\r\n")
		else :
			self.conn.sendall("ERROR the file "+file_to_delete+" Does not exist on the server\n")


	def dir(self,*args):
		'''dir          list contents of remote dir '''
		count_list[3]+=1
		self.count_dict['dir'] = count_list[3]
		dir = args[0]
		#  If Client sent a PATH to list
		if args:
			self.list_items(dir)
		else:
			self.list_items(self.temp_dir)

	def list_items(self,*args):
		dir = args[0]
		if os.path.isdir(dir):
			dirs = os.listdir(dir)
			self.conn.sendall("250 listing files in "+dir+"\n")
			for files in dirs:
				if  not ( files.startswith('.') or files in self.deleted_items):
					if os.path.isdir(self.temp_dir+"/"+files):
						self.conn.sendall("\033[94m"+files+"\033[0m \r\n")
					else:
						self.conn.sendall(files+"\n")
		else:
			self.conn.sendall(dir+" no such file or dir")

	def status(self):
		'''status       show current status '''
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



	def put(self,*args):
		""" put  command used to upload files from Client to  server"""
		count_list[6]+=1
		self.count_dict['put']=count_list[6]
		file_name = args[0]
		if len(args) == 2:
			dir=args[1]
		else:
			dir=self.temp_dir
			self.conn.sendall(dir)

		if os.path.isdir(dir):
			print "file {0} exist".formate(dir)
			self.conn.sendall("YES")
			self.client_connect()
			if  '/' in file_name:
				file_name = file_name[file_name.rfind('/')+1:]
			data_recieved = open(dir+"/"+file_name,'w+')
			data=self.servsock.recv(1204)
			# Start reading and writting  data
			while data:
				data_recieved.write(data)
				data = self.servsock.recv(1024)
			data_recieved.close()
			self.servsock.close()
		else:
			self.conn.sendall(dir+" Does not exist")

	def get(self,*args):
		""" get  command used to download files from the server to Client """
		count_list[5]+=1
		self.count_dict['get'] = count_list[5]
		file_name = args[0]
		if len(args) == 2:
			dir=args[1]
		elif len(args) == 1:
			dir=self.conn.recv(1024)

		name='\033[91m'+file_name+'\033[0m'
		dir_path='\033[91m'+dir+'\033[0m'
		file_path=str(os.path.join(self.temp_dir,file_name))
		if os.path.exists(file_path) and file_name not in self.deleted_items:
			self.conn.sendall("The file: "+name+" EXIST on the server")
			client_response=self.conn.recv(1024)
			# Check the confermation response from Client
			if client_response == 'Y':
				print "file path is :"+file_path
				self.conn.sendall("remote : "+name+\
				 "   local : "+dir_path+"\n"
				+"200 PORT command successful.\r\n"+\
				"150 Opening BINARY mode data connection for "+\
				 name+"("+str(os.path.getsize(file_path))+\
				"bytes)\n 150 Opening data connection .\n")
				# for the good practice of closing socket , WITH statement was not used
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

	def mkdir(self,data):
		'''mkdir       make dir on the remote machine'''
		count_list[7]+=1
		self.count_dict['mkdir'] = count_list[7]
		dir=self.temp_dir+"/"+data
		os.mkdir(dir)
		self.conn.sendall('257 directory created'+dir)

	def rmdir(self,data):
		count_list[8]+=1
		self.count_dict['rmdir'] = count_list[8]
		dir = self.temp_dir+"/"+data
		if os.path.isdir(dir):
			os.rmdir(dir)
			self.conn.sendall('250 directory deleted.\r\n')

	# this 'commands_dict' values are the server commands to be excuted
	commands_dict={'pwd':pwd,'cd':cd,'delete':delete,'dir':dir,\
	   'status':status,'get':get,'put':put,'mkdir':mkdir,\
	   'rmdir':rmdir,'bye':bye}
	# this 'count_dict' keys are the server comands and the values are number of
	# occurrance of each , this will be used to visualize the commands and its
	# occurrancein HP.py
	count_dict=dict(zip(count_list, commands_dict.values()))

class VtechServer(threading.Thread):
	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((HOST,PORT))
		threading.Thread.__init__(self)

	def run(self):
		self.sock.listen(5)
		while True:
			th=VtechThread(self.sock.accept())
			th.daemon=True
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
