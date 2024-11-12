#include <hiredis/hiredis.h>
#include <iostream>
#include <string>

int main() {
    // 创建连接到Redis服务器的连接
    redisContext *c = redisConnect("127.0.0.1", 6379);
    if (c != NULL && c->err) {
        std::cerr << "连接错误: " << c->errstr << std::endl;
        // 处理错误
        return 1;
    }

    // 设置Redis回调函数，用于异步操作
    hiredis::setDefaultAllocators();

    // 向Redis发送命令
    redisReply *reply = (redisReply*)redisCommand(c, "GET key");
    if (reply->type == REDIS_REPLY_ERROR) {
        std::cerr << "命令错误: " << reply->str << std::endl;
        // 处理错误
        freeReplyObject(reply);
        redisFree(c);
        return 1;
    }

    if (reply->type == REDIS_REPLY_STRING) {
        std::string value(reply->str, reply->len);
        std::cout << "获取的值: " << value << std::endl;
    }

    // 释放reply对象
    freeReplyObject(reply);

    // 关闭连接
    redisFree(c);

    return 0;
}