#include <mutex>
#include <vector>
#include <sstream>
#include <string>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <tuple>
#include "./include/config.h"
#include "./include/util.h"

recursive_mutex mtx;

ofstream log_file("./web_disk.log", ios::app);

string getNowTime()
{
    timeval tv;
    char buf[64];
    gettimeofday(&tv, NULL);
    strftime(buf, sizeof(buf) - 1, "%Y-%m-%d %H:%M:%S", localtime(&tv.tv_sec));
    return string(buf);
}

void writeLog()
{
    log_file << endl;
}

vector<string> split(const string &s, const char seperator)
{

    stringstream ss(s);
    string item;
    vector<string> v;

    while (getline(ss, item, seperator))
    {
        v.push_back(item);
    }
    return v;
}

tuple<string, int> getPeerIPWithPort(int fd)
{
    struct sockaddr_in addr;
    socklen_t len = sizeof(addr);
    tuple<string, int> info;
    if (getpeername(fd, (struct sockaddr *)&addr, &len) != -1)
    {
        info = make_tuple(string(inet_ntoa(addr.sin_addr)), ntohs(addr.sin_port));
    }
    return info;
}
bool Gbk2utf8(string &utfStr, string &srcStr)
{
 
    //�����Ƚ�gbk����ת��Ϊunicode����   
    if(NULL==setlocale(LC_ALL,"zh_CN.gbk"))//����ת��Ϊunicodeǰ����,��ǰΪgbk����   
    {
        printf("Bad Parameter\n");
        return false;
    }
 
    int unicodeLen=mbstowcs(NULL,srcStr.c_str(),0);//����ת����ĳ���   
    if(unicodeLen<=0)
    {
        printf("Can not Transfer!!!\n");
        return false;
    }
    wchar_t *unicodeStr=(wchar_t *)calloc(sizeof(wchar_t),unicodeLen+1);
    mbstowcs(unicodeStr,srcStr.c_str(),srcStr.size());//��gbkת��Ϊunicode   
 
    //��unicode����ת��Ϊutf8����   
    if(NULL==setlocale(LC_ALL,"zh_CN.utf8"))//����unicodeת�������,��ǰΪutf8   
    {
        printf("Bad Parameter\n");
        return false;
    }
    int utfLen=wcstombs(NULL,unicodeStr,0);//����ת����ĳ���   
    if(utfLen<=0)
    {
        printf("Can not Transfer!!!\n");
        return false;
    }
    char utfbuf[utfLen];
    wcstombs(utfbuf,unicodeStr,utfLen);
    utfbuf[utfLen]=0;//��ӽ�����   
    free(unicodeStr);
    utfStr = utfbuf;
    return true;
}