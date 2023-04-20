#pragma once

#include <string>
#include <sys/time.h>
#include <fstream>
#include <vector>
#include <mutex>

#include "config.h"
using namespace std;

extern recursive_mutex mtx;

extern ofstream log_file;

string getNowTime();

void writeLog();

vector<string> split(const string &s, const char seperator);

template <typename T, typename... Types>
void writeLog(const T &first_log, const Types &...rest_log)
{
	mtx.lock();
	log_file << first_log;
	writeLog(rest_log...);
	mtx.unlock();
}

tuple<string, int> getPeerIPWithPort(int fd);
bool Gbk2utf8(string &utfStr, string &srcStr);
