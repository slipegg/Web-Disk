#include <sys/epoll.h>
#include <unistd.h>
#include <errno.h>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <set>

#include "./include/upload.h"
#include "./include/FDMgr.h"
#include "./include/config.h"
#include "./include/util.h"
#include "./include/disksql.h"
#include "./configor/json.hpp"

using namespace std;
using namespace configor;

Clip::Clip()
{
    start_pos = end_pos = 0;
}

Clip::Clip(int start, int end)
{
    start_pos = start;
    end_pos = end;
}

UploadHelper::UploadHelper()
{
    epoll_fd = epoll_create(epoll_size);
    if (epoll_fd < 0)
    {
        writeLog(getNowTime(), "create epoll error in download");
        exit(-1);
    }
    fd_num = 0;
    clip_talbe = "upload_clip";
}

UploadHelper::~UploadHelper()
{
    close(epoll_fd);
}

// give back clip if client doesn't complete it.
// erase from corresponding UploadingFile.
void UploadHelper::closeFd(Client *client, bool alloc_clip_release_file)
{
    // it has been completed, discard it.
    if (client->clip->start_pos == client->clip->end_pos)
    {
        writeLog(getNowTime(), " fd(", client->fd, ") complete clip(", client->clip->start_pos, ",", client->clip->end_pos, ")");
        delete client->clip;
    }
    // give it back
    else
    {
        writeLog(getNowTime(), " fd(", client->fd, ") give back clip(", client->clip->start_pos, ",", client->clip->end_pos);
        client->file->to_be_uploaded_clips.push_back(client->clip);
    }
    close(client->fd);
    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client->fd, nullptr);
    fd_num--;
    if (alloc_clip_release_file)
    {
        writeLog(getNowTime(), " delete ", client->fd, " from file(", client->file->file_name, ")");
        client->file->clients.erase(client);
        if (existClient(client->file))
        {
            allocToCertainClient(client->file);
        }
        else
        {
            releaseFile(client->file);
        }
    }
    writeLog(getNowTime(), " close fd(", client->fd, ") in upload.closeFd()");
    delete client;
}

// take out all fds in each round of service
void UploadHelper::acceptAllClients()
{
    while (fd_mgr.getFdNum() > 0)
    {
        epoll_event event;
        event.events = EPOLLIN;
        Client *client = new (nothrow) Client;
        client->fd = fd_mgr.popFront();
        event.data.ptr = client;
        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client->fd, &event) < 0)
        {
            writeLog(getNowTime(), " epoll_ctr error, errno:", strerror(errno));
            closeFd(client);
            continue;
        }
        fd_num++;
        writeLog(getNowTime(), " accept ", client->fd, " in upload");
    }
}

// header:[file_name, total_len, cookie, full_path]
// associate UploadingFile with a client and allocate clip
void UploadHelper::acceptUploadHeader(Client *client, vector<string> &&header)
{
    writeLog(getNowTime(), " accept upload header of ", client->fd);
    client->cookie = header[2];
    client->full_path = header[3];
    string file_name = header[0];
    int file_size = atoi(header[1].c_str());
    cout << "judege file exist in db" << endl;
    if (existFile(file_name))
    {
        User user;
        cout << "add file in acceptUploadHeader" << endl;
        UserFile user_file(atoi(user.get_id_by_token(client->cookie).c_str()));
        user_file.add_file(file_name, client->full_path, file_size);

        epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client->fd, nullptr);
        fd_num--;
        json j;
        j["byte_num"] = header[1];
        string j_str = j.dump();
        write(client->fd, j_str.c_str(), j_str.length());
        close(client->fd);
        cout << "delete client in acceptUploadHeader" << endl;
        delete client;
        writeLog(getNowTime(), " file to upload exists, write it to file tree");
        return;
    }

    // this file isn't uploading, create UploadingFile in memory
    if (files.find(file_name) == files.end())
    {
        openFile(header);
    }
    UploadingFile *file = files[file_name];
    file->clients.insert(client);
    client->file = file;
    client->has_sent_header = true;
    // allocate clip to client.
    getNextClip(file, client);
}

