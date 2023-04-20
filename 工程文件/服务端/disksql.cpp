// #include <iostream>	// cin,cout??
// #include <mysql.h>	// mysql????
// #include <string.h>
// #include <vector>
// #include <string>
// #include <algorithm>
// #include <openssl/md5.h>
// #include "base64.h"
// #include "configor/json.hpp"
// using namespace configor;
// using std::vector;
// using namespace std;

// #define SQLIP "localhost"
// #define SQLPORT 3036
// #define SQLUSER "root"
// #define SQLPASSWD "root123"
// #define SQLDB "pan"
// #define SALT "huahuadan"

#include "./include/disksql.h"
#include "./include/util.h"

string get_hex_md5(string content)
{
    unsigned char md5[32];
    MD5_CTX md5Context;
    // cout<< typeid(md5Context).name()<<endl;
    MD5_Init(&md5Context);
    MD5_Update(&md5Context, content.data(), content.length());
    MD5_Final(md5,&md5Context);
    string md5_hex;
    const char map[] = "0123456789abcdef";
    for (size_t i = 0; i < MD5_DIGEST_LENGTH; ++i) {
        // std::cout << int(md5[i]) << " ";
        md5_hex += map[md5[i] / 16];
        md5_hex += map[md5[i] % 16];
    }
    return md5_hex;
}

// class Sql{
//    public:
//       int exec(string s,bool is_mul=0);//??????????????0?????????,is_mul???????????§Ø?????
//       int exec_out(string s,vector<vector<string>>& res,int& rows,int& cols);//??????????????res??
// } sql;
Sql sql;

int Sql::exec(string s,bool is_mul){
   MYSQL     *mysql;   
   MYSQL_RES *mresult;   
   MYSQL_ROW  mrow;
   if ((mysql = mysql_init(NULL))==NULL) 
   {
    	cout << "mysql_init failed" << endl;
      return -1;
   }
   if (mysql_real_connect(mysql,SQLIP,SQLUSER, SQLPASSWD,SQLDB,SQLPORT, NULL, 0)==NULL) 
   {
      cout << "mysql_real_connect failed(" << mysql_error(mysql) << ")" << endl;
      return -1;
   }
   mysql_set_character_set(mysql, "gbk");    
   if(is_mul)
   {
      mysql_set_server_option(mysql,MYSQL_OPTION_MULTI_STATEMENTS_ON);
   }
   if (mysql_query(mysql, s.c_str())) 
   {
      cout << "mysql_query failed(" << mysql_error(mysql) << ")" << endl;
      return -1;
   }

   if ((mresult = mysql_store_result(mysql))==NULL) 
   {
      // cout << "mysql_store_result failed" << endl;
      return 0;
   }
   
   int r=(int)mysql_num_rows(mresult);
   
   mysql_free_result(mresult);  
   mysql_close(mysql);  
   return r;
}

int Sql::exec_out(string s,vector<vector<string>>& res,int& rows,int& cols)
{
   MYSQL     *mysql;   
   MYSQL_RES *result;   
   MYSQL_ROW  row;

   if ((mysql = mysql_init(NULL))==NULL) 
   {
    	cout << "mysql_init failed" << endl;
      return -1;
   }
   if (mysql_real_connect(mysql,SQLIP,SQLUSER, SQLPASSWD,SQLDB,SQLPORT, NULL, 0)==NULL) 
   {
      cout << "mysql_real_connect failed(" << mysql_error(mysql) << ")" << endl;
      return -1;
   }
   mysql_set_character_set(mysql, "gbk");    

   if (mysql_query(mysql, s.c_str())) 
   {
      cout << "mysql_query failed(" << mysql_error(mysql) << ")" << endl;
      return -1;
   }

   if ((result = mysql_store_result(mysql))==NULL) 
   {
      cout << "mysql_store_result failed" << endl;
      return -1;
   }
   
   // vector<vector<string> > res;
   int r=(int)mysql_num_rows(result);
   rows=0;
   cols=mysql_num_fields(result);
   // cout<<"cols"<<cols<<endl;
   while((row=mysql_fetch_row(result))!=NULL) {
      res.push_back(vector<string>());
      unsigned long *lengths;
      lengths = mysql_fetch_lengths(result);
      for(int i=0;i<cols;i++)
      {
         if((int) lengths[i]!=0)
         {
             res[rows].push_back(row[i]);
         }
         else{
            res[rows].push_back("");
         }
      }
      rows++;
   }

   mysql_free_result(result);  
   mysql_close(mysql);  
   return r;
}


