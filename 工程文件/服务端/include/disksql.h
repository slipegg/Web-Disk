#include <iostream>	// cin,cout�?
#include <mysql.h>	// mysql特有
#include <string.h>
#include <vector>
#include <string>
#include <algorithm>
#include <openssl/md5.h>
#include "base64.h"
#include "../configor/json.hpp"
using namespace configor;
using std::vector;
using namespace std;

#define SQLIP "localhost"
#define SQLPORT 3036
#define SQLUSER "root"
#define SQLPASSWD "root123"
#define SQLDB "pan"
#define SALT "huahuadan"



string get_hex_md5(string content);

class Sql{
   public:
      int exec(string s,bool is_mul=0);//只记录返回的个数�?0代表无返�?,is_mul代表是否是执行多个语�?
      int exec_out(string s,vector<vector<string>>& res,int& rows,int& cols);//返回查询结果记录在res�?
};

extern Sql sql;

class User{
   //返回-1代表操作过程中有错误，失�?
   private:
      Sql sql;
      int is_name_exist(string user_name);//用户名是否已经存在，0不存在，1存在，login的时候用
      string get_token(string id);//依据id得到token
   public:
      int create_table();//创建用户表，留档用，不需要调�?,0代表成功,-1代表出错
      int login(string name,string passwd,string& id,string& token);//登陆判断�?0登陆成功,并将token记录进去�?1为用户名对，密码错，2位用户名不存�?
      int user_register(string name,string passwd);//注册�?0为注册成功，1代表已经有了这个名字，注册失�?
      string get_id_by_token(string token);//从token中得到id
};



class RealFile{
   // private:
   //    Sql sql;
   // protected:
   public:
      int create_table();//建表，留档，主要注意建立时建立了一个md5码为0的代指空文件的项
      int is_file_exist(string rf_md5);//该md5码的文件是否存在，存在返�?1，不存在返回0，出错返�?-1
      int add_file(string rf_md5,unsigned long long rf_length);//加入一个文件项，如果已经存在就rf_links+1，否则新建一个项�?-1表示出错，否则返�?0代表成功
      int del_file(string rf_md5);//这个是减去rf_links值，最小减�?0，但是不会删除项�?-1表示出错，否则返�?0代表成功
      int clear_file();//删除所以引用值为0的项，但是注意md5=0的空文件项不删除�?-1表示出错,返回0表示成功
};


class UserFile:public RealFile{
   private:
      string s_user_id;
   public:
      UserFile(int user_id);
      string get_file_tree();//得到文件�?
      int create_table();//返回0代表成功
      int add_file(string rf_md5,string uf_path,unsigned long long rf_length);//user的自己目录下加一个文件或者文件夹，返�?0代表成功
      int add_folder(string uf_path);//添加文件�?
      string get_file_md5(string uf_path);//依据路径得到文件的md5�?
      int del_file(string uf_path);//依据路径删除文件
      int del_folder(string uf_path);//依据路径删除文件�?
      int mv_file(string old_uf_path,string new_uf_path);//将文�?/文件夹移动到其他路径
      int cp_file(string old_uf_path,string new_uf_path);//将文�?/文件夹复制到其他路径
};