// create UploadingFile in the files
// header:[file_name, total_len]
void UploadHelper::openFile(vector<string> &header)
{
    UploadingFile *file = new (nothrow) UploadingFile;
    files[header[0]] = file;
    file->file_name = header[0];

    writeLog(getNowTime(), " file exist:", access((file_path + header[0]).c_str(), F_OK));
    // file not exist, create clips
    if (access((file_path + header[0]).c_str(), F_OK) == -1)
    {
        writeLog(getNowTime(), " create file ", header[0]);
        int total_len = atoi(header[1].c_str());
        if (total_len < clip_num)
        {
            sql.exec("insert into " + clip_talbe + "(file_name,start,end) values('" +
                        header[0] + "'," + to_string(0) + "," + to_string(total_len) + ");");

            writeLog(getNowTime(), " create clip(0,", total_len, ") of file ", header[0]);
        }
        else
        {
            int start = 0, end = 0;
            // 向上取整
            int each_clip_len = (total_len + clip_num - 1) / clip_num;
            cout << "each_clip_len:" << each_clip_len << endl;
            cout << "total_len:" << total_len << endl;
            for (int i = 0; i < clip_num - 1; i++)
            {
                start = i * each_clip_len;
                end = start + each_clip_len;
                cout << "exe sql in openFile" << endl;
                sql.exec("insert into " + clip_talbe + "(file_name,start,end) values('" +
                         header[0] + "'," + to_string(start) + "," + to_string(end) + ");");

                writeLog(getNowTime(), " create clip(", start, ",", end, ") of file ", header[0]);
            }
            start = end;
            end = total_len;
            cout << "exe sql in openFile(latter)" << endl;
            sql.exec("insert into " + clip_talbe + "(file_name, start,end) values('" +
                    header[0] + "'," + to_string(start) + "," + to_string(end) + ");");
            writeLog(getNowTime(), " create clip(", start, ",", end, ") of file ", header[0]);
        }
        // create file
        file->o_file.open(file_path + header[0], ios::in | ios::out | ios::trunc | ios::binary);
    }
    else
    {
        file->o_file.open(file_path + header[0], ios::binary | ios::in | ios::out);
    }
    if (file->o_file.fail())
    {
        cerr << "can't open file " << header[0] << endl;
        writeLog(getNowTime(), " can't open file ", header[0]);
        exit(-1);
    }

    int file_size = atoi(header[1].c_str());
    cout << "header[1]:" << header[1] << endl;
    // get clips and has_uploaded_bytes_num from db
    vector<vector<string>> clips;
    int row_num, col_num;
    sql.exec_out("select start,end from " + clip_talbe + " where file_name='" + header[0] + "';",
                 clips, row_num, col_num);
    for (vector<string> &clip : clips)
    {
        int start = atoi(clip[0].c_str());
        int end = atoi(clip[1].c_str());
        file_size -= end - start;
        file->to_be_uploaded_clips.push_back(new Clip(start, end));
        writeLog(getNowTime(), " read clip(", start, ",", end, ") of file ", header[0], " from database");

        cout << "create clip:" << start << "," << end << endl;
    }
    file->has_uploaded_bytes_num = file_size;
    writeLog(getNowTime(), " file(", header[0], ") has upload ", file_size, " bytes");
    cout << "file->has_uploaded_bytes_num:" << file->has_uploaded_bytes_num << endl;
}

// if there aren't any clip, it return default clip
Clip *UploadHelper::allocClip(UploadingFile *file)
{
    Clip *clip;
    int num = file->to_be_uploaded_clips.size();
    if (num > 0)
    {
        clip = file->to_be_uploaded_clips[num - 1];
        file->to_be_uploaded_clips.pop_back();
        cout << "alloc clip in allocClip:" << clip->start_pos << "," << clip->end_pos << endl;
    }
    else
    {
        clip = new (nothrow) Clip();
    }
    return clip;
}

void UploadHelper::notifySendByteNum(UploadingFile *file)
{
    cout << "ready to nofiy byte num" << endl;
    json j;
    j["byte_num"] = file->has_uploaded_bytes_num;
    string j_str = j.dump();

    for (Client *client : file->clients)
    {
        write(client->fd, j_str.c_str(), j_str.length());
        cout << "notify client byte num:" << j["byte_num"] << endl;
    }
}

