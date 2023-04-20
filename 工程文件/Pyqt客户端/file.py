import json
import sqlite3
import numpy as np
import os
import hashlib
from time import strftime, localtime

# LOCAL_KEYS = ['full_path','MD5','length','up_time']   #本地文件存储位置，包含下载了一半的，
# REMOTE_KEYS = ['full_path','MD5']           #
# UPLOADING_KEYS = ['full_path','MD5','length']
# class FileList:
#     def __init__(self,keys):
#         self.files = []
#         self.keys = keys
#     def loadFromJson(self,files_str):
#         self.files = json.loads(files_str)
#
#     def append(self,file_new):
#         #print(file_new)
#         # check type
#         for key in self.keys:
#             if(key not in file_new):
#                 raise TypeError("【MY ERROR】file parameter wrong: ",key)
#         #check exist
#         for file in self.files:
#             if file['full_path'] == file_new['full_path']:
#                 #print("PATH: ",file['full_path'],file_new['full_path'])
#                 return False
#         self.files.append(file_new)
#         return True
#
#     def delete(self,path):
#         # cnt = 0
#         self.files = [file for file in self.files if not file['full_path'].startswith(path)]
#         #不能变遍历边remove，会改变下标
#         #[filter(lambda file:~ file['full_path'].startswith(path), self.files)]
#         # for file in self.files:
#         #     print("PATH, ",file['full_path'],path)
#         #     if file['full_path'].startswith(path):
#         #         # self.files.remove(file)
#         #         cnt += 1
#         # return cnt
#
#     #get childrens recursively
#     # return file in {} mode
#     def getChildrenR(self,dir_path):
#         results = []
#         for file in self.files:
#             if file['full_path'].startswith(dir_path):
#                 results.append(file)
#         return results
#
#     #get children files and dirs
#     # return : child_files: filename with out path
#     #           child_dirs: dir name without path
#     def getChildren(self,dir_path):
#         child_files = []
#         child_dirs = []
#         if(dir_path[-1]!='/'):
#             dir_path = dir_path+'/'
#         for file in self.files:
#             if file['full_path'].startswith(dir_path):
#                 child_path = file['full_path'][len(dir_path):]
#
#                 #child files
#                 index=child_path.find('/')
#
#                 if(index==-1):#file
#                     child_files.append(child_path)
#                 else:#dir
#                     if child_path[0:index] not in child_dirs:
#                         child_dirs.append(child_path[0:index])
#         return child_files,child_dirs
#
#     def getByPath(self,path):
#         for file in self.files:
#             if file['full_path'] == path:
#                 return file
#         return None
#
#     def getByMD5(self,md5):
#         for file in self.files:
#             if file['MD5'] == md5:
#                 return file
#         return None
dbUserName='233'
def db_exec(str):
    conn = sqlite3.connect('localFileSystem'+dbUserName+'.db')
    c = conn.cursor()
    c.execute(str)
    results = c.fetchall()
    res=[]
    for row in results:
        # print(row)
        res.append(row)
    conn.commit()
    return res
def key_function(x):
    return x[2]

