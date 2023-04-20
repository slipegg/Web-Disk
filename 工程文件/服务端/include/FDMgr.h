#pragma once

#include <map>
#include <queue>
#include <mutex>
#include <thread>
#include<unordered_map>
#include<condition_variable>

#include "util.h"

using namespace std;
using namespace std::this_thread;

/*
manage all fds that wait to be served.
*/
class FDMgr
{
private:
    // each thread has one queue to store fds
    map<thread::id, queue<int>> fds;
    // main thread and service thread will access queue together, make it exclusive.
    // if thread has queue, it must has mutex, vice versa.
    map<thread::id, mutex *> queue_mtx;
    // thread will go to sleep if there aren't any fds, 
    // use condition_variable and mutex to archive.
    unordered_map<thread::id, tuple<condition_variable *, mutex *>> condition_lock;


    queue<int> *getFdQueue(thread::id t_id);

    void addFd(thread::id t_id, int fd);

    mutex &getMutex();

    tuple<condition_variable *, mutex *> &getLockTuple();

public:
    friend class WebFrame;

    int peek();

    int popFront();

    int getFdNum();

};



extern FDMgr fd_mgr;
