#include"./include/webFrame.h"
#include"./include/download.h"
#include"./include/authorize.h"
#include"./include/upload.h"
#include"./include/fileOperation.h"

int main()
{
    web_frame.init();
    web_frame.route("download", download);
    web_frame.route("login", login);
    web_frame.route("register", registerAccount);
    web_frame.route("upload", upload);
    web_frame.route("fastUpload", fastUpload);
    web_frame.route("fileOperation", fileOperation);
    web_frame.run();
}
