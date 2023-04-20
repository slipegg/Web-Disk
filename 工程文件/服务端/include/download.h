#pragma once

#include <sys/epoll.h>
#include <unistd.h>
#include <fstream>


struct DownloadInfo
{
    int fd;
    ifstream i_file;  // file to download
    int start_pos;
    int end_pos;
};

class DownloadHelper
{
public:
    int epoll_fd;
    const char seperator;
    // whhen it decreases to 0, this service round ends.
    int fd_cnt;

    DownloadHelper();

    ~DownloadHelper();

    void closeDownloadFd(DownloadInfo *info);
};


void download();