int User::create_table(){
   string sql_query="drop table if exists user;"
      "create table user ("
      "user_id int unsigned auto_increment,"
      "user_name char(50) not null,"
      "user_password char(32) not null,"
      "user_email char(50),"
      "user_sex char(2) not null default '??',"
      "user_level char(1) not null default '0',"
      "user_enable char(1) not null default '1',"
      "primary key(user_id)"
      ") ENGINE=InnoDB CHARSET=gbk;";
   return sql.exec(sql_query,1);
}

string User::get_id_by_token(string token)
{
    string temp=base64_decode(token);
    string md5=temp.substr(temp.length()-32);
    string tid=temp.substr(0,temp.length()-32);
    // cout<<md5<<endl;
    // cout<<tname<<endl;
    if(get_hex_md5(tid+SALT)==md5)
    {
      return tid;
    }
    else{
        return "-1";
    }
}

string User::get_token(string id)
{
   string temp=id+SALT;
   string md5=get_hex_md5(temp);
   // cout<<"md5:"<<md5<<endl;
   temp=id+md5;
   string token=base64_encode((const unsigned char*)temp.data(),temp.length());
   return token;
}

int User::login(string name,string passwd,string& id,string& token)
{
   int res;
   vector<vector<string>> result;
   int rows,cols;
   cout<<"name:"<<name<<"passwd:"<<passwd<<endl;
   res=sql.exec_out("select user_id from user where user_name='"+name+"' and user_password=MD5('"+passwd+"') limit 1",result,rows,cols);
   
   if(res==-1)
   {
      return -1;
   }
   else if(res==0)
   {
      res=sql.exec("select * from user where user_name='"+name+"' limit 1");
      if(res==1)//???????????????
      {
         return 1;
      }
      else{//???????????
         return 2;
      }
   }
   else{//??????
      // cout<<"result:"<<result[0][0]<<endl;
      id=result[0][0];
      token=get_token(result[0][0]);
      // cout<<token;
      return 0;
   }
}

int User::is_name_exist(string user_name)
{
   return sql.exec("select * from user where user_name='"+user_name+"'");
}

int User::user_register(string name,string passwd){
   int flag;
   cout<<"name:"<<name<<"passwd:"<<passwd<<endl;
   if((flag=is_name_exist(name))==-1){//????
      return -1;
   }
   else if(flag==1)//name????
   {
      return 1;
   }
   else{//???
      string sql_query="insert user(user_name,user_password) values('"+name+"',MD5('"+passwd+"'))";
      if(sql.exec(sql_query)==-1)
      {
         return -1;
      }
      return 0;
   }
}

// class RealFile{
//    // private:
//    //    Sql sql;
//    // protected:
//    public:
//       int create_table();//??????????????????????????????md5???0?????????????
//       int is_file_exist(string rf_md5);//??md5????????????????????1???????????0??????????-1
//       int add_file(string rf_md5,unsigned long long rf_length);//???????????????????????rf_links+1??????????????-1??????????????0???????
//       int del_file(string rf_md5);//???????rf_links?????§³???0??????????????-1??????????????0???????
//       int clear_file();//?????????????0???????????md5=0?????????????-1???????,????0??????
// };

int RealFile::create_table()
{
   string sql_query="drop table if exists realFile;"
      "create table realFile ("
      "rf_md5 char(32) not null,"
      "rf_length bigint unsigned not null,"
      "rf_links int unsigned not null default 1,"
      "primary key(rf_md5),"
      "unique key rf_md5(rf_md5) using btree"
      ") ENGINE=InnoDB CHARSET=gbk;"
      "insert into realFile(rf_md5,rf_length,rf_links) values('0',0,0);";
   cout<<sql_query<<endl;
   return sql.exec(sql_query,1);
}

int RealFile::is_file_exist(string rf_md5)
{
   string sql_query="select * from realFile where rf_md5='"+rf_md5+"'";
   return sql.exec(sql_query);
}

int RealFile::add_file(string rf_md5,unsigned long long rf_length)
{
   string s_rf_length=to_string(rf_length);
   string sql_query="insert into realFile(rf_md5,rf_length) values('"+rf_md5+"',"+s_rf_length+") on duplicate key update rf_links=rf_links+1";
   // cout<<sql_query<<endl;
   return sql.exec(sql_query);
}

