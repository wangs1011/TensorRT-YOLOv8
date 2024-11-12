#include <iostream>
#include <curl/curl.h>

int main() {
    CURL *curl;
    CURLcode res;

    curl_mime *mime;
    curl_mimepart *part;

    curl = curl_easy_init();
    if(curl) {
        // 设置URL
        curl_easy_setopt(curl, CURLOPT_URL, "http://192.168.30.182:23777/yolov8_test");

        // 初始化mime结构，用于存放multipart表单数据
        mime = curl_mime_init(curl);

        // 添加文本字段
//        part = curl_mime_addpart(mime);
//        curl_mime_name(part, "username");  // 表单字段名
//        curl_mime_data(part, "john_doe", CURL_ZERO_TERMINATED);  // 字段值

        // 添加图片文件字段
        part = curl_mime_addpart(mime);
        curl_mime_name(part, "file");  // 表单字段名
        curl_mime_filedata(part, "/home/ods/wshuo_test/TensorRT-YOLOv8/C++/detect/images/bus.jpg");  // 文件路径

        // 将mime结构附加到请求中
        curl_easy_setopt(curl, CURLOPT_MIMEPOST, mime);

        // 执行请求
        res = curl_easy_perform(curl);

        // 检查是否成功
        if(res != CURLE_OK)
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        else
            std::cout << "Image uploaded successfully!" << std::endl;

        // 清理
        curl_mime_free(mime);  // 释放mime结构
        curl_easy_cleanup(curl);
    }
    return 0;
}