void UploadHelper::getNextClip(UploadingFile *file, Client *client)
{
    // send information about uploading file to client.
    Clip *clip = allocClip(file);
    cout << "delete clip in getNextClip" << endl;
    if (client->clip != nullptr)
        delete client->clip;
    client->clip = clip;
    writeLog(getNowTime(), " alloc clip(", clip->start_pos, ",", clip->end_pos, ") to ", client->fd);

    if (clip->start_pos != clip->end_pos)
    {
        cout << "alloc one to client,clip:" << clip->start_pos << "," << clip->end_pos << endl;
        // client is loading
        client->is_uploading = true;
        json j;
        j["start_pos"] = clip->start_pos;
        j["end_pos"] = clip->end_pos;
        j["byte_num"] = file->has_uploaded_bytes_num;
        string j_str = j.dump();
        writeLog(getNowTime(), " send ", j_str, " to ", client->fd);
        cout << "send start_pos and end_pos:" << j["start_pos"] << "," << j["end_pos"] << endl;
        if (write(client->fd, j_str.c_str(), j_str.length()) <= 0)
        {
            writeLog(getNowTime(), " send to fd(", client->fd, ")clip(", clip->start_pos, ",", clip->end_pos,") error");
            cout << "send error in getNextClip" << endl;
            closeFd(client);
            cout << "closeFd in getNextClip" << endl;
        }
    }
    else
    {
        client->is_uploading = false;
    }
    cout << "getNextClip ok" << endl;
}

// when file->to_be_uploaded_clips == 0 and all clients isn't uploading,
// the task will be completed.
bool UploadHelper::checkUploadAll(UploadingFile *file)
{
    cout << "ready to checkUploadAll" << endl;
    cout << "file->to_be_uploaded_clips.size():" << file->to_be_uploaded_clips.size() << endl;
    writeLog(getNowTime(), " check whether upload all the file ", file->file_name);
    if (file->to_be_uploaded_clips.size() > 0)
        return false;
    for (Client *client : file->clients)
    {
        cout << "client->is_uploading:" << client->is_uploading << endl;
        if (client->is_uploading)
            return false;
    }
    writeLog(getNowTime(), " file(", file->file_name, ") uploaded");
    cout << "checkUploadAll: all uploaded" << endl;
    notifySendByteNum(file);
    return true;
}

bool UploadHelper::existClient(UploadingFile *file)
{
    return file->clients.size() > 0;
}

void UploadHelper::allocToCertainClient(UploadingFile *file)
{
    if (file->clients.size() == 0 || file->to_be_uploaded_clips.size() == 0)
        return;
    for (Client *client : file->clients)
    {
        if (!client->is_uploading)
        {
            getNextClip(file, client);
            writeLog(getNowTime(), " select ", client->fd, " to get clip");
            break;
        }
    }
}

void UploadHelper::releaseFile(UploadingFile *file)
{
    cout << "release file" << endl;
    writeLog(getNowTime(), " release file ", file->file_name);

    cout << "delete from " + clip_talbe + " where file_name='" + file->file_name + "';" << endl;
    sql.exec("delete from " + clip_talbe + " where file_name='" + file->file_name + "';");

    // don't upload whole file, save clips
    if (file->to_be_uploaded_clips.size() > 0)
    {
        for (Clip *clip : file->to_be_uploaded_clips)
        {
            writeLog(getNowTime(), " save file(", file->file_name, ") clip(", clip->start_pos, ",", clip->end_pos, ")");

            cout << "exe sql in releaseFile:" << endl;
            cout << "insert into " + clip_talbe + "(file_name,start,end) values('" +
                        file->file_name + "'," + to_string(clip->start_pos) + "," + to_string(clip->end_pos) + ");"
                 << endl;

            sql.exec("insert into " + clip_talbe + "(file_name,start,end) values('" +
                     file->file_name + "'," + to_string(clip->start_pos) + "," + to_string(clip->end_pos) + ");");

            cout << "delete clip in releaseFile" << endl;
            delete clip;
            cout << "delete successfully" << endl;
        }
    }
    // write to file system
    else
    {
        writeLog(getNowTime(), " save file(", file->file_name, ") to database");
        cout << "add user_file to db" << endl;
        for (Client *client : file->clients)
        {
            User user;
            cout << "file->file_name:" << file->file_name << endl;
            cout << "file->full_path:" << client->full_path << endl;
            cout << "file->has_uploaded_bytes_num:" << file->has_uploaded_bytes_num << endl;
            cout << "client->cookie:" << endl;
            cout << client->cookie << endl;
            UserFile user_file(atoi(user.get_id_by_token(client->cookie).c_str()));
            cout << "ready to add" << endl;
            user_file.add_file(file->file_name, client->full_path, file->has_uploaded_bytes_num);
            cout << "add user_file successfully" << endl;
        }
    }

    cout << "close clients" << endl;
    // close client
    for (set<Client *>::iterator iter = file->clients.begin(); iter != file->clients.end(); iter++)
    {
        // client may be erased in closeFd()
        cout << "close client in releaseFile " << endl;
        closeFd(*iter, false);
        cout << "close successfully in releaseFile " << endl;
    }

    cout << "ready to close ofile" << endl;
    file->o_file.close();
    cout << "close file ok" << endl;
    files.erase(file->file_name);
    cout << "erase file" << endl;
    delete file;
    cout << "realease ok" << endl;
}

