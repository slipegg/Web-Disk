//±‡“Î∑Ω∑®: g++ file_md5.cpp  --std=c++11 -lcrypto
 
#include <fstream>
#include <openssl/md5.h>
#include <string>
#include <string.h>
using namespace std;
using std::string;
 
// string salt="huahuadan";
// int get_file_md5(const std::string &file_name, std::string &md5_value)
// {
//     md5_value.clear();
 
//     std::ifstream file(file_name.c_str(), std::ifstream::binary);
//     if (!file)
//     {
//         return -1;
//     }
 
//     MD5_CTX md5Context;
//     MD5_Init(&md5Context);
 
//     char buf[1024 * 16];
//     while (file.good()) {
//         file.read(buf, sizeof(buf));
//         MD5_Update(&md5Context, buf, file.gcount());
//     }
 
//     unsigned char result[MD5_DIGEST_LENGTH];
//     MD5_Final(result, &md5Context);
 
//     char hex[35];
//     memset(hex, 0, sizeof(hex));
//     for (int i = 0; i < MD5_DIGEST_LENGTH; ++i)
//     {
//         sprintf(hex + i * 2, "%02x", result[i]);
//     }
//     hex[32] = '\0';
//     md5_value = string(hex);
 
//     return 0;
// }


void get_char_md5(string content,unsigned char* p)
{
    unsigned char md5[32];
    MD5_CTX md5Context;
    MD5_Init(&md5Context);
    MD5_Update(&md5Context, content.data(), content.length());
    MD5_Final(md5,&md5Context);
    for (size_t i = 0; i < MD5_DIGEST_LENGTH; ++i) {
        // std::cout << int(md5[i]) << " ";
        p[i]=md5[i];
    }
}


// string get_token(string name)
// {
//     string temp=name+salt;
//     string md5=get_hex_md5(temp);
//     // cout<<"md5:"<<md5<<endl;
//     temp=name+md5;
//     string token=base64_encode((const unsigned char*)temp.data(),temp.length());
//     return token;
// }

// bool veri_token(string token,string& name)
// {
//     string temp=base64_decode(token);
//     string md5=temp.substr(temp.length()-32);
//     string tname=temp.substr(0,temp.length()-32);
//     // cout<<md5<<endl;
//     // cout<<tname<<endl;
//     if(get_hex_md5(tname+salt)==md5)
//     {
//         name=tname;
//         return true;
//     }
//     else{
//         return false;
//     }
// }

// int main(int argc, char* argv[])
// {
//     string name;
//     string token=get_token("¡ıºŒŒƒ");
//     cout<<"token:"<<token<<endl;
//     cout<<veri_token(token,name)<<endl<<"name:"<<name<<endl;
// }