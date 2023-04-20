#pragma once

#include <sys/epoll.h>
#include <functional>
#include <unordered_map>
#include <thread>

#include <iostream>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <errno.h>
#include <sys/time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <mutex>
#include <condition_variable>
#include <tuple>

#include "FDMgr.h"

using namespace std;
using namespace std::this_thread;
class WebFrame
{
private:
    int epoll_fd;
    int accept_client_fd;
    mutex thread_map_mux;
    unordered_map<string, thread::id> transaction_threads;

    void startService(int client_fd, string request_type);

    void setNonblock(int fd);

    bool verifyID(vector<string> &header);

public:
    WebFrame();

    ~WebFrame();

    void route(string url, function<void()> func);

    void init();

    /*
    main loop.
    accept client and its service type of request.
    when got the service type, the fd will be removed from epoll.
    */
    void run();
};

extern WebFrame web_frame;
