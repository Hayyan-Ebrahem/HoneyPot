import sys
from Tkinter import *
import time
import notebook
from ttk import *
import os
import matplotlib.pyplot as pyplot
import ast
import operator

"""
this file will read the log files and open a tkinter window with tabs named as the log files
'192.168.178.162016-06-1815:38:44' and start typing out the file contents
when all files are typed out new window will pop up showing simple visualization of commands
that were sent from Client to Server

"""
# These files are STATIC on server system
log_files=[]
log_dir='/home/oracle/HP/log'
readable_log='/home/oracle/HP/read_log'

label_list=[]
x_list=[]
########################################################################
class RedirectText(object):
	defstdout = sys.stdout

	def __init__(self, text_output):
		self.output = text_output

	def write(self, string):
		""""""
		self.output.insert(END, string)

	def flush(self):
		self.defstdout.flush()

class get_text(object):
	def __init__(self):
		self.dict_from_log=""

	def open_file(self,*args):
		redir = RedirectText(args[0])
		sys.stdout = redir
		f=open(log_dir+"/"+args[1])
		#iter_file=iter(f)
		readable=open(readable_log+"/"+args[1],'w+')
		readable.write("Client is :"+args[1][:15]+"\n\n")
		sys.stdout=sys.stdout
		lines=f.readlines()
		indices = [i for i, x in enumerate(lines) if ".[94mVTechftp>.[0m" in x ]
		for j in indices:
			readable.write("Client send : "+lines[j+1])
			readable.write("Server replys : "+lines[j+2]+"\r\n")
		try:
			for line in lines:
				if "{" in line:
					self.dict_from_log=line
				for ch in line:
					sys.stdout.write(ch)
					sys.stdout.flush()
					root.update()
					time.sleep(0.001)
				#    if ch =="}":
				 #       raise StopIteration()
		except StopIteration:
			pass
		f.close()
		readable.close()
# 		try:
# 			# mutt should be set up on the Server to send emails
# 			os.system('mutt -s "Message from VtechServer" hayyan-ebrahem@hotmail.com < /home/oracle/HP/log/'+args[1])
# 		except OSError, error:
# 			print error

	def get_log_files():
		files=os.listdir(log_dir)
		for logs in files:
			log_files.append(logs)

	get_log_files()
	########################################################################
class MyApp(object):
	""""""
	def __init__(self, parent):
		"""Constructor"""
		self.root = parent
		note= Notebook(parent)
		self.root.title("Hony Pot")
		self.root.configure(bg='gray')
		self.analyize=Button(root,text="Analyize Log",command=self.he)
		self.advice=Button(root,text="Advice Log",command=self.advice)
		self.analyize.pack(side=BOTTOM)
		self.advice.pack(side=BOTTOM)
		self.get=get_text()
		tab1=Frame(note)
		note.add(tab1,text=log_files[0])
		frame1 = Frame(tab1,width=50, height=200)
		frame1.pack()
		frame1.place(x=10,y=10)
		editArea1 = Text(tab1, width=50, height=100, wrap=WORD,fg='green',font=(12),bg="black")
		editArea1.pack()
		#editArea1.place(x=10,y=10)
		tab2=Frame(note)
		note.add(tab2,text=log_files[1])
		frame2 = Frame(tab2,width=50, height=200)
		frame2.pack()
		editArea2 = Text(tab2, width=50, height=100, wrap=WORD,font=(12), fg='green',bg="black")
		editArea2.pack()
		frame2.place(x=10,y=10)

	 #   tab3=Frame(note)
	  #  note.add(tab3,text=log_files[2])
	   # frame3 = Frame(tab3,width=200, height=500)
  #      frame3.pack()

   #     editArea3 = Text(tab3, width=50, height=100, wrap=WORD, font=(12),fg='green')
  #      editArea3.pack()

	#    frame3.place(x=10,y=10)

		note.pack()
		tab1.bind('<Button-1>',self.get.open_file(editArea1,log_files[0]))
		tab2.bind('<Button-1>',self.get.open_file(editArea2,log_files[1]))

	def he(self):
		pyplot.rcParams['font.size'] = 24
		d= self.get.dict_from_log
		cut_dict=d[d.find("{"):d.find("}")+1]
		p=ast.literal_eval(cut_dict)
		mydict = { k : v for k,v in p.iteritems() if v != 0 }
		for i, j in mydict.iteritems():
			x_list.append(i)
			label_list.append(j)
		print "\n\r"
		print x_list
		print label_list
		pyplot.axis("equal")
		pyplot.pie(
		x_list,
		labels=label_list,
		autopct="%1.1f%%"
		 )
		pyplot.title("\tLogin Statistics ")
	#pyplot.show()
		pyplot.show()

	def advice(self):
		# create child window
		 win = Toplevel()
		 win.geometry("1800x800")
		# display message
		 values=x_list
		 keys=label_list
		 data = dict(zip(keys, values))
		 # Sort the data dictionary then reverse it
		 items = [(v, k) for k, v in sorted(data.items(), key=operator.itemgetter(1), reverse=True)]
		 message="  \t\tServer advice \n\n"
		 advice=['cd','Secure the important directories in the server like configuration folders and files to be protected been downloadable from the Hackers',\
				 'delete','All systems files must be unshown or undeleteable by default it doesn\'t show hidden files specially folders most visited by the hackers ',\
				 'put','The uploaded files to the server must be scaned before they are uploaded or must be unexcutable by applying \" chmod 644 \"',\
				 'get','Secure all system configuration files and make sure non can be downloadable by the hacker',\
				 'rmdir','all system folders must not be removeable by applying \" sudo chown -R root:root <directory name> && sudo chmod -R 700 <directory name> \" ',\
				 'mkdir','make sure the hackers can not overwrite any system\'s directory ']

		 for x in range(0,len(items)-1):
			 print x
			 if items[x][0] in advice:
				 message+=items[x][0]+" : " + advice[advice.index(items[x][0])+1]+"\n\n"
		 advices=Label(win, text=message,font=("Helvetica", 16))
		 advices.pack()
		 Button(win, text='OK', command=win.destroy).pack()

if __name__ == "__main__":
	root = Tk()
	root.geometry("1600x900")
	app = MyApp(root)
	root.mainloop()
