#include <sys/epoll.h>
#include <unistd.h>
#include <errno.h>
#include <cstring>
#include <iostream>
#include <string>

#include "./include/authorize.h"
#include "./include/FDMgr.h"
#include "./include/config.h"
#include "./include/util.h"
#include "./include/disksql.h"

#include "configor/json.hpp"

using namespace std;
using namespace configor;

Authenticator::Authenticator()
{
    epoll_fd = epoll_create(epoll_size);
    if (epoll_fd < 0)
    {
        writeLog(getNowTime(), "create epoll error in download");
        exit(-1);
    }
    fd_cnt = 0;
}

Authenticator::~Authenticator()
{
    close(epoll_fd);
}

void Authenticator::closeFd(UserInfo *info)
{
    close(info->fd);
    delete info;
    fd_cnt--;
}

void login()
{
    Authenticator authenticator;
    epoll_event events[epoll_size];

    // take out all fds in each round of service
    while (fd_mgr.getFdNum() > 0)
    {
        epoll_event event;
        event.events = EPOLLIN;
        UserInfo *info = new (nothrow) UserInfo;
        info->fd = fd_mgr.popFront();
        event.data.ptr = info;
        if (epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_ADD, info->fd, &event) < 0)
        {
            writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
            authenticator.closeFd(info);
            continue;
        }
        authenticator.fd_cnt++;
    }

    // read/write sharing
    char *buffer = new (nothrow) char[buffer_size];
    while (authenticator.fd_cnt > 0)
    {
        // block service, so it won't serve fds in next round unitl
        // its service ends in this round.
        int event_num = epoll_wait(authenticator.epoll_fd, events, epoll_size, -1);
        for (int i = 0; i < event_num; i++)
        {
            memset(buffer, 0, buffer_size);
            UserInfo *info = reinterpret_cast<UserInfo *>(events[i].data.ptr);
            // get infomation about user
            if (events[i].events & EPOLLIN)
            {
                int client_fd = info->fd;
                epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_DEL, client_fd, nullptr);
                int read_len = read(client_fd, buffer, buffer_size);
                // read error
                if (read_len < 0)
                {
                    writeLog(getNowTime(), " read request error, errno:", strerror(errno));
                    authenticator.closeFd(info);
                }
                // client has closed, it means client not sending any data
                else if (read_len == 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed before authorizing");
                    authenticator.closeFd(info);
                }
                // request_type must contain '\0', but this position is occupied by request.
                else if (read_len == buffer_size)
                {
                    writeLog(getNowTime(), "client(fd:", client_fd, ") send invalid file type, it's too long");
                    authenticator.closeFd(info);
                }
                // get it
                else
                {
                    // split user information from string
                    // (username, password)
                    cout << buffer << endl;
                    vector<string> params = split(string(buffer), ' ');
                    info->username = params[0];
                    info->password = params[1];

                    epoll_event event;
                    event.events = EPOLLOUT;
                    event.data.ptr = info;
                    epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_ADD, client_fd, &event);
                }
            }
            // return result
            else
            {
                User user;
                string id("-1"), cookie("-1");
                int res = user.login(info->username, info->password, id, cookie);
                json j;
                j["ack"] = 1;
                j["res"] = res;
                writeLog(getNowTime(), " login status:", j["res"]);
                j["cookie"] = cookie;
                UserFile user_file(atoi(id.c_str()));
                cout << "ready to get file tree" << endl;
                j["file_tree"] = user_file.get_file_tree();
                cout << "get it" << endl;
                string j_str = j.dump();
                write(info->fd, j_str.c_str(), j_str.length());
                writeLog(getNowTime(), " write to ", info->fd, "(fd) ", j_str.length(), " bytes.");
                authenticator.closeFd(info);
            }
        }
    }

    delete[] buffer;
}

void registerAccount()
{
    Authenticator authenticator;
    epoll_event events[epoll_size];

    // take out all fds in each round of service
    while (fd_mgr.getFdNum() > 0)
    {
        epoll_event event;
        event.events = EPOLLIN;
        UserInfo *info = new (nothrow) UserInfo;
        info->fd = fd_mgr.popFront();
        event.data.ptr = info;
        if (epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_ADD, info->fd, &event) < 0)
        {
            writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
            authenticator.closeFd(info);
            continue;
        }
        authenticator.fd_cnt++;
    }

    // read/write sharing
    char *buffer = new (nothrow) char[buffer_size];
    while (authenticator.fd_cnt > 0)
    {
        // block service, so it won't serve fds in next round unitl
        // its service ends in this round.
        int event_num = epoll_wait(authenticator.epoll_fd, events, epoll_size, -1);
        for (int i = 0; i < event_num; i++)
        {
            memset(buffer, 0, buffer_size);
            UserInfo *info = reinterpret_cast<UserInfo *>(events[i].data.ptr);
            // get infomation about user
            if (events[i].events & EPOLLIN)
            {
                int client_fd = info->fd;
                epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_DEL, client_fd, nullptr);
                int read_len = read(client_fd, buffer, buffer_size);
                // read error
                if (read_len < 0)
                {
                    writeLog(getNowTime(), " read request error, errno:", strerror(errno));
                    authenticator.closeFd(info);
                }
                // client has closed, it means client not sending any data
                else if (read_len == 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed before authorizing");
                    authenticator.closeFd(info);
                }
                // request_type must contain '\0', but this position is occupied by request.
                else if (read_len == buffer_size)
                {
                    writeLog(getNowTime(), "client(fd:", client_fd, ") send invalid file type, it's too long");
                    authenticator.closeFd(info);
                }
                // get it
                else
                {
                    // split user information from string
                    // (username, password)
                    vector<string> params = split(string(buffer), ' ');
                    info->username = params[0];
                    info->password = params[1];

                    epoll_event event;
                    event.events = EPOLLOUT;
                    event.data.ptr = info;
                    epoll_ctl(authenticator.epoll_fd, EPOLL_CTL_ADD, client_fd, &event);
                }
            }
            // return result
            else
            {
                User user;
                json j;
                j["ack"] = 1;
                j["res"] = user.user_register(info->username, info->password);
                writeLog(getNowTime(), " register status:", j["res"]);
                string j_str = j.dump();
                write(info->fd, j_str.c_str(), j_str.length());
                writeLog(getNowTime(), " write to ", info->fd, "(fd) ", j_str.length(), " bytes.");
                authenticator.closeFd(info);
            }
        }
    }

    delete[] buffer;
}
