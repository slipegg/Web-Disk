#include <map>
#include <queue>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <condition_variable>
#include<iostream>

#include "include/util.h"
#include "include/FDMgr.h"

using namespace std;
using namespace std::this_thread;

FDMgr fd_mgr;


queue<int> *FDMgr::getFdQueue(thread::id t_id)
{
    // thread has no queue, give it one and generate mutex
    if(queue_mtx.find(t_id) == queue_mtx.end())
    {
        fds[t_id] = queue<int>();
        queue_mtx[t_id] = new (nothrow) mutex();
        if (queue_mtx[t_id] == NULL)
        {
            writeLog(getNowTime(), " create mutex error");
            exit(-1);
        }
    }
    queue_mtx[t_id]->lock();
    map<thread::id, queue<int>>::iterator iter = fds.find(t_id);
    queue<int> *q = &(iter->second);
    queue_mtx[t_id]->unlock();
    return q;
}

void FDMgr::addFd(thread::id t_id, int fd)
{
    queue<int> *q = getFdQueue(t_id);
    queue_mtx[t_id]->lock();
    q->push(fd);
    // wake up thread every time add fd.
    // it won't go wrong if thread has been awake.
    get<0>(condition_lock[t_id])->notify_one();
    queue_mtx[t_id]->unlock();
}

/*
provide mutex for condition_variable
*/
mutex &FDMgr::getMutex()
{
    thread::id id = get_id();
    if (condition_lock.find(id) == condition_lock.end())
    {
        condition_lock[id] = forward_as_tuple(new (nothrow) condition_variable(), new (nothrow) mutex());
    }
    mutex &m = *(get<1>(condition_lock[id]));
    return m;
}

tuple<condition_variable *, mutex *> &FDMgr::getLockTuple()
{
    return condition_lock[get_id()];
}

int FDMgr::peek()
{
    thread::id id = get_id();
    queue<int> *q = getFdQueue(id);
    if (q == nullptr)
    {
        writeLog(getNowTime(), " this thread(id:", id, ") has no fd queue");
        return -1;
    }
    int fd;
    queue_mtx[id]->lock();
    if (q->size() > 0)
        fd = q->front();
    else
        fd = -1;
    queue_mtx[id]->unlock();
    return fd;
}

int FDMgr::popFront()
{
    thread::id id = get_id();
    queue<int> *q = getFdQueue(id);
    if (q == nullptr)
    {
        writeLog(getNowTime(), " this thread(id:", id, ") has no fd queue");
        return -1;
    }
    int fd;
    queue_mtx[id]->lock();
    if (q->size() > 0)
    {
        fd = q->front();
        q->pop();
    }
    else
        fd = -1;
    queue_mtx[id]->unlock();
    return fd;
}

int FDMgr::getFdNum()
{
    thread::id id = get_id();
    queue<int> *q = getFdQueue(id);
    int num;
    queue_mtx[id]->lock();
    num = q->size();
    queue_mtx[id]->unlock();

    return num;
}
