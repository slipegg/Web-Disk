#self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
import sys
import os
import shutil
from utils import *
from time import sleep
from scapy.all import ifaces
from threading import Thread
from PyQt5.QtWidgets import *
from login import Ui_Dialog as ui_loginDialog
from register import Ui_Dialog as ui_registerDialog
from mainWindow import Ui_MainWindow as ui_mainWindow
from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QBrush
from fileTable import Ui_Form as ui_fileTable
from file import fileDb,db_exec,dbUserName
from download import Ui_Form as ui_downloadTable
from finishDownLoad import Ui_Form as ui_finishDownLoadTable
import random
from upload import Ui_Form as ui_uploadTable
from sock import *
from user import *
user=User()
donwloadLimit=3
downloadsum=0

registerW=None
loginW=None
mainW=None

class uploadTable(QWidget,ui_uploadTable):
    def __init__(self):
        super(uploadTable, self).__init__()
        self.setupUi(self)

class finishDownLoadTable(QWidget,ui_finishDownLoadTable):
    def __init__(self):
        super(finishDownLoadTable, self).__init__()
        self.setupUi(self)

class loginWindow(QWidget,ui_loginDialog):
    def __init__(self):
        super(loginWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("网盘")
        self.LoginButton.clicked.connect(self.login)
        self.registerButton.clicked.connect(self.register)
    def login(self):
        userName=self.userName.text()
        userPasswd=self.userPasswd.text()
        res=user.login(userName,userPasswd,'login')
        if res['res']==0:#登陆成功
            self.close()
            global mainW
            print('user file_tree:',res['file_tree'])
            mainW=mainWindow(res['file_tree'],userName)
            mainW.show()
        elif res['res']==1:
            QMessageBox.warning(self, "提醒", "密码错误", QMessageBox.Yes)
        elif res['res']==2:
            QMessageBox.warning(self, "提醒", "用户不存在", QMessageBox.Yes)
        else:
            QMessageBox.warning(self, "提醒", "网络状态不佳，请重试", QMessageBox.Yes)

    def register(self):
        self.hide()
        global registerW
        registerW=registerWindow()
        registerW.show()

class registerWindow(QWidget,ui_registerDialog):
    def __init__(self):
        super(registerWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("网盘")
        self.registerButton.clicked.connect(self.register)
        self.backButton.clicked.connect(self.back_login)

    def testPasswd(self,s):
        kind = [0, 0, 0, 0]
        for c in s:
            if c >= 'a' and c <= 'z':
                kind[0] = 1
            elif c >= 'A' and c <= 'Z':
                kind[1] = 1
            elif c >= '0' and c <= '9':
                kind[2] = 1
            else:
                kind[3] = 1
        print(kind)
        if (sum(kind) < 3 or len(s) < 12 ):
            return False
        else:
            return True
    def register(self):
        userName=self.userName.text()
        passwd=self.passwd.text()
        passwd_2=self.passwd_2.text()
        print(userName,passwd,passwd_2)
        if(passwd!=passwd_2):
            QMessageBox.warning(self, "提醒", "输入的两次密码不一样", QMessageBox.Yes)
            return
        if( not self.testPasswd(passwd)):
            QMessageBox.warning(self, "提醒", "密码强度不够", QMessageBox.Yes)
            return
        res = user.login(userName, passwd, 'register')
        if res['res']== 0:  # 注册成功
            self.hide()
            loginW.show()
        elif res['res']==1:
            QMessageBox.warning(self, "提醒", "该用户名已存在", QMessageBox.Yes)
        elif res['res']==-1:
            QMessageBox.warning(self, "提醒", "网络状态不佳，请重试", QMessageBox.Yes)

    def back_login(self):
        self.hide()
        loginW.show()

def upload_file(fileInfoList):
    for fileInfo in fileInfoList:#实际上只有一个，只考虑单文件上传了
        user.upload(fileInfo['localFilePath'],fileInfo['diskPath'],fileInfo['uf_md5'])
        # upload_length=random.randint(0,fileInfo['file_length'])
        # sleepTime=3
        # while upload_length<fileInfo['file_length']:
        #     res=db_exec("select is_upload from uploadHistory where uf_md5='{}'".format(fileInfo['uf_md5']))
        #     print('upload_file res:',res)
        #     if res[0][0]=='0':
        #         sleep(1)
        #         continue
        #     onceLen=random.randint(0,fileInfo['file_length']//5)
        #     if onceLen>fileInfo['file_length']-upload_length:
        #         onceLen=fileInfo['file_length']-upload_length
        #     upload_length=onceLen+upload_length
        #     db_exec("update uploadHistory set upload_length={} where uf_md5='{}'".format(upload_length,fileInfo['uf_md5']))
        #     sleep(sleepTime)
        # print('delete:',fileInfo)
        # db_exec("delete from uploadHistory where uf_md5='{}'".format( fileInfo['uf_md5']))

def download_file(fileInfoList):
    # print('fileInfoList:',fileInfoList)
    for fileInfo in fileInfoList:
        # [{'uf_md5': 'childmd5', 'down_length': 0, 'file_length': 100, \
        # 'file_path': 'D:/Source/webDisk/netDisk', 'file_name': '5.txt', \
        #     'is_download': '0','bar':None,'button':None}]
        print('fileInfo:',fileInfo)
        # uf_name=fileInfo['file_name']
        uf_md5=fileInfo['uf_md5']
        down_path=fileInfo['file_path']
        file_name = fileInfo['file_name']
        uf_length=int(fileInfo['file_length'])
        parent = ""
        print("uf_md5",uf_md5,"down_path:",down_path,"file_name",file_name,"uf_length:",uf_length)
        #获取已经下载的长度
        sql="select down_length from historyFile where uf_md5='{}'".format(uf_md5)
        res=db_exec(sql)

        recv_num=int(res[0][0])
        sleepTime=1
        res_file=None
        while recv_num<uf_length: #当没有下载完的时候
            # once_len=random.randint(0,90)
            if 'parent_dir' in fileInfo.keys():#说明是下载一个文件夹
                parent = fileInfo['parent_dir']
                sql= "select is_download from historyFile where uf_md5='{}'".format(fileInfo['parent_dir'])
                # print(sql)
                res_file=db_exec(sql)
                # # print(res)
                # # para = []
                # if res[0][0] == '1':
                #     sql = "select uf_md5,down_length,file_lenth,file_path,file_name,is_folder from historyFile where file_directory='{}'".formate(uf_md5)
                #     res=db_exec(sql)
                #     for item in res:
                #         if not is_folder :
                #             needed_lenth = min(item[2] - item[1], BLOCKSIZE)  
                #             para.append({"MD5":item[0],"down_length":item[1],"needed_length":needed_lenth,
                #             "full_path":item[3] +'/'+ item[4]})
                #     print(para)
                #     user.download(para)

            #是一个文件
            else:
                res_file = db_exec("select is_download,down_length from historyFile where uf_md5='{}'".format(uf_md5))
            
            if res_file[0][0] == '1':
                needed_lenth = min(uf_length - res_file[0][1], BLOCKSIZE)  
                para ={"MD5":uf_md5,"down_length":res_file[0][1],"needed_length":needed_lenth,
                "full_path":down_path +'/'+file_name,"parent":parent}
                print(para)
                user.download(para)

            #print('download res:',res)
            if res[0][0] == '0':#如果不存在socket就不管，如果存在就停止下载传输
                sleep(1)
                continue
            #如果没有socket就建立，如果有就继续下载
            # if recv_num+once_len>=uf_length:
            #     once_len=uf_length-recv_num
            ###############
            #sock接收一段长度，然后继续往下走
            ###############
            # recv_num += once_len
            # sleep(sleepTime)
            #print('recv_num:',recv_num)
            #print("update historyFile set down_length={} where uf_md5='{}'".format(recv_num,uf_md5))

            # db_exec("update historyFile set down_length={} where uf_md5='{}'".format(recv_num,uf_md5))
            #print('fileInfo:',fileInfo)
            # if 'parent_dir' in fileInfo.keys():#update文件夹的下载长度
            #     #print('update parent!')
            #     sql="update historyFile set down_length=down_length+{} where uf_md5='{}'".format(once_len,fileInfo['parent_dir'])
            #     db_exec(sql)
            #     #print(sql)

        # db_exec("update historyFile set is_download='0' where uf_md5='{}' and down_length=file_length".format(uf_md5))

    if 'parent_dir' in fileInfoList[0].keys():#如果是文件夹下载
        db_exec("update historyFile set is_download='0' where uf_md5='{}'".format(fileInfoList[0]['parent_dir']))


# def download_file(fileInfoList):
#     print('fileInfoList:',fileInfoList)
#     for fileInfo in fileInfoList:
#         print('fileInfo:',fileInfo)
#         # uf_name=fileInfo['file_name']
#         uf_md5=fileInfo['uf_md5']
#         down_path=fileInfo['file_path']
#         uf_length=int(fileInfo['file_length'])
#         #获取已经下载的长度
#         res=db_exec("select down_length from historyFile where uf_md5='{}'".format(uf_md5))
#         print('recv:',res[0][0])
#         recv_num=int(res[0][0])
#         sleepTime=1
#         while recv_num<uf_length: #当没有下载完的时候
#             once_len=random.randint(0,90)
#             if 'parent_dir' in fileInfo.keys():#说明是下载一个文件夹
#                 res=db_exec("select is_download from historyFile where uf_md5='{}'".format(fileInfo['parent_dir']))
#             else:
#                 res = db_exec("select is_download from historyFile where uf_md5='{}'".format(uf_md5))
#             print('download res:',res)
#             if res[0][0] == '0':#如果不存在socket就不管，如果存在就停止下载传输
#                 sleep(1)
#                 continue
#             #如果没有socket就建立，如果有就继续下载
#             if recv_num+once_len>=uf_length:
#                 once_len=uf_length-recv_num
#             ###############
#             #sock接收一段长度，然后继续往下走
#             ###############
#             recv_num += once_len
#             sleep(sleepTime)
#             print('recv_num:',recv_num)
#             print("update historyFile set down_length={} where uf_md5='{}'".format(recv_num,uf_md5))

#             db_exec("update historyFile set down_length={} where uf_md5='{}'".format(recv_num,uf_md5))
#             print('fileInfo:',fileInfo)
#             if 'parent_dir' in fileInfo.keys():#update文件夹的下载长度
#                 print('update parent!')
#                 sql="update historyFile set down_length=down_length+{} where uf_md5='{}'".format(once_len,fileInfo['parent_dir'])
#                 db_exec(sql)
#                 print(sql)

#         db_exec("update historyFile set is_download='0' where uf_md5='{}' and down_length=file_length".format(uf_md5))

#     if 'parent_dir' in fileInfoList[0].keys():#如果是文件夹下载
#         db_exec("update historyFile set is_download='0' where uf_md5='{}'".format(fileInfoList[0]['parent_dir']))

class mainWindow(QMainWindow,ui_mainWindow):
    def __init__(self,file_tree_str_json,userName):
        super(mainWindow, self).__init__()
        self.userName=userName
        self.fb = fileDb()
        self.fb.setName(self.userName)

        self.setupUi(self)
        self.setWindowTitle("网盘")
        self.hello.setText(userName+',你好')
        self.downloadList=[]
        self.uploadList=[]
        self.allFileList=[]
        self.clipboard={"uf_path":"","uf_file_name":"","uf_file_type":"","operate":""}
        self.pasteButton.clicked.connect(self.paste)

        self.fileTable=fileTable()
        self.downloadTable=downloadTable()
        self.finishDownloadTable=finishDownLoadTable()
        self.uploadTable=uploadTable()
        self.filishUploadTable=uploadTable()
        self.folderUploadButton.clicked.connect(self.folderUpload)
        self.nowDirEdit.returnPressed.connect(self.go_by_line_edit)
        self.showDownload.clicked.connect(self.changeDownloadTable)
        self.uploadButton.clicked.connect(self.upload)
        self.createFolderButton.clicked.connect(self.createFolder)
        self.fileTable.tableWidget.doubleClicked.connect(self.go_dir_by_click)

        print('file_tree_str_json',file_tree_str_json)
        self.fb.init_by_json_str(file_tree_str_json)

        self.now_dir='/'
        self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
        self.timer=QTimer()
        self.timer.timeout.connect(self.timer_operate)

        self.timer.start(500)
        self.fileTable.show()
        self.fileTableLayout.addWidget(self.fileTable)
        self.downLoadLayout.addWidget(self.downloadTable)
        self.uploadLayout.addWidget(self.uploadTable)
        self.downloadTable.show()
        self.downLoadLayout.addWidget(self.finishDownloadTable)
        self.finishDownloadTable.hide()
        self.draw_file_table()
        self.draw_downLoadTable()
        self.draw_finishDownLoadTable()
        self.draw_uploadTable()

    def folderUpload(self):
        file_path = QFileDialog.getExistingDirectory(None, "选取要上传的文件夹", "./")
        print(file_path)
        if file_path=='':
            return
        son_file_info=self.fb.get_file_list_by_dir(self.now_dir)
        f_n=self.fb.get_file_name_by_path(file_path)
        for s in son_file_info:
            if f_n==s[0]:
                QMessageBox.warning(self, "提示", "当前云端目录已有该"+f_n+"文件夹", QMessageBox.Yes)
                return

        all_son_file=self.fb.get_all_local_files_by_folder(file_path)
        print(all_son_file)
        print(self.now_dir+f_n)
        uf_up_time = strftime('%Y-%m-%d %H:%M:%S', localtime())
        if user.makedir(self.now_dir+f_n+'/'):
            db_exec(
                "insert into userFile(uf_md5,uf_length,uf_path,uf_file_name,uf_file_type,uf_up_time) values('{}','{}','{}','{}','{}','{}')"
                    .format('', '', self.now_dir, f_n, '文件夹', uf_up_time)
            )
        upload_list=[]
        for i in range(len(all_son_file)):#只是子文件遍历
            if all_son_file[i]['is_dir']==True:
                new_dir=(all_son_file[i]['file_name'].replace(file_path[:len(file_path)-len(f_n)],self.now_dir).replace('\\','/')+'/')
                print('folder upload new_dir:',new_dir)
                if user.makedir(new_dir):
                    db_exec(
                        "insert into userFile(uf_md5,uf_length,uf_path,uf_file_name,uf_file_type,uf_up_time) values('{}','{}','{}','{}','{}','{}')"
                        .format('', '', new_dir[:len(new_dir)-len(new_dir[:-1].split('/')[-1])-1], new_dir[:-1].split('/')[-1], '文件夹', uf_up_time)
                        )
            else:
                continue


                disk_path=all_son_file[i]['file_name'].replace(file_path[:len(file_path)-len(f_n)],self.now_dir).replace('\\','/')
                disk_path=disk_path[:len(disk_path)-len(disk_path.split('/')[-1])]
                one_upload=all_son_file[i]['file_name'],disk_path,get_file_md5(all_son_file[i]['file_name'])
                print(one_upload)

                res = user.is_quick_upload(all_son_file[i]['file_name'], disk_path)
                if res['is_exist']:
                    QMessageBox.warning(self, "提示", "文件秒传成功", QMessageBox.Yes)
                    self.fb.addFile(res['md5'], all_son_file[i]['file_name'], disk_path, res['file_length'])
                    # self.fileList = self.fb.get_file_list_by_dir(self.now_dir)
                    # self.draw_file_table()
                else:
                    db_exec(
                        "insert into uploadHistory(uf_md5,upload_length,file_length,local_file_path,disk_path,is_upload) values ('{}',{},{},'{}','{}','{}')"
                            .format(res['md5'], res['upload_length'], res['file_length'], all_son_file[i]['file_name'], disk_path,
                                    '1'))
                    self.oneFileUpload(all_son_file[i]['file_name'], disk_path, res['md5'], res['upload_length'],
                                       res['file_length'], '1')
        self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
        self.draw_file_table()

    def createFolder(self):
        txt=self.newFolderName.text()
        if txt=='':
            QMessageBox.warning(self, "提示", "文件夹为空，不能下载", QMessageBox.Yes)
        uf_up_time=strftime('%Y-%m-%d %H:%M:%S', localtime())
        if user.makedir(self.now_dir+txt+'/'):
            db_exec("insert into userFile(uf_md5,uf_length,uf_path,uf_file_name,uf_file_type,uf_up_time) values('{}','{}','{}','{}','{}','{}')"
                    .format('','',self.now_dir,txt,'文件夹',uf_up_time)
                    )
        self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
        self.draw_file_table()

    def paste(self):
        print('paste')
        pasteList=[]
        if self.clipboard['operate']=='':
            return
        ##判断文件或者文件夹是否已经存在

        for f in self.fileList:
            if self.clipboard['uf_file_type']=='文件夹':
                if f[0]==self.clipboard['uf_file_name'] and self.clipboard['uf_file_type']==f[2]:
                    QMessageBox.warning(self, "提醒", "该文件夹已经在当前目录", QMessageBox.Yes)
                    return
            else:
                if f[0]==self.clipboard['uf_file_name'] and self.clipboard['uf_file_type']==f[2]:
                    QMessageBox.warning(self, "提醒", "该文件已经在当前目录", QMessageBox.Yes)
                    return
        if self.clipboard['operate']=='cut':
            if self.clipboard['uf_file_type']!='文件夹':#文件剪贴
                temp={}
                temp['old_uf_path']=self.clipboard['uf_path']+self.clipboard['uf_file_name']
                temp['new_uf_path']=self.now_dir+self.clipboard['uf_file_name']
                pasteList.append(temp)
                print('pasteList:',pasteList)
                if user.cut(pasteList):
                    db_exec("update userFile set uf_path='{}' where uf_path='{}' and uf_file_name='{}'"
                            .format(self.now_dir,self.clipboard['uf_path'],self.clipboard['uf_file_name']))
            else:#文件夹剪贴
                print('文件夹剪贴')
                res = db_exec(
                    "select uf_path,uf_file_name,uf_file_type from userFile where uf_path like '{}%' "
                        .format(self.clipboard['uf_path']+self.clipboard['uf_file_name'] + '/'))
                print(res)

                for r in res:
                    temp={}
                    temp['old_uf_path'] = r[0] + r[1]
                    print((r[0],self.clipboard['uf_path'],self.now_dir))
                    temp['new_uf_path'] = self.fb.change_file_mulu(r[0],self.clipboard['uf_path'],self.now_dir)+r[1]
                    if r[2]=='文件夹':
                        temp['old_uf_path']+='/'
                        temp['new_uf_path']+='/'
                    pasteList.append(temp)
                temp={}
                temp['old_uf_path']=self.clipboard['uf_path']+self.clipboard['uf_file_name'] + '/'
                temp['new_uf_path'] = self.now_dir+self.clipboard['uf_file_name'] + '/'
                pasteList.append(temp)
                if user.cut(pasteList):
                    for r in res:
                        new_uf_path=self.fb.change_file_mulu(r[0],self.clipboard['uf_path'],self.now_dir)

                        db_exec("update userFile set uf_path='{}' where uf_path='{}' and uf_file_name='{}'"
                            .format(new_uf_path,r[0],r[1]))
                    db_exec("update userFile set uf_path='{}' where uf_path='{}' and uf_file_name='{}'"
                            .format(self.now_dir,self.clipboard['uf_path'], self.clipboard['uf_file_name']))
                print('剪贴文件夹：',pasteList)
            self.clipboard['uf_path']=self.now_dir
            self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()
        elif self.clipboard['operate'] == 'copy':
            if self.clipboard['uf_file_type']!='文件夹':#文件复制
                temp={}
                temp['old_uf_path']=self.clipboard['uf_path']+self.clipboard['uf_file_name']
                temp['new_uf_path']=self.now_dir+self.clipboard['uf_file_name']
                pasteList.append(temp)
                print('pasteList:',pasteList)
                if user.copy(pasteList):
                    sql="insert into userFile(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time) select uf_md5,'{}',uf_file_name,uf_length,uf_file_type,uf_up_time from userFile where uf_file_name='{}' and uf_path='{}' limit 1"\
                        .format(self.now_dir,self.clipboard['uf_file_name'],self.clipboard['uf_path'])
                    print(sql)
                    db_exec(sql)
            else:#文件夹粘贴
                print('文件夹粘贴')
                res = db_exec(
                    "select uf_path,uf_file_name,uf_file_type from userFile where uf_path like '{}%' "
                        .format(self.clipboard['uf_path']+self.clipboard['uf_file_name'] + '/'))
                print(res)

                for r in res:
                    temp={}
                    temp['old_uf_path'] = r[0] + r[1]
                    print((r[0],self.clipboard['uf_path'],self.now_dir))
                    temp['new_uf_path'] = self.fb.change_file_mulu(r[0],self.clipboard['uf_path'],self.now_dir)+r[1]
                    if r[2]=='文件夹':
                        temp['old_uf_path']+='/'
                        temp['new_uf_path']+='/'
                    pasteList.append(temp)
                temp={}
                temp['old_uf_path']=self.clipboard['uf_path']+self.clipboard['uf_file_name'] + '/'
                temp['new_uf_path'] = self.now_dir+self.clipboard['uf_file_name'] + '/'
                pasteList.append(temp)
                if user.copy(pasteList):
                    for r in res:
                        new_uf_path=self.fb.change_file_mulu(r[0],self.clipboard['uf_path'],self.now_dir)
                        sql = "insert into userFile(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time) select uf_md5,'{}',uf_file_name,uf_length,uf_file_type,uf_up_time from userFile " \
                              "where uf_file_name='{}' and uf_path='{}' limit 1" \
                            .format(new_uf_path,r[1],r[0])
                        print(sql)
                        db_exec(sql)
                    db_exec("insert into userFile(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time) select uf_md5,'{}',uf_file_name,uf_length,uf_file_type,uf_up_time from userFile "
                            "where uf_file_name='{}' and uf_path='{}' limit 1" \
                             .format(self.now_dir, self.clipboard['uf_file_name'],self.clipboard['uf_path']))
                print('粘贴文件夹：',pasteList)
            self.clipboard['uf_path']=self.now_dir
            self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()

    def draw_uploadTable(self):
        db_exec("update uploadHistory set is_upload='0'")
        while self.uploadTable.tableWidget.rowCount() > 0:
            self.uploadTable.tableWidget.removeRow(0)
        res=db_exec('select * from uploadHistory where upload_length<file_length')
        for r in res:
            self.oneFileUpload(r[4],r[5],r[1],r[2],r[3],r[6])

    def uploadListBtnOperate(self):
        button = self.sender()
        if button:
            row = self.uploadTable.tableWidget.indexAt(button.pos()).row()

            print('row:',row)
            # print(self.downloadList)
            # print(self.downloadList[len(self.downloadList)-1-row])
            md5=self.uploadTable.tableWidget.item(row,2).text()
            print('md5:',md5)
            if button.text()=='继续':
                button.setText("暂停")
                sql='update uploadHistory set is_upload="1" where uf_md5="{}"'.format(md5)
                db_exec(sql)
                res=db_exec('select local_file_path,disk_path,uf_md5 from uploadHistory where uf_md5="{}"'
                            .format(md5))

                Thread(target=user.upload, args=(res[0][0],res[0][1],res[0][2],)).start()

            elif button.text()=='暂停':
                button.setText("继续")
                sql='update uploadHistory set is_upload="0" where uf_md5="{}"'.format(md5)
                db_exec(sql)

    def oneFileUpload(self,localFilePath,diskPath,uf_md5,upload_length,file_length,is_upload):
        temp={}
        temp['uf_md5']=uf_md5
        temp['localFilePath']=localFilePath
        temp['diskPath']=diskPath
        temp['upload_length']=upload_length
        temp['file_length']=file_length
        temp['now_dir']=self.now_dir
        self.uploadTable.tableWidget.insertRow(0)
        t = QTableWidgetItem(localFilePath)
        self.uploadTable.tableWidget.setItem(0, 0, t)
        t = QTableWidgetItem(diskPath)
        self.uploadTable.tableWidget.setItem(0, 1, t)
        t = QTableWidgetItem(uf_md5)
        self.uploadTable.tableWidget.setItem(0, 2, t)
        t = QTableWidgetItem(str(file_length))
        self.uploadTable.tableWidget.setItem(0, 3, t)

        if is_upload=='1':
            uploadOpearteBtn = QPushButton("暂停")
        else:
            uploadOpearteBtn = QPushButton("继续")
        uploadOpearteBtn.clicked.connect(self.uploadListBtnOperate)
        self.uploadTable.tableWidget.setCellWidget(0, 5, uploadOpearteBtn)
        temp['button']=uploadOpearteBtn
        # 定义水平进度条
        progressBar = QProgressBar()
        # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
        progressBar.setRange(0, 100)
        # 设置进度条的初始值
        if file_length!=0:
            progressBar.setValue(int(int(upload_length)/int(file_length)*100))
        self.uploadTable.tableWidget.setCellWidget(0, 4, progressBar)
        temp['bar']=progressBar
        self.uploadList.append(temp)
        Thread(target=user.upload, args=(temp['localFilePath'],temp['diskPath'],temp['uf_md5'],)).start()

    def upload(self):
        #先判断文件是否秒传
        localFilePath, filetype = QFileDialog.getOpenFileName(self, "选取上传文件", "./", "*.*")
        print(localFilePath)

        if(localFilePath==''):
            return

        son_file_info=self.fb.get_file_list_by_dir(self.now_dir)
        f_n=self.fb.get_file_name_by_path(localFilePath)
        for s in son_file_info:
            if f_n==s[0]:
                QMessageBox.warning(self, "提示", "当前云端目录已有该"+s[3]+"文件", QMessageBox.Yes)
                return
        res=user.is_quick_upload(localFilePath,self.now_dir)
        if res['is_exist']:
            QMessageBox.warning(self, "提示", "文件秒传成功", QMessageBox.Yes)
            self.fb.addFile(res['md5'],localFilePath,self.now_dir,res['file_length'])
            self.fileList = self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()
        else:
            db_exec(
                "insert into uploadHistory(uf_md5,upload_length,file_length,local_file_path,disk_path,is_upload) values ('{}',{},{},'{}','{}','{}')"
                .format(res['md5'], res['upload_length'], res['file_length'], localFilePath, self.now_dir,'1'))
            self.oneFileUpload(localFilePath,self.now_dir,res['md5'],res['upload_length'],res['file_length'],'1')

    def draw_finishDownLoadTable(self):
        while self.finishDownloadTable.tableWidget.rowCount() > 0:
            self.finishDownloadTable.tableWidget.removeRow(0)
        res = db_exec('select file_name,file_path,uf_md5 from historyFile where down_length=file_length')
        for r in res:
            self.finishDownloadTable.tableWidget.insertRow(0)
            for i in range(3):
                t = QTableWidgetItem(r[i])
                self.finishDownloadTable.tableWidget.setItem(0, i, t)

    def changeDownloadTable(self):
        if "完成" in self.showDownload.text():
            self.showDownload.setText('查看正在下载的文件')
            self.downloadTable.hide()
            self.finishDownloadTable.show()
        else:
            self.showDownload.setText('查看已经下载完成的文件')
            self.finishDownloadTable.hide()
            self.downloadTable.show()

    def get_index_by_md5(self,md5):
        for i in range(self.downloadTable.tableWidget.columnCount()):
            if(self.downloadTable.tableWidget.item(i,1).text()==md5):
                return i

    def upload_get_index_by_md5(self,md5):
        for i in range(self.uploadTable.tableWidget.columnCount()):
            if(self.uploadTable.tableWidget.item(i,2).text()==md5):
                return i

    def draw_downLoadTable(self):
        while self.downloadTable.tableWidget.rowCount() > 0:
            self.downloadTable.tableWidget.removeRow(0)
        res=db_exec("update historyFile set is_download='0' where down_length!=file_path")
        res=db_exec('select * from historyFile where down_length!=file_length and file_directory is null ')
        print('draw_downLoadTable',res)
        for r in res:
            sock_down_list=[]
            if r[8]=='1':#是文件夹
                print('文件夹历史下载')
                # temp={}
                # temp['uf_md5']=r[1]
                # temp['down_length']=r[2]
                # temp['file_length']=r[3]
                # temp['file_path']=r[4]
                # temp['file_name']=r[5]
                # temp['is_download']=r[6]
                print('r[9]+r[5]',r[9],r[5])
                son_file_info=self.fb.get_all_son_file_by_dir(r[9]+r[5])
                print('son_file_info',son_file_info)
                # self.fb.create_dir(son_file_info,file_path)#已经创建过了
                folder_length=0
                for son_file in son_file_info:
                    if son_file[1]!='':
                        # temp = {}
                        # temp['file_name'] = son_file[3]
                        # temp['file_path'] = file_path
                        # temp['uf_md5'] = son_file[1]
                        # temp['down_length'] = 0
                        # temp['file_length'] = son_file[4]
                        # temp['full_path'] = file_path + son_file[2] + son_file[3]
                        # ####
                        # print('full_path', temp['full_path'])
                        # ####
                        #
                        # temp['parent_dir'] = folder_md5
                        # sock_down_list.append(temp)
                        #

                        temp={}
                        temp['file_name']=son_file[3]
                        temp['file_path']=r[4]
                        temp['uf_md5']=son_file[1]
                        temp['file_length']=son_file[4]
                        temp['parent_dir']=r[1]
                        temp['full_path']=r[4] + son_file[2] + son_file[3]
                        res=db_exec('select down_length from historyFile where uf_md5="{}"'.format(temp['uf_md5']))
                        temp['down_length']=int(res[0][0])
                        print('temp_full_path:',temp['full_path'])
                        sock_down_list.append(temp)

                temp = {}
                temp['uf_md5'] = r[1]
                temp['down_length'] = r[2]
                temp['file_length'] = r[3]
                temp['file_path'] = r[4]
                temp['file_name'] = r[5]
                temp['is_download'] = '0'
                self.downloadTable.tableWidget.insertRow(0)
                t = QTableWidgetItem(r[5])
                self.downloadTable.tableWidget.setItem(0, 0, t)
                t = QTableWidgetItem(temp['uf_md5'])
                self.downloadTable.tableWidget.setItem(0, 1, t)
                t = QTableWidgetItem(str(r[3]))
                self.downloadTable.tableWidget.setItem(0, 2, t)
                downloadOpearteBtn = QPushButton("暂停")
                downloadOpearteBtn.clicked.connect(self.downloadListBtnOperate)
                self.downloadTable.tableWidget.setCellWidget(0,4,downloadOpearteBtn)
                # 定义水平进度条
                progressBar = QProgressBar()
                # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
                progressBar.setRange(0, 100)
                # 设置进度条的初始值
                progressBar.setValue(0)
                self.downloadTable.tableWidget.setCellWidget(0,3,progressBar)
                temp['bar']=progressBar
                temp['button']=downloadOpearteBtn
                print(temp)
                self.downloadList.append(temp)
                ######################
                Thread(target=user.download, args=(sock_down_list,)).start()
                ######################
                return
            else:
                temp={}
                temp['uf_md5']=r[1]
                temp['down_length']=r[2]
                temp['file_length']=r[3]
                temp['file_path']=r[4]
                temp['file_name']=r[5]
                temp['is_download']=r[6]
                temp['parent_dir']=''
                temp['full_path']=r[4]+'/'+r[5]
                self.downloadTable.tableWidget.insertRow(0)
                t = QTableWidgetItem(temp['file_name'])
                self.downloadTable.tableWidget.setItem(0, 0, t)
                t = QTableWidgetItem(temp['uf_md5'])
                self.downloadTable.tableWidget.setItem(0, 1, t)
                t = QTableWidgetItem(str(temp['file_length']))
                self.downloadTable.tableWidget.setItem(0, 2, t)
                downloadOpearteBtn = QPushButton("继续")
                downloadOpearteBtn.clicked.connect(self.downloadListBtnOperate)
                self.downloadTable.tableWidget.setCellWidget(0, 4, downloadOpearteBtn)
                # 定义水平进度条
                progressBar = QProgressBar()
                # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
                progressBar.setRange(0, 100)
                # 设置进度条的初始值
                progressBar.setValue(temp['down_length'])
                self.downloadTable.tableWidget.setCellWidget(0, 3, progressBar)
                temp['bar']=progressBar
                temp['button']=downloadOpearteBtn
                self.downloadList.append(temp)
                ######################
                Thread(target=user.download, args=(self.downloadList,)).start()
                ######################

    def go_by_line_edit(self):
        temp=self.nowDirEdit.text()
        fileList = self.fb.get_file_list_by_dir(temp)
        if len(fileList)!=0:
            self.now_dir=temp
            self.fileList=fileList
            self.draw_file_table()
        else:
            QMessageBox.warning(self, "提示", temp+"路径不存在", QMessageBox.Yes)

    def timer_operate(self):
        # print('timer downloadList :',self.downloadList)
        for i in range(len(self.downloadList)):
            res=db_exec("select down_length,file_length,is_download from historyFile where uf_md5='{}'".format(self.downloadList[i]['uf_md5']))
            # print('timer:',res)
            if int(res[0][1])!=0:
                self.downloadList[i]['bar'].setValue(int(int(res[0][0])/int(res[0][1])*100))
            if res[0][0]==res[0][1]:
                index=self.get_index_by_md5(self.downloadList[i]['uf_md5'])
                self.downloadTable.tableWidget.removeRow(index)
                self.draw_finishDownLoadTable()
                del self.downloadList[i]
            elif res[0][2]=='0':#双向绑定
                self.downloadList[i]['button'].setText("继续")

        for i in range(len(self.uploadList)):
            res = db_exec("select upload_length,file_length,is_upload from uploadHistory where uf_md5='{}'".format(
            self.uploadList[i]['uf_md5']))
            if len(res)==0:
                continue
            # print('upload res:', res)
            if int(res[0][1])!=0:
                self.uploadList[i]['bar'].setValue(int(int(res[0][0])/int(res[0][1])*100))
            if res[0][0]==res[0][1]:
                index=self.upload_get_index_by_md5(self.uploadList[i]['uf_md5'])
                self.uploadTable.tableWidget.removeRow(index)
                self.fb.addFile(self.uploadList[i]['uf_md5'], self.uploadList[i]['localFilePath'], self.uploadList[i]['now_dir'], self.uploadList[i]['file_length'])
                self.fileList = self.fb.get_file_list_by_dir(self.now_dir)
                self.draw_file_table()
                del self.uploadList[i]
            elif res[0][2]=='0':
                self.uploadList[i]['button'].setText("继续")

    def downloadListBtnOperate(self):
        button = self.sender()
        if button:
            row = self.downloadTable.tableWidget.indexAt(button.pos()).row()

            print('row:',row)
            # print(self.downloadList)
            # print(self.downloadList[len(self.downloadList)-1-row])
            md5=self.downloadTable.tableWidget.item(row,1).text()
            print('md5:',md5)
            if button.text()=='继续':
                button.setText("暂停")
                sql='update historyFile set is_download="1" where uf_md5="{}"'.format(md5)
                db_exec(sql)
            elif button.text()=='暂停':
                button.setText("继续")
                sql='update historyFile set is_download="0" where uf_md5="{}"'.format(md5)
                db_exec(sql)
            # else:
            #     button.setText("暂停")

    def downloadFile(self,fileInfo):
        print('fileIno:',fileInfo)
        file_path= QFileDialog.getExistingDirectory(None, "选取下载到的文件夹", "./")
        print('file_path:',file_path)
        if(file_path==''):#没有选择文件夹直接回去了
            return
        print(fileInfo)
        if fileInfo[2] != '文件夹':#获取要下载的文件的信息
            sql="select file_path,file_name,uf_md5,down_length,file_length from historyFile where uf_md5='{}'".format(fileInfo[4])
            # print('sql:',sql)
            res=db_exec(sql)
            print('res:',res)
        else:#获取要下载的文件夹下所有文件的信息
            son_file_info = self.fb.get_all_son_file_by_dir(self.now_dir + fileInfo[0] + '/')
            folder_md5 = self.fb.get_dir_md5(son_file_info)
            sql = "select file_path,file_name,uf_md5,down_length,file_length from historyFile where uf_md5='{}'".format(folder_md5)
            res = db_exec(sql)
        sock_down_list=[]
        # if len(res)==0:
        #     if fileInfo[2]!='文件夹':
        #         sql="insert into historyFile(uf_md5,down_length,file_length,file_path,file_name,is_download) values ('{}',0,{},'{}','{}','1')".format(fileInfo[4],fileInfo[3],file_path,fileInfo[0])
        #         print(sql)
        #         db_exec(sql)
        #     else:
        print('下载中的res:',res)
        if len(res)!=0:
            path=res[0][0]+'/'+res[0][1]
            print('path',path)
            if os.path.exists(path):
                if res[0][3]!=res[0][4]:
                    QMessageBox.warning(self, "提示", "该路径下载文件已经在下载列表中，请勿重复下载", QMessageBox.Yes)
                    return
                else:
                    if fileInfo[2]!='文件夹':
                        dst=file_path+'/'+res[0][1]
                        cp='copy {} {}'.format(path,file_path+'/'+res[0][1])
                        cp=cp.replace('/','\\')
                        os.system(cp)
                        QMessageBox.warning(self, "提示", "该文件已经下载完成过，秒下完成", QMessageBox.Yes)
                        return
                    else:
                        print(path,file_path+'/'+res[0][1])
                        shutil.copytree(path,file_path+'/'+res[0][1])
                        QMessageBox.warning(self, "提示", "该文件夹已经下载完成过，秒下完成", QMessageBox.Yes)
                        return
            else:#原本下载过但是发现文件被删除
                QMessageBox.warning(self, "提示", "原先下载的文件丢失，重新下载", QMessageBox.Yes)
                if fileInfo[2] != '文件夹':
                    print(res[0][0]+'/'+res[0][1],'原本下载过但是发现文件被删除')
                    db_exec("delete from historyFile where uf_md5='{}'".format(res[0][2]))
                    self.draw_finishDownLoadTable()
                else:
                    db_exec("delete from historyFile where uf_md5='{}' or file_directory='{}'".format(res[0][2],res[0][2]))
                    self.draw_finishDownLoadTable()
        if fileInfo[2] != '文件夹':
            if int(fileInfo[3])==0:
                QMessageBox.warning(self, "提醒", "空文件已创建成功", QMessageBox.Yes)
                f = open(file_path+"/"+fileInfo[0], 'w')
                f.close()
                return

            sql = "insert into historyFile(uf_md5,down_length,file_length,file_path,file_name,is_download) values ('{}',0,{},'{}','{}','1')".format(
                fileInfo[4], fileInfo[3], file_path, fileInfo[0])
            print(sql)
            db_exec(sql)
            temp = {}
            temp['uf_md5'] = fileInfo[4]
            temp['down_length'] = 0
            temp['file_length'] = fileInfo[3]
            temp['file_path'] = file_path
            temp['file_name'] = fileInfo[0]
            temp['full_path']=file_path+"/"+fileInfo[0]
            temp['is_download'] = '1'
            temp['parent_dir']=''
            self.downloadTable.tableWidget.insertRow(0)
            t = QTableWidgetItem(fileInfo[0])
            self.downloadTable.tableWidget.setItem(0, 0, t)
            t = QTableWidgetItem(temp['uf_md5'])
            self.downloadTable.tableWidget.setItem(0, 1, t)
            t = QTableWidgetItem(str(temp['file_length']))
            self.downloadTable.tableWidget.setItem(0, 2, t)
            downloadOpearteBtn = QPushButton("暂停")
            downloadOpearteBtn.clicked.connect(self.downloadListBtnOperate)
            self.downloadTable.tableWidget.setCellWidget(0,4,downloadOpearteBtn)
            # 定义水平进度条
            progressBar = QProgressBar()
            # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
            progressBar.setRange(0, 100)
            # 设置进度条的初始值
            progressBar.setValue(0)
            self.downloadTable.tableWidget.setCellWidget(0,3,progressBar)
            temp['bar']=progressBar
            temp['button']=downloadOpearteBtn
            self.downloadList.append(temp)

            sock_down_list.append(temp)
            ######################
            Thread(target=user.download,args=(sock_down_list,)).start()
            ######################
        else:
            print('文件夹下载')
            son_file_info = self.fb.get_all_son_file_by_dir(self.now_dir + fileInfo[0] + '/')
            print('son_file_info', son_file_info)
            folder_md5 = self.fb.get_dir_md5(son_file_info)
            print('folder md5', folder_md5)
            self.fb.create_dir(son_file_info, file_path)  # 为了方便调试暂时注释掉
            if len(son_file_info)==0:
                if not os.path.exists(file_path+'/'+fileInfo[0]):
                    os.mkdir(file_path+'/'+fileInfo[0])
                QMessageBox.warning(self, "提醒", "文件夹已创建成功，无文件可下载", QMessageBox.Yes)
                return
            folder_length = 0
            for son_file in son_file_info:
                if son_file[1] != '':
                    temp = {}
                    temp['file_name'] = son_file[3]
                    temp['file_path'] = file_path
                    temp['uf_md5'] = son_file[1]
                    temp['down_length'] = 0
                    temp['file_length']=son_file[4]
                    temp['full_path']=file_path+son_file[2]+son_file[3]
                    ####
                    print('full_path',temp['full_path'])
                    ####

                    temp['parent_dir'] = folder_md5
                    sock_down_list.append(temp)
                    folder_length += son_file[4]
                    sql = "insert into historyFile(uf_md5,down_length,file_length,file_path,file_name,is_download,file_directory,user_path) values ('{}',{},{},'{}','{}','{}','{}','{}')" \
                        .format(son_file[1], 0, son_file[4], file_path, son_file[3], '1', folder_md5, self.now_dir)
                    print(sql)
                    db_exec(sql)
            sql = "insert into historyFile(uf_md5,down_length,file_length,file_path,file_name,is_download,is_folder,user_path) values ('{}',{},{},'{}','{}','{}',{},'{}')".format(
                folder_md5, 0, folder_length, file_path, fileInfo[0], '1', '1', self.now_dir)
            db_exec(sql)
            temp = {}
            temp['uf_md5'] = folder_md5
            temp['down_length'] = '0'
            temp['file_length'] = folder_length
            temp['file_path'] = file_path
            temp['file_name'] = fileInfo[0]
            temp['is_download'] = '1'
            self.downloadTable.tableWidget.insertRow(0)
            t = QTableWidgetItem(fileInfo[0])
            self.downloadTable.tableWidget.setItem(0, 0, t)
            t = QTableWidgetItem(temp['uf_md5'])
            self.downloadTable.tableWidget.setItem(0, 1, t)
            t = QTableWidgetItem(str(temp['file_length']))
            self.downloadTable.tableWidget.setItem(0, 2, t)
            downloadOpearteBtn = QPushButton("暂停")
            downloadOpearteBtn.clicked.connect(self.downloadListBtnOperate)
            self.downloadTable.tableWidget.setCellWidget(0, 4, downloadOpearteBtn)
            # 定义水平进度条
            progressBar = QProgressBar()
            # 设置进度条的范围，参数1为最小值，参数2为最大值（可以调得更大，比如1000
            progressBar.setRange(0, 100)
            # 设置进度条的初始值
            progressBar.setValue(0)
            self.downloadTable.tableWidget.setCellWidget(0, 3, progressBar)
            temp['bar'] = progressBar
            temp['button'] = downloadOpearteBtn
            print(temp)
            self.downloadList.append(temp)
            ######################
            Thread(target=user.download, args=(sock_down_list,)).start()
            ######################
            return

    def file_system_download_button_click(self):
        button = self.sender()
        if button:
            row = self.fileTable.tableWidget.indexAt(button.pos()).row()
            # print(self.fileList[len(self.fileList)-1-row])
            if self.now_dir=='/':
                self.downloadFile(self.fileList[len(self.fileList)-1-row])
            else:
                self.downloadFile(self.fileList[len(self.fileList) - row])
    # def get_file_info_by_row(self,row):
    #     for i in range(len(self.allFileList)):
    #
    def file_system_del_button_click(self):
        button = self.sender()
        if button:
            row = self.fileTable.tableWidget.indexAt(button.pos()).row()
            file_name=self.fileTable.tableWidget.item(row,0).text()
            file_type=self.fileTable.tableWidget.item(row,2).text()
            print('file_name:',file_name)
            print('del:',self.now_dir+file_name)
            delFileList={'file':[],'folder':[]}
            if file_type=='文件夹':
                print('文件夹删除')
                res=db_exec("select uf_path,uf_file_name from userFile where uf_path like '{}%' and uf_file_type='文件夹'".format(self.now_dir+file_name+'/'))
                print(res)
                for r in res:
                    delFileList['folder'].append(r[0]+r[1]+'/')
                delFileList['folder'].append(self.now_dir+file_name+"/")
                res = db_exec(
                    "select uf_path,uf_file_name from userFile where uf_path like '{}%' and uf_file_type!='文件夹'".format(
                        self.now_dir + file_name + '/'))
                for r in res:
                    delFileList['file'].append(r[0]+r[1])
                if user.delete(delFileList):
                    db_exec("delete from userFile where (uf_path='{}' and uf_file_name='{}' and uf_file_type='文件夹') or uf_path like'{}%'"
                            .format(self.now_dir,file_name,self.now_dir+file_name+'/'))
            else:
                delFileList['file'].append(self.now_dir+file_name)
                if user.delete(delFileList):
                    db_exec("delete from userFile where uf_path='{}' and uf_file_name='{}'"
                            .format(self.now_dir,file_name))
            print('delFileList:',delFileList)
            self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()

    def file_system_copy_button_click(self):
        button = self.sender()
        if button:
            row = self.fileTable.tableWidget.indexAt(button.pos()).row()
            file_name=self.fileTable.tableWidget.item(row,0).text()
            file_type=self.fileTable.tableWidget.item(row,2).text()
            self.clipboard['uf_path']=self.now_dir
            self.clipboard['uf_file_name']=file_name
            self.clipboard['uf_file_type']=file_type
            self.clipboard['operate']="copy"
            print(self.clipboard)

    def file_system_cut_button_click(self):
        button = self.sender()
        if button:
            row = self.fileTable.tableWidget.indexAt(button.pos()).row()
            file_name=self.fileTable.tableWidget.item(row,0).text()
            file_type=self.fileTable.tableWidget.item(row,2).text()
            self.clipboard['uf_path']=self.now_dir
            self.clipboard['uf_file_name']=file_name
            self.clipboard['uf_file_type']=file_type
            self.clipboard['operate']="cut"
            print(self.clipboard)

    # def file_system_reName_button_click(self):
    #     button = self.sender()
    #     if button:
    #         row = self.fileTable.tableWidget.indexAt(button.pos()).row()
    #         # file_name=self.fileTable.tableWidget.item(row,0).text()
    #         print(row)
    #         file_name=self.fileTable.tableWidget.item(row,0).text()
    #         fullName=self.now_dir+file_name
    #         print(fullName)
    #         text, ok = QInputDialog.getText(self, '重命名', '新名字：')
    #         if ok and text:
    #             for i in self.fileList:
    #                 if i[0]==text:
    #                     QMessageBox.warning(self, "提醒", "与当前目录下的文件重名", QMessageBox.Yes)
    #                     return
    #             print('new fullname:',self.now_dir+text)
    #             item={}
    #             item['old_uf_path']=fullName
    #             item['new_uf_path']=self.now_dir+text
    #
    #             if user.cut([item]):
    #                 if '.' in text:
    #                     f_name=text.split('.')[0]
    #                     f_type = text[len(f_name):]
    #                 db_exec('update userFile set uf_file_name="{}" and uf_file_type="{}" where uf_path="{}" and uf_file_name="{}"'
    #                         .format(f_name,f_type,self.now_dir,file_name))
    #             self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
    #             self.draw_file_table()
    # def file_system_reName_button_click(self):
    #     button = self.sender()
    #     if button:
    #         row = self.fileTable.tableWidget.indexAt(button.pos()).row()
    #         # file_name=self.fileTable.tableWidget.item(row,0).text()
    #         print(row)
    #         file_name=self.fileTable.tableWidget.item(row,0).text()
    #         fullName=self.now_dir+file_name
    #         print(fullName)
    #         text, ok = QInputDialog.getText(self, '重命名', '新名字：')
    #         if ok and text:
    #             for i in self.fileList:
    #                 if i[0]==text:
    #                     QMessageBox.warning(self, "提醒", "与当前目录下的文件重名", QMessageBox.Yes)
    #                     return
    #             print('new fullname:',self.now_dir+text)
    #             item={}
    #             item['old_uf_path']=fullName
    #             item['new_uf_path']=self.now_dir+text
    #             if user.cut([item]):
    #                 db_exec('update userFile set uf_file_name="{}" , uf_file_type="{}" where uf_path="{}" and uf_file_name="{}"'
    #                         .format(text.split('.')[0],text.split('.')[1],self.now_dir,file_name))
    #             self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
    #             self.draw_file_table()
    def file_system_reName_button_click(self):
        button = self.sender()
        if button:
            row = self.fileTable.tableWidget.indexAt(button.pos()).row()
            # file_name=self.fileTable.tableWidget.item(row,0).text()
            print(row)
            file_name=self.fileTable.tableWidget.item(row,0).text()
            fullName=self.now_dir+file_name
            print(fullName)
            text, ok = QInputDialog.getText(self, '重命名', '新名字：')
            if ok and text:
                for i in self.fileList:
                    print("重名：",i[0],text)
                    if i[0]==text:
                        QMessageBox.warning(self, "提醒", "与当前目录下的文件重名", QMessageBox.Yes)
                        return
                print('new fullname:',self.now_dir+text)
                item={}
                item['old_uf_path']=fullName
                item['new_uf_path']=self.now_dir+text
                f_name=''
                f_type=''
                if user.cut([item]):
                    if '.' in text:
                        f_name=text.split('.')[0]
                        f_type = text[len(f_name)+1:]
                    db_exec('update userFile set uf_file_name="{}" , uf_file_type="{}" where uf_path="{}" and uf_file_name="{}"'
                            .format(text,f_type,self.now_dir,file_name))
                    print('rename:',(text,f_type,self.now_dir,file_name))
                self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
                self.draw_file_table()

    def draw_file_table(self):
        self.allFileList=[]
        self.nowDirEdit.setText(self.now_dir)
        while self.fileTable.tableWidget.rowCount() > 0:
            self.fileTable.tableWidget.removeRow(0)
        for i in self.fileList:
            temp={}
            temp['file_name']=i[0]
            temp['uf_md5']=i[4]
            self.fileTable.tableWidget.insertRow(0)
            for j in range(4):
                t = QTableWidgetItem(str(i[j]))
                self.fileTable.tableWidget.setItem(0, j, t)
            downloadBtn = QPushButton("下载")
            downloadBtn.clicked.connect(self.file_system_download_button_click)
            temp['downloadBtn']=downloadBtn
            # downloadBtn.setStyleSheet("QPushButton{margin:6px};")
            self.fileTable.tableWidget.setCellWidget(0,4,downloadBtn)
            copyBtn=QPushButton("复制")
            copyBtn.clicked.connect(self.file_system_copy_button_click)
            temp['copyBtn']=copyBtn
            self.fileTable.tableWidget.setCellWidget(0,5,copyBtn)
            cutBtn=QPushButton("剪切")
            cutBtn.clicked.connect(self.file_system_cut_button_click)
            temp['cutBtn']=cutBtn
            self.fileTable.tableWidget.setCellWidget(0,6,cutBtn)

            delBtn=QPushButton("删除")
            delBtn.clicked.connect(self.file_system_del_button_click)
            temp['delBtn']=delBtn
            self.fileTable.tableWidget.setCellWidget(0,7,delBtn)

            reNameBtn=QPushButton("重命名")
            reNameBtn.clicked.connect(self.file_system_reName_button_click)
            temp['reNameBtn']=reNameBtn
            self.fileTable.tableWidget.setCellWidget(0,8,reNameBtn)
            self.allFileList.append(temp)

        if self.now_dir!='/':
            self.fileTable.tableWidget.insertRow(0)
            t = QTableWidgetItem('..')
            self.fileTable.tableWidget.setItem(0, 0, t)

    def go_dir_by_click(self):
        if(self.fileTable.tableWidget.selectedItems()[0].text()=='..'):
            self.now_dir=self.fb.get_parent_dir(self.now_dir)
            self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()
            return
        elif self.fileTable.tableWidget.selectedItems()[2].text()!='文件夹':
            return
        else:
            self.now_dir=self.now_dir+self.fileTable.tableWidget.selectedItems()[0].text()+'/'
            self.fileList=self.fb.get_file_list_by_dir(self.now_dir)
            self.draw_file_table()

class fileTable(QWidget,ui_fileTable):
    def __init__(self):
        super(fileTable, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("网盘")

class downloadTable(QWidget,ui_downloadTable):
    def __init__(self):
        super(downloadTable, self).__init__()
        self.setupUi(self)

# def test():
#     fb=fileDb()
#     fb.printName()
#     fb.setName(4444)
#     fb.printName()
#下载0字节、重命名、文件夹上传
if __name__ == '__main__':
    app = QApplication(sys.argv)
    loginW=loginWindow()
    # loginW=mainWindow(open('files/loacl_files.json').read(),'')
    loginW.show()
    sys.exit(app.exec_())
    # print(get_file_md5(r'D:\PyCharm\testwebDisk\files\1.txt'))
    # test()