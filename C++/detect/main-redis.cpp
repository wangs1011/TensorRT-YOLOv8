#include <hiredis/hiredis.h>
#include <iostream>
#include <string>
#include <nlohmann/json.hpp>

int main() {
    // 连接到Redis服务器
    const char* redis_host = "127.0.0.1";
    int redis_port = 6379;
    const char* redis_pass = "thd2000"; // 替换为你的密码

    // 创建连接
    redisContext* c = redisConnect(redis_host, redis_port);
    if (c != NULL && c->err) {
        std::cerr << "连接错误: " << c->errstr << std::endl;
        redisFree(c);
        return 1;
    }

    // 认证
    redisReply* reply = (redisReply*)redisCommand(c, "AUTH %s", redis_pass);
    if (reply->type == REDIS_REPLY_ERROR) {
        std::cerr << "认证失败: " << reply->str << std::endl;
        freeReplyObject(reply);
        redisFree(c);
        return 1;
    }
    freeReplyObject(reply);

    // 连接成功，可以进行操作
    // 写入键值对
//    reply = (redisReply*)redisCommand(c, "SET c++_test {\"jobFlinkName\":\"测试\"}");
//
//    if (reply->type == REDIS_REPLY_STATUS) {
//        std::cout << "设置成功" << std::endl;
//    }
//    freeReplyObject(reply);

    // 假设你已经有一个键"mykey"，它的值是一个JSON字符串
    reply = (redisReply*)redisCommand(c, "GET c++_test");
    if (reply->type == REDIS_REPLY_ERROR) {
        std::cerr << "命令错误: " << reply->str << std::endl;
        // 处理错误
        freeReplyObject(reply);
        redisFree(c);
        return 1;
    }

    // 假设返回的是字符串
    if (reply->type != REDIS_REPLY_STRING) {
        std::cerr << "期望得到字符串类型的回复" << std::endl;
        // 处理错误
        freeReplyObject(reply);
        redisFree(c);
        return 1;
    }

    std::string redis_result = reply->str;
    freeReplyObject(reply);

    // 解析JSON
    nlohmann::json jsonParsed = nlohmann::json::parse(redis_result);

    // 读取JSON数据
    std::cout << "jobFlinkName: " << jsonParsed["jobFlinkName"] << std::endl;




    // 关闭连接
    redisFree(c);
    return 0;
}