class fileDb:
    def setName(self,name):
        global dbUserName
        dbUserName=name
    def printName(self):
        print("name:",dbUserName)
    def splite_path_file(self,str):
        index=-1
        if str[-1]!='/':
            for i in range(len(str)):
                if str[(len(str)-1-i)]=='/':
                    index=len(str)-1-i
                    break
            return [str[:index+1],str[index+1:]]
        else:
            for i in range(len(str)):
                if str[(len(str)-2-i)]=='/':
                    index=len(str)-2-i
                    break
            return [str[:index+1],str[index+1:-1]]
    def init_by_json_str(self,json_str):
        db_exec('drop table if exists userFile')
        sql = """create table if not exists  userFile 
        (
            uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            uf_md5 char(32),
            uf_path varchar(10000) not null,
            uf_file_name varchar(10000),
            uf_length integer,
            uf_file_type varchar(10000),
            uf_up_time datetime not null,
            constraint unique_path Unique(uf_path,uf_file_name)
        )
        """
        db_exec(sql)
        print('json_str:',json_str)
        if json_str!='null':
            fj=json.loads(json_str)
            for f in fj:
                sql="insert into userFile(uf_md5,uf_path,uf_file_name,uf_file_type,uf_length,uf_up_time) values ('{}','{}','{}','{}','{}','{}')"
                temp=self.splite_path_file(f['full_path'])

                if f['full_path'][-1]=='/':
                    ftype='文件夹'
                elif '.'in temp[1]:
                    ftype=temp[1].split('.')[1]
                else:
                    ftype=''
                s=(sql.format(f['MD5'],temp[0],temp[1],ftype,f['length'],f['up_time']))
                print(s)
                db_exec(s)
        sql = """create table if not exists uploadHistory
            (
                uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uf_md5 char(32),
                upload_length integer not null,
                file_length integer not null,
                local_file_path varchar(10000) not null,
                disk_path varchar(10000) not null,
                is_upload varchar(1)
            )
            """
        db_exec(sql)
        sql = """create table if not exists historyFile 
            (
                uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uf_md5 char(32),
                down_length integer not null,
                file_length integer not null,
                file_path varchar(10000) not null,
                file_name varchar(10000) not null,
                is_download varchar(1),
                file_directory varchar(10000),
                is_folder varchar(1),
                user_path varchar(10000)
            )
            """
        db_exec(sql)

    def get_file_name_by_path(self,dir):
        if dir=='/':
            return '/'
        # print(dir)
        index=0
        for i in range(len(dir)-2,-1,-1):
            if dir[i]=='/' or dir[i]=='\\':
                index=i
                break
        return dir[index+1:]

    def get_file_list_by_dir(self,dir):
        res=db_exec("select uf_file_name,uf_up_time,uf_file_type,uf_length,uf_md5 from userFile where uf_path='"+dir+"'")
        print('get_file_list_by_dir:',res)
        return res
    def get_parent_dir(self,dir):
        if dir=='/':
            return '/'
        # print(dir)
        index=0
        for i in range(len(dir)-2,-1,-1):
            if dir[i]=='/' or dir[i]=='\\':
                index=i
                break
        return dir[:index+1]
    def get_all_son_file_by_dir(self,dir):#文件夹类型
        sql="select * from userFile where uf_path like '{}%' order by uf_path desc".format(dir)
        res=db_exec(sql)
        return res
    def create_dir(self,file_list,save_path):
        print(file_list)
        file_list.sort(key=key_function)
        print(file_list)
        for p in file_list:
            if not os.path.exists(save_path+p[2]):
                os.mkdir(save_path+p[2])
            if p[5]=='文件夹':
                if not os.path.exists(save_path+p[2]+p[3]):
                    os.mkdir(save_path+p[2]+p[3])

    def get_dir_md5(self,file_list):
        temp=''
        for i in file_list:
            temp+=i[1]
        folder_md5=hashlib.md5(bytes(temp,encoding='utf-8')).digest().hex()
        # print(folder_md5)
        # print(len(folder_md5))
        return folder_md5

    def addFile(self,uf_md5,local_path,uf_path,uf_length):
        temp=self.splite_path_file(local_path)
        uf_file_name=temp[1]
        print(uf_file_name)
        if '.' in uf_file_name:
            uf_file_type = uf_file_name.split('.')[1]
        else:
            uf_file_type = ''

        uf_up_time=strftime('%Y-%m-%d %H:%M:%S', localtime())
        db_exec("insert into userFile(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time) values('{}','{}','{}','{}','{}','{}')"
                .format(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time))
    def change_file_mulu(self,dir,old_mulu,new_mulu):
        res=dir[len(old_mulu):]
        res=new_mulu+res
        return res
    def file_path_change_file_mulu(self,dir,old_mulu,new_mulu):
        res=dir[len(old_mulu):]
        res=new_mulu+res
        return res

    def get_all_local_files_by_folder(self,path):
        all_file = []
        for f in os.listdir(path):  # listdir返回文件中所有目录
            temp={}
            f_name = os.path.join(path, f)
            temp['file_name']=f_name
            if os.path.isdir(f_name):
                temp['is_dir']=True
                all_file.append(temp)
                res=self.get_all_local_files_by_folder(temp['file_name'])
                for r in res:
                    all_file.append(r)
            else:
                temp['is_dir']=False
                all_file.append(temp)
        return all_file
    def get_disk_path_by_local_and_dir(self,local_file_path,now_dir):
        local_parent=self.get_parent_dir(local_file_path)
        res=now_dir+local_file_path[len(local_parent):]
        return res
    # def get_disk_path_by_local_file(self,local_path,):
