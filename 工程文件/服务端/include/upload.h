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

// #include "./include/config.h"
// #include "./include/util.h"

using namespace std;

struct Clip
{
    int start_pos;
    int end_pos;
    Clip();
    Clip(int start, int end);
};

struct UploadingFile;

struct Client
{
    int fd;
    Clip *clip;
    bool has_sent_header = false;
    bool is_uploading = false;
    UploadingFile *file = nullptr;
    string cookie;
    string full_path;
};

struct UploadingFile
{
    string file_name;
    // for notifing clients the byte num uploaded by all clients
    int has_uploaded_bytes_num;
    // client who is uploading this file
    set<Client *> clients;
    // clip will be allocated to client.
    // if client doesn't complete uploading this clip, clip will be put back into
    // to_be_uploaded_clips.
    vector<Clip *> to_be_uploaded_clips;
    // all clients who is uploading share
    fstream o_file;
};

class UploadHelper
{
public:
    int epoll_fd;
    unordered_map<string, UploadingFile *> files;
    int fd_num;
    string clip_talbe;

    UploadHelper();

    ~UploadHelper();

    // give back clip if client doesn't complete it.
    // erase from corresponding UploadingFile.
    void closeFd(Client *client, bool alloc_clip_release_file=true);

    // take out all fds in each round of service
    void acceptAllClients();

    // header:[file_name, total_len]
    // associate UploadingFile with a client and allocate clip
    void acceptUploadHeader(Client *client, vector<string> &&header);
    // create UploadingFile in the files
    // header:[file_name, total_len]
    void openFile(vector<string> &header);

    // if there aren't any clip, it return nullptr
    Clip *allocClip(UploadingFile *file);

    void notifySendByteNum(UploadingFile *file);

    void getNextClip(UploadingFile *file, Client *client);

    // when file->to_be_uploaded_clips == 0 and all clients isn't uploading,
    // the task will be completed.
    bool checkUploadAll(UploadingFile *file);

    void releaseFile(UploadingFile *file);

    bool existClient(UploadingFile *file);

    void allocToCertainClient(UploadingFile *file);

};

void upload();

bool existFile(string file_name);

void fastUpload();
    