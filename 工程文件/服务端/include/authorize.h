#pragma once
#include<string>

using namespace std;


struct UserInfo {
    int fd;
    string username;
    string password;
};

class Authenticator
{
public:
    int epoll_fd;
    int fd_cnt;

    Authenticator();

    ~Authenticator();

    void closeFd(UserInfo* info);

};



void login();

void registerAccount();
