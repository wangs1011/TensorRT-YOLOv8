"""
使用本程序，接受转化过来的视频流
"""

import socket
import cv2
import numpy as np
import sys
import struct
import pickle


def run(socket_server_ip, socket_server_port):
    # 创建 socket 对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((socket_server_ip, socket_server_port))

    data = b""
    payload_size = struct.calcsize("L")

    while True:
        # 接收视频帧的大小
        while len(data) < payload_size:
            data += client_socket.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        # 接收实际帧数据
        while len(data) < msg_size:
            data += client_socket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # 反序列化视频帧
        frame = pickle.loads(frame_data)

        # 显示帧
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 3:
        print('PARAMS ERROR,usage is python receive_video_bytes.py <socket_server_ip> <socket_server_port>')
        sys.exit(0)
    run(args[1], int(args[2]))
