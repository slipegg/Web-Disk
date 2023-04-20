from file import *
from utils import *
from MySocket import *

from shutil import copyfile
import json
import os
import copy
from time import sleep
BLOCKSIZE = 1024 * 100


def get_parent_dir( dir):
    if dir == '/':
        return '/'
    # print(dir)
    index = 0
    for i in range(len(dir) - 2, -1, -1):
        if dir[i] == '/' or dir[i] == '\\':
            index = i
            break
    return dir[:index + 1]
def get_disk_path_by_local_and_dir(local_file_path,now_dir):
    local_parent=get_parent_dir(local_file_path)
    res=now_dir+local_file_path[len(local_parent):]
    print('get_disk_path_by_local_and_dir',res)
    return res

class User:
    def __init__(self):
        self.socket = None
        self.cookie = 'MTIyNjc2ZDg2Yjk1Y2FlOGJiZmU3NDhhYzkzZDcwNzQx'
        # mode :login register

    def login(self, username, passwd, mode):
        self.socket = Socket()
        request = mode
        self.socket.send(request.encode('gbk'))
        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv after login】", data)

        # username +passwd
        request = username + ' ' + passwd
        ret = self.socket.send(request.encode('gbk'))
        print("send bytes", ret)

        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print(data)
        info = json.loads(data)
        print("【recv after send username and passwd】", data)

        # if info['ack']==0:
        #     return False

        if mode == 'login' and info['ack'] == 1:
            self.username = username
            self.cookie = info['cookie']
            # return info['fileList']
        print('info:', info)
        return info

    # [{old_uf_path:"", new_uf_path:""}]
    def copy(self, copylist):
        for item in copylist:
            self.socket = Socket()
            request = "fileOperation " + self.cookie
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send copy ", str(data))

            request = "copy " + self.cookie + " " + item['old_uf_path'] + " " + item['new_uf_path']
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send copy", str(data))
            self.socket.close()
        return True

    # {file[],floder[]}
    def delete(self, target):
        # print(target['file'])
        for file in target['file']:
            self.socket = Socket()
            request = "fileOperation " + self.cookie
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send delFile ", str(data))

            request = "delFile " + self.cookie + " " + file
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send delFile ", str(data))
            self.socket.close()

        for floder in target['folder']:
            self.socket = Socket()
            request = "fileOperation " + self.cookie
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send delDir ", str(data))

            request = "delDir " + self.cookie + " " + floder
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send delDir ", str(data))
            self.socket.close()
        return True
    def is_quick_upload(self,file_path,remote_dir):
        res={}
        if not os.path.exists(file_path):
            return False
        statinfo = os.stat(file_path)
        file_length = statinfo.st_size

        self.socket = Socket()
        MD5 = get_file_md5(file_path)
        request = "fastUpload " + self.cookie
        self.socket.send(request.encode('gbk'))
        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv】after send is_quick_upload ", str(data))
        # remote_dir# + file_path.split('/')[-1]

        remote_path = get_disk_path_by_local_and_dir(file_path,remote_dir)

        request = MD5 + " " + self.cookie + " " + remote_path + " " + str(file_length)
        self.socket.send(request.encode('gbk'))

        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv】after send MD5 ", str(data))
        self.socket.close()
        res['md5']=MD5
        res['file_length']=file_length

        if (data == '1'):
            res['is_exist']=True
        else:
            res['is_exist']= False
        res['upload_length']=0
        return res

    def makedir(self,full_path):
        self.socket = Socket()
        request = "fileOperation " + self.cookie
        self.socket.send(request.encode('gbk'))

        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv】after send mkdir ",str(data))

        request = "mkdir " + self.cookie +" "+full_path
        self.socket.send(request.encode('gbk'))

        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv】after send mkdir",str(data))
        self.socket.close()
        return True

    def cut(self,cutlist):
        for item in cutlist:
            self.socket = Socket()
            request = "fileOperation " + self.cookie
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send cut ",str(data))

            request = "cut " + self.cookie +" "+item['old_uf_path'] + " "+item['new_uf_path']
            self.socket.send(request.encode('gbk'))

            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send cut",str(data))
            self.socket.close()
        return True

    # def upload(self, file_path, remote_path, md5):  # 本地路径、虚拟路径
    #     if not os.path.exists(file_path):
    #         return False
    #     MD5 = get_file_md5(file_path)
    #
    #     self.socket = Socket()
    #     # send upload and token
    #     request = self.cookie
    #     self.socket.send(('upload '+self.cookie).encode('utf-8'))
    #     fd = open(file_path, 'rb')
    #
    #     while True:
    #         # {fin:0,seq:0,length:102400}
    #         block = self.socket.recv(BLOCKSIZE).decode('utf-8')
    #
    #         if block['fin']:
    #             break
    #         else:
    #             send_cnt = 0
    #             while send_cnt < block['length']:
    #                 fd.seek(block['seq'] + send_cnt, 0)
    #                 data = fd.read(block['length'] - send_cnt)
    #                 send_cnt += self.socket.send(data)
    #         res = db_exec("select is_upload form uploadHistory where uf_md5='{}'"
    #                       .format(md5))
    #         if res[0][0] == '0':
    #             self.socket.close()
    #             break

    def upload(self,file_path,remote_path, md5):
        res = db_exec('select is_upload from uploadHistory where uf_md5="{}"'
                      .format(md5))
        if res[0][0] == '0':
            return

        if not os.path.exists(file_path):
            return False
        MD5 =md5
        statinfo = os.stat(file_path)

        self.socket = Socket()
        # send upload and token
        request = "upload "+ self.cookie
        print(request)
        self.socket.send(request.encode('gbk'))
        remote_path = get_disk_path_by_local_and_dir(file_path, remote_path)

        data = self.socket.recv(BLOCKSIZE).decode('utf-8')
        print("【recv】after send upload ",str(data))

        request = MD5 + " " + str(statinfo.st_size) + " " + self.cookie + " " + remote_path
        self.socket.send(request.encode('gbk'))
        print(request)

        fd = open(file_path,'rb')

        loop=1

        is_upload=True
        while is_upload:
            #{fin:0,seq:0,length:102400}
            block = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("which part to upload:",block)
            block = json.loads(block)
            sum_upload=block['byte_num']
            db_exec('update uploadHistory set upload_length ="{}" where uf_md5="{}"'
                    .format(sum_upload,MD5))
            if 'end_pos' not in block.keys():
                break
            else:
                length = block['end_pos'] - block['start_pos']
                send_cnt = 0
                oncce_len=length//10
                while send_cnt < length:
                    res=db_exec('select is_upload from uploadHistory where uf_md5="{}"'
                                .format(MD5))
                    if res[0][0]=='0':
                        self.socket.close()
                        is_upload=False
                        break
                    # sleep(1)

                    fd.seek(block['start_pos'] + send_cnt,0)
                    end_len=send_cnt+oncce_len
                    if length<end_len:
                        end_len=length
                    data = fd.read(end_len - send_cnt)
                    try:
                        ret = self.socket.send(data)
                        if ret == 0:
                            print("send num is 0,ERROR")
                            loop=0
                            break
                        send_cnt += ret
                        db_exec('update uploadHistory set upload_length = upload_length+{} where uf_md5="{}"'
                                .format(ret, MD5))
                        print('update uploadHistory!',MD5,ret)

                    except Exception as e:
                        loop=0
                        print("send recv exception", e.__str__())
                        break
        self.socket.close()
        fd.close()
        res=db_exec('update uploadHistory set is_upload ="0" where uf_md5="{}"'
                                .format(MD5))
    # fielPath : where to store (maybe exist)
    # MD5 : which one to download
    # down_length: 本地已存在长度
    # isDownload: 是否正在下载

    def download(self, files):
        for file in files:
            MD5 = file['uf_md5']
            down_length = int(file['down_length'])
            file_length = int(file['file_length'])
            file_path = file['full_path']
            print('file_path :',file_path )
            file_parent=file['parent_dir']

            fd = open(file_path, 'ab+')  # create if not exist
            seq = fd.tell()  # get length
            print(seq, down_length)
            if (down_length != seq):
                # fd.close()
                # os.remove(file_path)
                # fd=open(file_path, 'ab+')
                if file_parent!="":
                    sql='update historyFile set down_length = down_length+ {} where uf_md5="{}"'\
                        .format(str(seq-down_length),file_parent)
                    print(sql)
                    db_exec(sql)
                down_length=seq

            cnt = 0
            # 断线重连
            # for i in range (0,int(config['network']['reconnectLimit'])):
            # if True:
            # try:
            # if True:
            self.socket = Socket()
            # send download and token
            request = "download " + self.cookie
            self.socket.send(request.encode('gbk'))
            data = self.socket.recv(BLOCKSIZE).decode('utf-8')
            print("【recv】after send download ", str(data))

            # send needed file MD5
            request = MD5 + " " + str(seq) + " " + str(file_length - down_length)
            print(request)
            self.socket.send(request.encode('gbk'))

            # sql_update_isdownload = \
            #     "update historyFile set is_download = '1' where file_path = '" + file_path + "'"
            # db_exec(sql_update_isdownload)

            while down_length < file_length:
                if file_parent!="":
                    sql_isdownload = \
                        "select is_download from historyFile where uf_md5 = '" + file_parent + "'"
                else:
                    sql_isdownload = \
                        "select is_download from historyFile where uf_md5 = '" + MD5 + "'"
                res = db_exec(sql_isdownload)
                print("res", res)
                if (res[0][0] == '0'):
                    # fd.close()
                    # self.socket.close()
                    # exit()
                    time.sleep(1)
                    continue

                # statinfo = os.stat(file_path)
                # time.sleep(1)
                data = self.socket.recv(BLOCKSIZE)
                if not data:
                    fd.close()
                    self.socket.close()
                    db_exec('update historyFile set is_download ="0" where uf_md5 ="'+MD5+'"')
                    raise Exception("【ERROR】server socket close")
                    # print("接收空")

                # p = copy.copy(data[0:20])
                cnt += 1
                print(cnt, "recv len:", str(len(data)), "down_lenth...", down_length,
                      " real length:", file_length)  # , "content:",p.decode('gbk'))

                # fd = open("./myfile/"+str(cnt),'wb')
                # fd.write("【recv】:"+ str(len(data)) +"字节")
                fd.write(data)
                # fd.close()
                down_length += len(data)

                if file_parent!="":
                    sql_update_down_length = \
                        "update historyFile set down_length = down_length+'" + str(len(data)) + "' where uf_md5 = '" + file_parent + "'"
                    # print(sql_update_down_length)
                    db_exec(sql_update_down_length)

                sql_update_down_length = \
                    "update historyFile set down_length = '" + str(down_length) + "' where uf_md5 = '" + MD5 + "'"
                # print(sql_update_down_length)
                db_exec(sql_update_down_length)

            # catch exception and reconnect
            # except Exception as e:
            #     print("FOR ERROR",e)
            self.socket.close()
            fd.close()

            # set is_download 0
            sql_update_isdownload = \
                "update historyFile set is_download ='0' where uf_md5 = '" + MD5 + "'"

            db_exec(sql_update_isdownload)
        if file_parent!="":
            sql_update_isdownload = \
                "update historyFile set is_download ='0' where uf_md5 = '" + file_parent + "'"
            db_exec(sql_update_isdownload)
        return True

if __name__ == '__main__':
    res=get_disk_path_by_local_and_dir(r'D:\PyCharm\testwebDisk\testQQ\dsaf.ui','/')
    # user = User()
    # user.login('kong', '123456', 'register')
    # user.login('kong', '123456', 'login')
    # user.upload('file_path')
    # name = './large18'
    # sql = "insert into historyFile values (39,'462458279c9a2111aad54b4350840a70',0,82749750,'"+ name +"',0,0)"

    # db_exec(sql)
#     str_file = \
# '[{"MD5":"462458279c9a2111aad54b4350840a70","down_length":0,"file_length":82749750,"full_path":"'+name+'"}]'

# j_file = json.loads(str_file)

# user.download(j_file)
# open('/ttt/aaa.txt','ab+')
# md5 = get_file_md5('F:/linux-3.10.tar.gz')
# print(md5)
# download('./b.txt','qqqq')