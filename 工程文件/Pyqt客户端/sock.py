import random
def sock_register(username,userpasswd):
    return True

def sock_login(username,userpasswd):
    return True

def sock_judge_upload_file_type(local_path,disk_path):
    md5=random.randint(0,1000000)
    file_length=random.randint(0,10000)
    upload_length=random.randint(0,file_length//10)
    return {"md5":str(md5),"upload_length":upload_length,"file_length":file_length,"isExist":False}

def sock_send_del_message(file_path):
    return  True

def sock_send_copy_message(copy_file_list):
    return True

def sock_send_cut_message(cut_file_list):
    return True
def sock_send_new_folder_message(new_file):
    return True