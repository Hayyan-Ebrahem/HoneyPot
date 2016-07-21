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
        with open(log_dir+"/"+args[1]) as f:
            sys.stdout=sys.stdout
            lines=f.readlines()
            indices = [i for i, x in enumerate(lines) if "[94mVTechftp>[0m" in x ]
        #iter_file=iter(f)
            with open(readable_log+"/"+args[1],'w+') as readable:
                readable.write("Client is :"+args[1][:15]+"\n\n")
                for j in indices:
                    # lines[j+1]  ==> the sent command from client to server
                    # lines[j+3]  ==> the response from the server -indexed as
                    # i+3 because the new line after each command sent to the
                    # server
                    readable.write("Client send : "+lines[j+1])
                    readable.write("Server replys : "+lines[j+3]+"\r\n")
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
#       try:
#           # mutt should be set up on the Server to send emails
#           os.system('mutt -s "Message from VtechServer" hayyan-ebrahem@hotmail.com < /home/oracle/HP/log/'+args[1])
#       except OSError, error:
#           print error

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
        self.analyize=Button(root,text="Analyize Log",command=self.analyize)
        self.advice=Button(root,text="Advice Log",command=self.advice)
        self.analyize.pack(side=BOTTOM)
        self.advice.pack(side=BOTTOM)
        self.get=get_text()
        tab1=Frame(note)
        note.add(tab1,text=log_files[0])
        frame1 = Frame(tab1,width=100, height=200)
        frame1.pack()
        frame1.place(x=10,y=10)
        editArea1 = Text(tab1, width=100, height=100, wrap=WORD,fg='red',font=(16),bg="black")
        editArea1.pack()
        #editArea1.place(x=10,y=10)
        tab2=Frame(note)
        note.add(tab2,text=log_files[1])
        frame2 = Frame(tab2,width=100, height=200)
        frame2.pack()
        editArea2 = Text(tab2, width=100, height=100, wrap=WORD,font=(16), fg='red',bg="black")
        editArea2.pack()
        frame2.place(x=10,y=10)

        note.pack()
        tab1.bind('<Button-1>',self.get.open_file(editArea1,log_files[0]))
        tab2.bind('<Button-1>',self.get.open_file(editArea2,log_files[1]))

    def analyize(self):
        global x_list
        global label_list
        pyplot.rcParams['font.size'] = 24
        # get the dict like string "{'ls':(1, '125.9.0.9.12')}"
        str_dict= self.get.dict_from_log
        # convert the dict like string to DICT
        dict_str = ast.literal_eval(str_dict)
        mydict = { k : v for k,v in dict_str.iteritems() if v != 0 }
        # get the commands and occurance to plot them
        for i, j in mydict.iteritems():
            x_list.append(j[0])
            label_list.append(i)
        print "\n\r"
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
         global x_list
         global label_list
         # create child window
         win = Toplevel()
         win.geometry("1920x1080")
         # display message
         values=x_list
         keys=label_list
         data = dict(zip(keys, values))
         print 'data is ', data
         # Sort the data dictionary then reverse it
         items = [(v, k) for k, v in sorted(data.items(), key=operator.itemgetter(1), reverse=True)]
         print 'items ', items
         message="  \t\tServer advice \n\n"
         advice={
             'cd':'Secure the important directories in the server like configuration folders and files',\
             'delete':'All systems files must be hidden or undeleteable by default it doesn\'t show hidden files specially folders ',\
             'put':'The uploaded files to the server must be scaned before they are uploaded or must be unexcutable by applying \" chmod 644 \"',\
             'get':'Secure all system configuration files and make sure non can be downloadable by the hacker',\
             'rmdir':'all system folders must not be removeable by applying \" sudo chown -R root:root <directory name> && sudo chmod -R 700 <directory name> \" ',\
             'mkdir':'make sure the hackers can not overwrite any system\'s directory '
                 }

         for x in label_list:
             if x in advice:
                 message+= x +": " + advice[x]+"\n\n"
         advices=Label(win, text=message,font=("Helvetica", 16))
         advices.pack()
         Button(win, text='OK', command=win.destroy).pack()

if __name__ == "__main__":
    root = Tk()
    root.geometry("1920x1080")
    app = MyApp(root)
    root.mainloop()

