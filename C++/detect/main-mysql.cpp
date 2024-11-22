#include <mysql/mysql.h>
#include <iostream>
#include <cstdlib>

int main() {
    MYSQL *conn;
    MYSQL_RES *res;
    MYSQL_ROW row;

    // 初始化 MySQL 连接
    conn = mysql_init(nullptr);
    if (conn == nullptr) {
        std::cerr << "mysql_init failed!" << std::endl;
        return EXIT_FAILURE;
    }

    // 连接数据库
    const char *host = "192.168.30.182";
    const char *user = "root";
    const char *password = "12345678"; // 替换为实际的密码
    const char *database = "ws_test"; // 替换为实际的数据库名

    if (mysql_real_connect(conn, host, user, password, database, 0, nullptr, 0) == nullptr) {
        std::cerr << "mysql_real_connect failed: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return EXIT_FAILURE;
    }

    // 执行 SQL 查询
    const char *query = "SELECT * FROM time_test";
    if (mysql_query(conn, query)) {
        std::cerr << "Query failed: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return EXIT_FAILURE;
    }

    // 获取查询结果
    res = mysql_store_result(conn);
    if (res == nullptr) {
        std::cerr << "mysql_store_result failed: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return EXIT_FAILURE;
    }

    // 遍历结果并打印
    std::cout << "Tables in database '" << database << "':" << std::endl;
    while ((row = mysql_fetch_row(res)) != nullptr) {
        std::cout << row[0] << " "<< row[1] << " "<< row[2] << std::endl;
    }

    // 清理资源
    mysql_free_result(res);
    mysql_close(conn);

    return EXIT_SUCCESS;
}