int RealFile::del_file(string rf_md5)
{
   string sql_query="update realFile set rf_links=if(rf_links<1,0,rf_links-1) where rf_md5='"+rf_md5+"'";
   // cout<<sql_query<<endl;
   return sql.exec(sql_query);
}

int RealFile::clear_file()
{
   string sql_query="delete from realFile where rf_links=0 and rf_md5!='0'";
   return sql.exec(sql_query);
}

// class UserFile:public RealFile{
//    private:
//       string s_user_id;
//    public:
//       UserFile(int user_id);
//       string get_file_tree();//????????
//       int create_table();//????0???????
//       int add_file(string rf_md5,string uf_path,unsigned long long rf_length);//user????????????????????????§µ?????0???????
//       int add_folder(string uf_path);//?????????
//       string get_file_md5(string uf_path);//????¡¤??????????md5??
//       int del_file(string uf_path);//????¡¤????????/?????
//       int mv_file(string old_uf_path,string new_uf_path);//?????/??????????????¡¤??
//       int cp_file(string old_uf_path,string new_uf_path);//?????/????§Ú????????¡¤??
// };
UserFile::UserFile(int user_id){
   s_user_id=to_string(user_id);
}
int UserFile::create_table()
{
   string sql_query="drop table if exists userFile;"
      "create table userFile ("
      "uf_id int unsigned not null auto_increment,"
      "user_id int unsigned not null,"
      "rf_md5 char(32),"
      "uf_path varchar(1000) not null,"
      "uf_up_time datetime not null default current_timestamp,"
      "uf_is_folder char(1) not null default '0',"
      "primary key(uf_id),"
      "foreign key(user_id) references user(user_id),"
      "foreign key(rf_md5) references realFile(rf_md5),"
      "constraint unique_user_path Unique(user_id, uf_path)"
      ") ENGINE=InnoDB CHARSET=gbk;";
   cout<<sql_query<<endl;
   return sql.exec(sql_query,1);   
}

int UserFile::add_file(string rf_md5,string uf_path,unsigned long long rf_length)
{
   if(RealFile::add_file(rf_md5,rf_length)==-1)
   {
      return -1;
   }
   string sql_query="insert into userFile(user_id,rf_md5,uf_path) values("+s_user_id+",'"+rf_md5+"','"+uf_path+"')";
   cout<<sql_query<<endl;
   return sql.exec(sql_query);  
}

int UserFile::add_folder(string uf_path)
{
   string sql_query="insert into userFile(user_id,uf_path,uf_is_folder) values("+s_user_id+",'"+uf_path+"','1')";
   cout<<sql_query<<endl;
   return sql.exec(sql_query); 
}

string UserFile::get_file_md5(string uf_path)
{
   string sql_query="select rf_md5 from userFile where user_id="+s_user_id+" and uf_path='"+uf_path+"' and uf_is_folder='0'";
   cout<<sql_query<<endl;

   vector<vector<string>> res;
   int rows,cols;
   int r=sql.exec_out(sql_query,res,rows,cols);
   if(r==0)
   {
      return "-1";
   }
   else
   {
      return res[0][0];
   }
}

int UserFile::del_file(string uf_path)
{
   string md5=get_file_md5(uf_path);
   if(md5!="-1")
   {
      RealFile::del_file(md5);
      string sql_query="delete from userFile where user_id="+s_user_id+" and uf_path='"+uf_path+"'";
      cout<<sql_query<<endl;
      return sql.exec(sql_query);  
   }
   else
   {
      return -1;
   }
}

int UserFile::mv_file(string old_uf_path,string new_uf_path)
{
   string sql_query="update userFile set uf_path='"+new_uf_path+"' where user_id="+s_user_id+" and uf_path='"+old_uf_path+"'";
   cout<<sql_query<<endl;
   return sql.exec(sql_query); 
}

int UserFile::cp_file(string old_uf_path,string new_uf_path)
{
   string sql_query="insert into userFile(user_id,rf_md5,uf_path,uf_is_folder) select user_id,rf_md5,'"+new_uf_path+"',uf_is_folder from userFile where user_id="+s_user_id+" and uf_path='"+old_uf_path+"' limit 1";
   cout<<sql_query<<endl;
   return sql.exec(sql_query); 
}

