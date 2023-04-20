import socket   
import sys
import time
from utils import *


class Socket:
    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        self.reconnect()
    def reconnect(self):
        for i in range(0,config['network']['reconnectLimit']):
            time.sleep(3)
            try:
                self.socket = socket.socket()   # 创建socket对象
                self.socket.connect((self.ip, self.port))   #建立连接
                log.write(getNowTime() + " No. " + i +" try to connect")
                break
            except Exception as e:
                log.write(getNowTime() +" connect failed")
                
    def send(self,data):
        try:
            ret = self.socket.send(data)
        except Exception as e:
            log.write(getNowTime() + " connection closed")
            self.reconnect()
        finally:
            return ret
    
    def recv(self,recv):
        try:
            data = self.socket.recv()
        except Exception as e:
            log.write(getNowTime() + " connection closed")
            self.reconnect()
        finally:
            return data.decode('gbk')


if __name__ == '__main__':
    socket = Socket(config['network']['ip'], config['network']['port'])
    # localFiles = FileList(LOCAL_KEYS)
    # remoteFiles = FileList(LOCAL_KEYS)
    # downloadFiles = FileList(LOCAL_KEYS)
    i=32
    while True:
        info = char(i)*100
        print(info)
        time.sleep(0.1)
        socket.send(info)
        # ab=input('客户端发出：')
        # if ab=='quit':
        #     c.close()                                               #关闭客户端连接
        #     sys.exit(0)
        # else:
        #     c.send(ab.encode('utf-8'))                               #发送数据
        #     data=c.recv(1024)                                        #接收一个1024字节的数据
        #     print('收到：',data.decode('utf-8'))