#include <sys/epoll.h>
#include <iostream>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <fstream>
#include <unordered_map>

#include "./include/FDMgr.h"
#include "./include/download.h"
#include "./include/config.h"
#include "./include/util.h"

/*
struct DownloadInfo
{
    int fd;
    ifstream i_file;
    int start_pos;
    int end_pos;
};*/

DownloadHelper::DownloadHelper() : seperator(' ')
{
    epoll_fd = epoll_create(epoll_size);
    if (epoll_fd < 0)
    {
        writeLog(getNowTime(), "create epoll error in download");
        return;
    }
    fd_cnt = 0;
}

DownloadHelper::~DownloadHelper()
{
    close(epoll_fd);
}

void DownloadHelper::closeDownloadFd(DownloadInfo *info)
{
    fd_cnt--;
    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, info->fd, nullptr);
    close(info->fd);
    info->i_file.close();
    delete info;
    cout << "close fd" << endl;
}

void download()
{
    DownloadHelper download_helper;
    epoll_event events[epoll_size];

    // take out all fds in each round of service
    while (fd_mgr.getFdNum() > 0)
    {
        epoll_event event;
        event.events = EPOLLIN;
        DownloadInfo *info = new (nothrow) DownloadInfo;
        info->fd = fd_mgr.popFront();
        event.data.ptr = info;
        cout << "download get fd:" << info->fd << endl;
        if (epoll_ctl(download_helper.epoll_fd, EPOLL_CTL_ADD, info->fd, &event) < 0)
        {
            writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
            download_helper.closeDownloadFd(info);
            continue;
        }
        download_helper.fd_cnt++;
    }

    // read/write sharing
    char *buffer = new (nothrow) char[buffer_size];
    while (download_helper.fd_cnt > 0)
    {
        // block service, so it won't serve fds in next round unitl
        // its service ends in this round.
        int event_num = epoll_wait(download_helper.epoll_fd, events, epoll_size, -1);
        for (int i = 0; i < event_num; i++)
        {
            memset(buffer, 0, buffer_size);
            DownloadInfo *info = reinterpret_cast<DownloadInfo *>(events[i].data.ptr);
            // get infomation about file to be download
            if (events[i].events & EPOLLIN)
            {
                int client_fd = info->fd;
                epoll_ctl(download_helper.epoll_fd, EPOLL_CTL_DEL, client_fd, nullptr);
                cout <<  "ready to read" << endl;
                int read_len = read(client_fd, buffer, buffer_size);
                cout << "readlen:" << read_len << endl;
                // read error
                if (read_len < 0)
                {
                    writeLog(getNowTime(), " read request error, errno:", strerror(errno));
                    download_helper.closeDownloadFd(info);
                }
                // client has closed, it means client not sending any data
                else if (read_len == 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed before downloading");
                    download_helper.closeDownloadFd(info);
                }
                // request_type must contain '\0', but this position is occupied by request.
                else if (read_len == buffer_size)
                {
                    writeLog(getNowTime(), "client(fd:", client_fd, ") send invalid file type, it's too long");
                    download_helper.closeDownloadFd(info);
                }
                // get it
                else
                {
                    // split file information from string
                    // (md5, start_pos, length)
                    cout << buffer << endl;
                    vector<string> params = split(string(buffer), ' ');
                    cout<< "params[0]:" << params[0] << endl;
                    writeLog(getNowTime(), " ", info->fd, " download ", params[0]);

                    info->i_file.open(file_path + params[0], ios::binary);

                    // can't open
                    if (info->i_file.fail())
                    {
                        writeLog(getNowTime(), " file that client(fd:", client_fd, ") downloads can't open");
                        download_helper.closeDownloadFd(info);
                    }
                    info->start_pos = atoi(params[1].c_str());
                    info->end_pos = atoi(params[2].c_str()) + info->start_pos;
                    // download file from specified location
                    info->i_file.seekg(info->start_pos, ios::beg);
                    epoll_event event;
                    event.events = EPOLLOUT;
                    event.data.ptr = info;
                    epoll_ctl(download_helper.epoll_fd, EPOLL_CTL_ADD, client_fd, &event);
                }
            }
            // download file
            else
            {
                // read fully or partly
                int read_len = min(buffer_size, info->end_pos - info->start_pos);
                info->i_file.read(buffer, read_len);
                int write_len = write(info->fd, buffer, read_len);
                if (write_len <= 0)
                {
                    // buffer is full
                    if (errno == EAGAIN)
                    {
                        info->i_file.seekg(-read_len, ios::cur);
                    }
                    // server has closed
                    else if (errno == EPIPE || errno == ENOENT || errno == ECONNRESET)
                    {
                        download_helper.closeDownloadFd(info);
                    }
                    else
                    {
                        writeLog(getNowTime(), " send to client, errno has an unknown errno:", strerror(errno));
                        download_helper.closeDownloadFd(info);
                    }
                }
                else
                {
                    writeLog(getNowTime(), " write to ", info->fd, "(fd) ", write_len, " bytes.");
                    info->start_pos += write_len;
                    if (info->i_file.fail())
                    {
                        info->i_file.clear();
                    }
                    info->i_file.seekg(info->start_pos, ios::beg);
                    // send all successfully, close fd.
                    if (info->start_pos >= info->end_pos)
                    {
                        writeLog(getNowTime(), " ", info->fd, " download file successfully");
                        download_helper.closeDownloadFd(info);
                    }
                }
            }
        }
    }

    delete[] buffer;
}
