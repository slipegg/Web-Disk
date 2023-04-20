#include <sys/epoll.h>
#include <unistd.h>
#include <errno.h>
#include <cstring>
#include <iostream>
#include <string>

#include "./include/fileOperation.h"
#include "./include/FDMgr.h"
#include "./include/config.h"
#include "./include/util.h"
#include "./include/disksql.h"
#include "./configor/json.hpp"

using namespace std;
using namespace configor;



void fileOperation()
{
    epoll_event events[epoll_size];
    int epoll_fd = epoll_create(epoll_size);
    if (epoll_fd < 0)
    {
        writeLog(getNowTime(), "create epoll error in download");
        exit(-1);
    }
    int fd_cnt = 0;

    // take out all fds in each round of service
    while (fd_mgr.getFdNum() > 0)
    {
        epoll_event event;
        event.events = EPOLLIN;
        event.data.fd = fd_mgr.popFront();
        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, event.data.fd, &event) < 0)
        {
            writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
            close(event.data.fd);
            continue;
        }
        fd_cnt++;
    }

    // read/write sharing
    char *buffer = new (nothrow) char[buffer_size];
    while (fd_cnt > 0)
    {
        int event_num = epoll_wait(epoll_fd, events, epoll_size, -1);
        for (int i = 0; i < event_num; i++)
        {
            memset(buffer, 0, buffer_size);
            // get infomation about user
            if (events[i].events & EPOLLIN)
            {
                int client_fd = events[i].data.fd;
                epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client_fd, nullptr);
                int read_len = read(client_fd, buffer, buffer_size);
                // read error
                if (read_len < 0)
                {
                    writeLog(getNowTime(), " read request error, errno:", strerror(errno));
                }
                // client has closed, it means client not sending any data
                else if (read_len == 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed before authorizing");
                }
                // request_type must contain '\0', but this position is occupied by request.
                else if (read_len == buffer_size)
                {
                    writeLog(getNowTime(), "client(fd:", client_fd, ") send invalid file type, it's too long");
                }
                // get it
                else
                {
                    // copy, cut, delDir, delFile, mkdir
                    // ['copy', cookie, old_file_path, new_file_path]
                    // ['cut', cookie, old_path, new_path]
                    // ['delDir', cookie, path]
                    // ['delFile', cookie, path]
                    // ['mkdir', cookie, path]

                    cout << buffer << endl;
                    vector<string> params = split(string(buffer), ' ');
                    json j;
                    User user;
                    UserFile user_file(atoi(user.get_id_by_token(params[1]).c_str()));
                    if (params[0] == "copy")
                    {
                        if (user_file.cp_file(params[2], params[3]) == 0)
                            j["ack"] = 1;
                        else
                            j["ack"] = 0;
                    }
                    else if (params[0] == "cut")
                    {
                        if (user_file.mv_file(params[2], params[3]) == 0)
                            j["ack"] = 1;
                        else
                            j["ack"] = 0;
                    }
                    else if (params[0] == "delDir")
                    {
                        if (user_file.del_folder(params[2]) == 0)
                            j["ack"] = 1;
                        else
                            j["ack"] = 0;
                    }
                    else if (params[0] == "delFile")
                    {
                        if (user_file.del_file(params[2]) == 0)
                            j["ack"] = 1;
                        else
                            j["ack"] = 0;
                    }
                    else if (params[0] == "mkdir")
                    {
                        if (user_file.add_folder(params[2]) == 0)
                            j["ack"] = 1;
                        else
                            j["ack"] = 0;
                    }
                    else
                    {
                        j["ack"] = 0;
                    }

                    writeLog(getNowTime(), " ", params[0], " status:", j["ack"]);
                    string j_str = j.dump();
                    write(client_fd, j_str.c_str(), j_str.length());
                }
                close(client_fd);
                fd_cnt--;
            }
        }
    }
    delete[] buffer;
}


