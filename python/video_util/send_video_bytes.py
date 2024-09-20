"""
使用本程序，将视频文件转为socket流
"""
import sys

import cv2
import socket
import pickle
import struct

SOCKET_SERVER_IP = '192.168.20.136'
SOCKET_SERVER_PORT = 17774


def run():
    # 创建 socket 对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SOCKET_SERVER_IP, SOCKET_SERVER_PORT))
    server_socket.listen(5)

    # 连接客户端
    client_socket, addr = server_socket.accept()
    print(f"连接地址: {addr}")

    # 初始化摄像头
    cap = cv2.VideoCapture(0)  # 0 表示本地摄像头

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 压缩图像
        data = pickle.dumps(frame)
        # 发送数据长度和数据本身
        client_socket.sendall(struct.pack("L", len(data)) + data)

    cap.release()
    client_socket.close()
    server_socket.close()


if __name__ == '__main__':
    run()
