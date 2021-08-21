import os, sys
import socket
import cv2
import select
import threading
import  queue as Queue
from time import sleep
import  time
import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--port',default=8090,type=int)
parser.add_argument('--errcount',default=3,type=int)
opt=parser.parse_args()
def getTime():
    cur_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
    return cur_time
def writeData(dir,data):
    file = open(dir,"a")
    file.write(data+'\n')
    file.close()

errcount=opt.errcount
if errcount>=6 or errcount<=0 or isinstance(errcount,int)==False:
    print("invalid number of allowed failed consecutive attempt")
    sys.exit(0)
messagecount=1
dict={}
active_user={}
HOST = '0.0.0.0'
PORT = opt.port
buffersize = 1024
ADDR = HOST, PORT
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.bind(ADDR)
server.listen(128)
inputs = [server]
outputs = []
message_queues = {}
block={}
def block_step(user):
    global block
    while block[user]>0:
        sleep(1)
        block[user]-=1
while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    for index,s in enumerate(readable):
        # 新连接
        if s is server:
            # A "readable" socket is ready to accept a connection
            connection, client_address = s.accept()
            print('connection from', client_address)
            connection.setblocking(0)
            inputs.append(connection)
        # 旧连接
        else:
            data = s.recv(buffersize).decode()
            user=data.split(' ')[0]
            data=data[(len(user)+1):]
            if user in block and block[user]!=0:
                s.send("your account has been blocked for 10s")
                continue
            # 没登录
            if (user not in dict) or (dict[user]!=-1):
                tag=0
                for line in open("credentials.txt"):
                    line=line.strip('\n')
                    if line==data:
                        dict[user]=-1
                        tag=1
                        s.send("Welcome to Toom!".encode())
                        cur_time=getTime()
                        writeData(
                            'userlog.txt',str(index + 1) + '; ' + cur_time + '; ' + user + '; ' + str(
                                s.getpeername()[0]) + '; ' + str(s.getpeername()[1]))
                        active_user[user]=str(s.getpeername()[0])+' '+str(s.getpeername()[1])+' '+cur_time
                        break
                if tag==0:
                    if user not in dict:
                        dict[user]=0
                    if dict[user]>errcount:
                        dict[user]=1
                        block[user]=10
                        threading.Thread(target=block_step(user)).start()
                        s.send("Invalid Password. Your account has been blocked. Please try again later".encode())

                    else :
                        dict[user]+=1
                        s.send("Invalid Password. Please try again".encode())
            # 已经登录
            else:
                # MSG
                if data[0:4]=='MSG ':
                    # A readable client socket has data
                    data=data[4:]
                    if data !='':
                        print('received "%s" from %s' % (data, s.getpeername()))
                        cur_time=getTime()
                        writeData('messagelog.txt', str(messagecount) + '; ' + cur_time + '; ' + user + '; ' + data + '; ' + 'no')
                        print('{} posted MSG #{} "{}" at {}'.format(user,messagecount,data,cur_time))
                        s.send("Message #{} posted at {}.".format(messagecount,cur_time).encode())
                        messagecount+=1;
                    # 将收到的消息放入到相对应的socket客户端的消息队列中
                    # message_queues[s].put(data)
                    # Add output channel for response
                    # 将需要进行回复操作socket放到output 列表中, 让select监听
                    # if s not in outputs:
                    #     outputs.append(s)
                # DLT
                elif data[0:4]=='DLT ':
                    data = data[4:]
                    data_sp=data.split(' ')
                    tar_number=data_sp[0][1:]
                    tar_date=' '.join(data_sp[1:5])
                    tar_message=' '.join(data_sp[5:])
                    count=1
                    edit_tag=0
                    find_tag=0
                    with open("messagelog.txt", "r") as f:
                        lines = f.readlines()
                        with open("messagelog.txt", "w") as f:
                            for line in lines:
                                line_sp=line.split('; ')
                                number=line_sp[0]
                                date=line_sp[1]
                                this_user=line_sp[2]
                                cur_time=getTime()
                                if edit_tag==0:
                                    if number==tar_number and tar_date==date :
                                        edit_tag=1
                                        if user==this_user:
                                            s.send('{} deleted MSG {} “{}” at {}.'.format(user,number,message,cur_time).encode())
                                            print('{} deleted MSG {} “{}” at {}.'.format(user,number,message,cur_time))
                                            messagecount-=1
                                            continue
                                line_sp[0]='{}'.format(count)
                                line ='; '.join(i for i in line_sp)
                                f.write(line)
                                count+=1
                    if find_tag==0:
                        s.send("not find this message".encode())
                elif data[0:4]=='EDT ':
                    data = data[4:]
                    data_sp = data.split(' ')
                    tar_number = data_sp[0][1:]
                    tar_date = ' '.join(data_sp[1:5])
                    tar_message = ' '.join(data_sp[5:])
                    f = open("messagelog.txt", "r+")
                    for line in f:
                        line_sp = line.split('; ')
                        number = line_sp[0]
                        date = line_sp[1]
                        message = line_sp[3]
                        this_user = line_sp[2]
                        cur_time=getTime()
                        if number == tar_number and tar_date == date and this_user==user:
                            line_sp[3]=tar_message
                            line_sp[1]=cur_time
                            line_sp[-1]='yes'
                            line = '; '.join(i for i in line_sp)
                            f.write(line)
                            s.send("edit success")
                            break
                elif data[0:4]=='RDM ':
                    data = data[4:]
                    data_sp = data.split(' ')
                    tar_date = data_sp[3]
                    res=''
                    f = open("messagelog.txt", "r")
                    for line in f:
                        line_sp = line.split('; ')
                        date= line_sp[1].split(' ')[-1]
                        if date>=tar_date:
                            res+=line
                    s.send(res.encode())
                    print('{} issued RDM command.'.format(user))
                    print('return '+res)
                elif data[0:3]=='ATU':
                    data = data[4:]
                    res=''
                    for key in active_user:
                        res+=str(key)+' '+str(active_user[key])+'\n'
                    s.send(res.encode())
                    print('{} issued ATU command ATU.'.format(user))
                    print('return ' +res)
                elif data[0:4]=='UPD ':
                    data = data[4:]
                    custom=data.split(' ')[0]
                    tar_ip=active_user[custom].split(' ')[0]
                    tar_port=active_user[custom].split(' ')[1]
                    s.send((tar_ip+' '+tar_port).encode())
                elif data[0:3]=='OUT':
                    s.send('bye,{}'.format(user).encode())
                    active_user.pop(user)
                    inputs.remove(s)
                    print('{} log out'.format(user))
                    s.close()
