import socket
import threading
import time
user=''
server_address = ('0.0.0.0', 8090)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(server_address)
s_udp=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_udp.bind(server_address)
s_udp.setblocking(False)
if __name__ == '__main__':
    while 1:
            user=input("Username:")
            password=input("Password:")
            s.send((user+' '+user+' '+password).encode())
            data = s.recv(1024).decode()
            print(data)
            if data=='Welcome to Toom!':
                break;
    while 1:
            cmd=input("Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):")
            if cmd[0:4] == 'MSG ':
                s.send((user+' '+cmd).encode())
                print(s.recv(1024).decode())
                # Read responses on both sockets
            elif cmd[0:4] =='DLT ':
                s.send((user + ' ' + cmd).encode())
                print(s.recv(1024).decode())
            elif cmd[0:4] =='RDM ':
                s.send((user + ' ' + cmd).encode())
                print(s.recv(1024).decode())
            elif cmd[0:3] =='ATU':
                s.send((user + ' ' + cmd).encode())
                print(s.recv(1024).decode())
            elif cmd[0:4] =='UPD ':
                s.send((user +' '+cmd).encode())
                file_name=cmd[4:].split(' ')[-1]
                res= s.recv(1024).decode()
                tar_ip=res.split(' ')[0]
                tar_port=res.split(' ')[1]
                f=open(file_name,"rb")
                count =0;
                s_udp.sendto((user+' '+file_name).encode(),(tar_ip,int(tar_port)))
                print (s_udp)
                while 1:
                    send_data = f.read(1024)
                    if str(send_data) != "b''":
                        s_udp.sendto(send_data, (tar_ip,int(tar_port)))
                    else :
                        print("file has been send")
                        s_udp.sendto('end'.encode(), (tar_ip,int(tar_port)))
                        break
            elif cmd[0:3] =='OUT':
                s.send((user + ' '+cmd).encode())
                print(s.recv(1024).decode(),end="")
                s.close()
                break
            else :
                print("Error. Invalid command!")
            try:
                udp_data, addr = s_udp.recvfrom(1024)
                print(udp_data)
                if udp_data.split('.')[-1]=='mp4':
                    f=open("udp_data","rb")
                    print('Received {} from {}'.format(udp_data,udp_data.split(' ')[0]))
                elif udp_data=='end':
                    f.close()
                else:
                    f.write(udp_data)
            except socket.error:
                pass
            # data = s.recv(1024).decode()
            # print ('%s: received "%s"' % (s.getsockname(), data))