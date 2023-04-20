import socket 
import time
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # 创建socket对象
s.bind(('127.0.0.1',10000))                                      # 绑定地址
s.listen(5)                                                     # 建立5个监听
while True:
    conn,addr= s.accept()                                       # 等待客户端连接
    print('欢迎{}'.format(addr))                              #打印访问的用户信息
    data=conn.recv(1024).decode('utf-8')
    print("recive: ",data)

    conn.send('ack'.encode('utf-8'))

    data=conn.recv(1024).decode('utf-8')
    print("recive: ",data)

    conn.send('{"ack":1,"cookie":"cookie"}'.encode('utf-8'))
    # i=0
    # while True:
    #     i+=1
    #     ss = str(i)*10
    #     ret = conn.send(ss.encode('utf-8'))
    #     time.sleep(1)
    #     print("send ",i," return ",ret)
        # aa=input('服务器发出：') 
        # if aa=='quit':
        #     conn.close()                                        #关闭来自客户端的连接
        #     s.close()                                           #关闭服务器端连接
        # else:
        #     conn.send(aa.encode('utf-8'))