void upload()
{
    UploadHelper helper;
    epoll_event events[epoll_size];

    cout << "accept all clients in upload" << endl;
    helper.acceptAllClients();

    // read/write sharing
    char *buffer = new (nothrow) char[buffer_size];
    while (helper.fd_num > 0)
    {
        helper.acceptAllClients();
        // block service, so it won't serve fds in next round unitl
        // its service ends in this round.
        cout << "ready to wait fdnum:" << helper.fd_num << endl;
        int event_num = epoll_wait(helper.epoll_fd, events, epoll_size, -1);
        cout << "waited" << endl;
        for (int i = 0; i < event_num; i++)
        {
            memset(buffer, 0, buffer_size);
            Client *client = reinterpret_cast<Client *>(events[i].data.ptr);
            // get infomation about user
            if (events[i].events & EPOLLIN)
            {
                int client_fd = client->fd;
                int read_len = read(client_fd, buffer, buffer_size);
                // client has closed, it means client not sending any data
                if (read_len <= 0)
                {
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed actively");
                    helper.closeFd(client);
                    writeLog(getNowTime(), " client(fd:", client_fd, ") closed successfully");
                }
                // get data normally
                else
                {
                    // it's file header
                    if (!client->has_sent_header)
                    {
                        helper.acceptUploadHeader(client, split(string(buffer), ' '));
                        cout << "acceptUploadHeader ok" << endl;
                    }
                    // it's data
                    else
                    {
                        writeLog(getNowTime(), " client(", client->fd, ") send data len:", read_len);
                        UploadingFile *file = client->file;
                        file->o_file.seekp(client->clip->start_pos, ios::beg);
                        file->o_file.write(buffer, read_len);
                        client->clip->start_pos += read_len;
                        file->has_uploaded_bytes_num += read_len;
                        cout << client->fd << ":(" << client->clip->start_pos << "," << client->clip->end_pos << ")" << endl;
                        if (client->clip->start_pos >= client->clip->end_pos)
                        {
                            // helper.notifySendByteNum(file);
                            helper.getNextClip(file, client);
                            if (helper.checkUploadAll(file))
                            {
                                cout << "get all file succ" << endl;
                                helper.releaseFile(file);
                            }
                        }
                    }
                }
            }
        }
    }

    delete[] buffer;
}

bool existFile(string file_name)
{
    RealFile real_file;
    return real_file.is_file_exist(file_name);
}

void fastUpload()
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
                    cout << buffer << endl;
                    // [file_name, cookie, path, length]
                    vector<string> params = split(string(buffer), ' ');

                    char exist[1];
                    if (existFile(params[0]))
                    {
                        exist[0] = '1';
                        User user;
                        UserFile user_file(atoi(user.get_id_by_token(params[1]).c_str()));
                        user_file.add_file(params[0], params[2], atoi(params[3].c_str()));
                        writeLog(getNowTime(), " file(", params[0], ") fast upload");
                    }
                    else
                    {
                        exist[0] = '0';
                        writeLog(getNowTime(), " file(", params[0], ") doesn't fast upload");
                    }
                    write(client_fd, exist, sizeof(exist));
                }
                close(client_fd);
                fd_cnt--;
            }
        }
    }

    delete[] buffer;
}