if __name__=="__main__":
    fb=fileDb()
    print(fb.get_all_local_files_by_folder(r'D:\PyCharm\testwebDisk\files\AF'))

def t():
    # f=open(r"D:\1.txt",'w')
    # f.close()
    # fb = fileDb()
    # print(fb.get_file_name_by_path(r'D:\PyCharm\testwebDisk\main.py'))
    # res=fb.change_file_mulu('/AF/AAF/AAA/BBB/','/','/BF/')
    # print(res)
    # db_exec("insert into userFile(uf_md5,uf_path,uf_file_name,uf_length,uf_file_type,uf_up_time) select uf_md5,'/BF/AF/',uf_file_name,uf_length,uf_file_type,uf_up_time from userFile where uf_file_name='/AF/' and uf_path='AAF' limit 1")

    db_exec('drop table if exists uploadHistory')
    sql = """create table uploadHistory
    (
        uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
        uf_md5 char(32),
        upload_length integer not null,
        file_length integer not null,
        local_file_path varchar(10000) not null,
        disk_path varchar(10000) not null,
        is_upload varchar(1)
    )
    """
    db_exec(sql)
    #
    db_exec('drop table if exists historyFile')
    sql = """create table historyFile
    (
        uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
        uf_md5 char(32),
        down_length integer not null,
        file_length integer not null,
        file_path varchar(10000) not null,
        file_name varchar(10000) not null,
        is_download varchar(1),
        file_directory varchar(10000),
        is_folder varchar(1),
        user_path varchar(10000)
    )
    """
    db_exec(sql)
    # # jstr=open('files/loacl_files.json').read()
    # print(fb.get_disk_path_by_local_and_dir(r'D:\PyCharm\testwebDisk\test.ui','/'))
    # fb.get_all_local_files_by_folder(r'D:\PyCharm\testwebDisk\testQQ')
    # fb.init_by_json_str(jstr)

    # res=fb.get_all_file_by_dir('/AF/')
    # fb.create_dir(res,r'D:\PyCharm\netDisk\test')
    # fb.get_dir_md5(res)
    # print(fb.get_parent_dir('/'))
    # print(fb.get_file_list_by_dir('/AA'))
    # res=db_exec('select  from userFile')
    # print(res)
    # path='/aa/'
    # print(fb.splite_path_file(path))
    # print(path.split('/'))
    # print(path.find('/'))
    # sql="""
    # create table if not exists userFile
    # (
    #     uf_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     uf_md5 char(32),
    #     uf_path varchar(10000) not null,
    #     uf_file_name varchar(10000),
    #     uf_up_time datetime not null
    # )
    # """
    # db_exec(sql)
    # files_str = '[{"full_path": "/", "MD5":"ldsfhesiofhsfioefhel"},\
    #     { "full_path": "/dir1/filename", "MD5":"kukyjgfdvefhel"},\
    #     { "full_path": "/dir1/dir11/a", "MD5":"kukyjgfdvefhel"}]'
    # files_str=open('files/loacl_files.json')
    #
    # localFiles = FileList(REMOTE_KEYS)
    # localFiles.loadFromJson(files_str)
    # current_files,current_dirs = localFiles.getChildren("/dir1/")
    # print("test getchildren",current_files,current_dirs)
    #
    # child_files =localFiles.getChildrenR("/dir1/dir11")
    # print("test getchildrenR",child_files)
    #
    # newF = child_files[0].copy()
    # newF['full_path']="/dir1/dir11/b"
    # ret = localFiles.append(newF)
    # child_files =localFiles.getChildrenR("/dir1")
    # print("test append",ret,child_files,"\n")
    #
    # print('\n',localFiles.files,'\n')
    #
    # cnt = localFiles.delete("/dir1/dir11")
    # print("test delete")
    # print('\n',localFiles.files,'\n')
    #
    # print("test getByMD5",localFiles.getByMD5('ldsfhesiofhsfioefhel'),'\n')
    # print("test getByMD5",localFiles.getByPath('/dir1/filename'),'\n')