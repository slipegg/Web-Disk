/*
 * base64.h
 *
 *  Created on: Mar 16, 2016
 *      Author: root
 */

#ifndef BASE64_H_
#define BASE64_H_
#include <string>
#include <iostream>
// using namespace std;
std::string base64_encode(unsigned char const* , unsigned int len);//转码:传入字符串和长度，返回string

std::string base64_decode(std::string const& s); //解码:接收一个string


// std::string get_hex_md5(std::string content)

#endif /* BASE64_H_ */