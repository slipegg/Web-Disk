import datetime
from get_conf import get_conf
import hashlib

config={}
def loadConfig(config_path):
    f = open(config_path, 'r', encoding='gbk')
    txt = f.read()
    global config
    config = get_conf(txt)
    

loadConfig('./files/config.txt')
# print(config)


log = open(config['local']['log_file'],mode='a')
def getNowTime():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

# 与md5sum 相同
def get_file_md5(fname):
    m = hashlib.md5()  #创建md5对象
    with open(fname,'rb') as fobj:
        while True:
            data = fobj.read(4096)
            if not data:
                break
            m.update(data) #更新md5对象
    
    return m.hexdigest()  #返回md5对象

if __name__=="__main__":
    print(get_file_md5(r'D:\PyCharm\testwebDisk\testQQ\20220626_213314.mp4'))
    print(get_file_md5(r'G:\Ev录屏\20220626_213314.mp4'))