string UserFile::get_file_tree()
{
   string sql_query="select uf_path,userFile.rf_md5,realFile.rf_length,uf_up_time from userFile left join realFile on userFile.rf_md5=realFile.rf_md5  where user_id="+s_user_id;
   cout<<sql_query<<endl;
   vector<vector<string>> res;
   int rows,cols;
   int r=sql.exec_out(sql_query,res,rows,cols);
   json j;
   for(int i=0;i<rows;i++)
   {
      string utf8;
      Gbk2utf8(utf8,res[i][0]);
      j[i]["full_path"]=utf8;
      j[i]["MD5"]=res[i][1];
      j[i]["length"]=res[i][2];
      j[i]["up_time"]=res[i][3];
   }
   cout<<"result: "<< j.dump()<<endl;
   return j.dump();
}

 int UserFile::del_folder(string uf_path)
 {
   string sql_query="delete from userFile where user_id="+s_user_id+" and uf_path='"+uf_path+"'";
   int r=sql.exec(sql_query);
   return r;
 }

// int main(int argc, char* argv[])
// {
//    User user;
//    string id;
//    string token;
//    user.login("a","1",id,token);
//    cout<<token<<endl;
//    UserFile uf(1);
//    cout<<uf.get_file_tree();
//    // cout<<user.create_table();
//    // cout<<user.user_register("a","1")<<endl;
//    // RealFile rf;
//    // cout<<rf.create_table()<<endl;
//    // UserFile uf(1);

//    // cout<<uf.create_table()<<endl;
//    // cout<<uf.add_folder("/AF/");
//    // cout<<uf.add_folder("/BF/");
//    // cout<<uf.add_folder("/CF/");
//    // cout<<uf.add_folder("/AAF/");
//    // cout<<uf.add_folder("/ABF/");
//    // cout<<uf.add_folder("/BAF/");
//    // cout<<uf.add_file("6e328b973bc318775754741e47c88f91","/1.txt",3000000)<<endl;
//    // cout<<uf.add_file("86e91067996a31f3d80736ef0ff61a72","/2.txt",10000000)<<endl;
//    // cout<<uf.add_file("915487de76d4b2ef9ec35722fa3993d4","/AF/A1.txt",1000000)<<endl;
//    // cout<<uf.add_file("cd77828b1d070f25be23d10b6ab36940","/AF/A2.txt",1000000)<<endl;
//    // cout<<uf.add_file("d7c4876e26476b246bc15075b318258d","/AF/AAF/AA1.txt",10000000)<<endl;
//    // cout<<uf.add_file("f0af18af2671801044ce2817163f099f","/BF/B1.txt",10000000)<<endl;

//    // string token;
//    // cout<<user.login("abc","1",token)<<endl;
//    // cout<<user.get_id_by_token(token)<<endl;
//    // cout<<user.login("abc","2")<<endl;
//    // cout<<user.login("abcd","2")<<endl;
//    // RealFile rf;
//    // cout<<rf.create_table();
//    // cout<<rf.add_file("3728adef213",133333)<<endl;
//    // cout<<rf.add_file("3728adef213",133333)<<endl;
//    // cout<<rf.add_file("3728adef213",133333)<<endl;
//    // cout<<rf.add_file("9876812aed",787229)<<endl;
//    // cout<<rf.del_file("3728adef213")<<endl;
//    // cout<<rf.clear_file()<<endl;
//    // cout<<rf.is_file_exist("3728adef213")<<endl;
//    // UserFile uf(1);
//    // cout<<uf.RealFile::create_table();
//    // cout<<uf.create_table();
//    // cout<<uf.add_file("0","/000.txt",0);
//    // cout<<uf.add_file("3728adef213","/a.txt",1314);
//    // cout<<uf.add_folder("/test/");
//    // cout<<uf.get_file_md5("/a.txt")<<endl;
//    // cout<<uf.get_file_md5("/0.txt")<<endl;
//    // cout<<uf.del_file("/a.txt")<<endl;
//    // cout<<uf.get_file_md5("/test/")<<endl;
//    // cout<<uf.mv_file("/c.txt","/test/bb.txt")<<endl;
//    // cout<<uf.cp_file("/test/","/attt/")<<endl;
//    // cout<<uf.get_file_tree()<<endl;
//    return 0;
// }
/*

/000.txt
/test/
/test/bb.txt
/attt/

*/