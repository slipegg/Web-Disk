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
#include <cstring>
#include <signal.h>
#include <sys/socket.h>

#include "./include/webFrame.h"
#include "./include/FDMgr.h"
#include "./include/config.h"
#include "./include/util.h"
#include "./include/disksql.h"

using namespace std;
using namespace std::this_thread;

// add fd to corresponding fd_queue
void WebFrame::startService(int client_fd, string request_type)
{
    for (auto &t : transaction_threads)
    {
        cout << "key:" << t.first << endl;
        cout << "compare with " << request_type << " :" << (t.first == request_type) << endl;
    }
    cout << "compare in map:"
         << " :" << !(transaction_threads.find(request_type) == transaction_threads.end()) << endl;
    cout << endl;

    if (transaction_threads.find(request_type) == transaction_threads.end())
    {
        writeLog(getNowTime(), " request type not found, type is ", request_type);
        return;
    }
    fd_mgr.addFd(transaction_threads[request_type], client_fd);
}

WebFrame::WebFrame()
{
    epoll_fd = epoll_create(epoll_size);
    if (epoll_fd == -1)
    {
        cerr << "can't create connection epoll" << endl;
        exit(-1);
    }
}

WebFrame::~WebFrame()
{
    close(epoll_fd);
}

void WebFrame::setNonblock(int fd)
{
    int flag = fcntl(fd, F_GETFL, 0);
    if (fcntl(fd, F_SETFL, flag | O_NONBLOCK) < 0)
    {
        cerr << "can't set nonblock" << endl;
    }
}

bool WebFrame::verifyID(vector<string> &header)
{
    if (header[0] == "register" || header[0] == "login")
        return true;
    // (type, token)
    else
    {
        User user;
        if (user.get_id_by_token(header[1]) == to_string(-1))
        {
            writeLog(getNowTime(), " validation failed");
            return false;
        }
        else
        {
            writeLog(getNowTime(), " validation successfully");
            return true;
        }
    }
}

void WebFrame::route(string url, function<void()> func)
{
    if (transaction_threads.find(url) != transaction_threads.end())
    {
        cerr << "url repeated" << endl;
        return;
    }

    // if you assign a lambda function to a variable and then
    // use this variable as the argument of thread, it will trigger
    // SIGSEGV(it means crossing the border) and be killed.
    // note that it will go wrong when running on windows!!! it's too strange.
    thread t([&]
             {
            thread_map_mux.lock();
            transaction_threads[url] = get_id();
            thread_map_mux.unlock();
            cout << "create thread id:" << get_id() << " type is " << url << endl;
            // thread will sleep on its first come.
            while (true)
            {
                unique_lock<mutex> lock(fd_mgr.getMutex());
                auto lock_tuple = fd_mgr.getLockTuple();
                // if there is no fd, go to sleep
                (get<0>(lock_tuple))->wait(lock, [&]() -> bool
                    { return fd_mgr.getFdNum() > 0; });
                cout << get_id() << " awake" << endl;
                func();
            } });

    t.detach();
}

/*
initiate epoll and server_addr
*/
void WebFrame::init()
{
    accept_client_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (accept_client_fd < 0)
    {
        cerr << "acquire server fd error, errno:" << strerror(errno) << endl;
        exit(-1);
    }

    int reuse = 1;
    if (setsockopt(accept_client_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0)
    {
        cerr << "setsockopet error" << endl;
        exit(-1);
    }

    sockaddr_in server_addr;
    bzero(&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(local_port);
    server_addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(accept_client_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        cerr << "bind server addr error, errno:" << strerror(errno) << endl;
        exit(-1);
    }

    if (listen(accept_client_fd, epoll_size) < 0)
    {
        cerr << "listen error, errno:" << strerror(errno) << endl;
        exit(-1);
    }

    // add accept_client_fd to epoll for accepting connection
    epoll_event event;
    event.events = EPOLLIN;
    event.data.fd = accept_client_fd;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, accept_client_fd, &event) < 0)
    {
        cerr << "add accept_client_fd to epoll error, errno:" << strerror(errno) << endl;
        exit(-1);
    }

    if (log_file.fail())
    {
        cerr << "can't open log file, errno:" << strerror(errno) << endl;
    }

    signal(SIGPIPE, [](int sig) {});
}

/*
main loop.
accept client and its service type of request.
when got the service type, the fd will be removed from epoll.
*/
void WebFrame::run()
{
    epoll_event events[epoll_size];
    // client will send request type once connected
    char request_type[request_type_max_size];
    while (true)
    {
        int readable_fd_num = epoll_wait(epoll_fd, events, epoll_size, -1);
        for (int i = 0; i < readable_fd_num; i++)
        {
            // client comes to connect
            if (events[i].data.fd == accept_client_fd)
            {
                sockaddr_in client_addr;
                socklen_t len = sizeof(client_addr);
                int client_fd = accept(accept_client_fd, reinterpret_cast<sockaddr *>(&client_addr), &len);
                if (client_fd < 0)
                {
                    writeLog(getNowTime(), " accept client error, errno:", strerror(errno));
                    continue;
                }
                auto info = getPeerIPWithPort(client_fd);
                writeLog(getNowTime(), " ", get<0>(info), ":", get<1>(info), " connect");
                setNonblock(client_fd);
                // wait client sending type message of request
                epoll_event event;
                event.events = EPOLLIN;
                event.data.fd = client_fd;
                if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &event) < 0)
                {
                    writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
                    continue;
                }
            }
            // client sends request type
            else if (events[i].events & EPOLLIN)
            {
                memset(request_type, 0, request_type_max_size * sizeof(char));
                int client_fd = events[i].data.fd;
                // read request type
                int read_len = read(client_fd, request_type, request_type_max_size);
                if (read_len < 0)
                {
                    writeLog(getNowTime(), " read request error, errno:", strerror(errno));
                }
                // client has closed, it means client not sending any data
                else if (read_len == 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed before sending request type");
                }
                // request_type must contain '\0', but this position is occupied by request.
                else if (read_len == request_type_max_size)
                {
                    writeLog(getNowTime(), "client(fd:", client_fd, ") send invalid request type, it's too long");
                }
                // the rest of data will be read in the corresponding service.
                epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client_fd, nullptr);
                if (read_len > 0 && read_len < request_type_max_size)
                {
                    cout << "request type:" << request_type << endl;
                    writeLog(getNowTime(), " request type of client:", string(request_type));
                    vector<string> header = split(request_type, ' ');
                    if (verifyID(header))
                    {
                        char ack[] = {'a', 'c', 'k'};
                        write(client_fd, ack, sizeof(ack));
                        startService(client_fd, header[0]);
                    }
                    else
                    {
                        string deny("authentication failed");
                        write(client_fd, deny.c_str(), deny.length());
                    }
                }
            }
            // unknown event type
            else
            {
                cerr << "unknown event type" << endl;
            }
        }
    }
}

WebFrame web_frame;
