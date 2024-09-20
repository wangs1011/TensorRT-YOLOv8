"""
使用Ffmpeg 将视频文件推流到远程服务器

"""
import subprocess

def stream_video_to_rtsp(input_file, rtsp_url):
    """
    使用ffmpeg将本地视频文件推送到RTSP流服务器
    :param input_file: 本地视频文件的路径
    :param rtsp_url: RTSP服务器地址
    """
    # 构建FFmpeg命令
    ffmpeg_command = [
        'ffmpeg',
        '-v', 'debug',
        '-re',  # 以实时帧率读取文件
        '-i', input_file,  # 输入文件路径
        '-c:v', 'libx264',  # 视频编码器使用H.264
        '-preset', 'veryfast',  # 使用快速压缩
        '-f', 'rtsp',  # 输出格式为RTSP
        '-rtsp_transport', 'tcp',  # 传输方式为TCP
        rtsp_url  # RTSP服务器URL
    ]

    # 执行FFmpeg命令
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        stdout, stderr = process.communicate()  # 等待命令执行完成
        if process.returncode == 0:
            print("推流成功!")
        else:
            print(f"推流失败: {stderr.decode('utf-8')}")
    except Exception as e:
        print(f"推流过程中出错: {str(e)}")

if __name__ == '__main__':
    # 示例调用
    video_file = '/Users/wshuo/fsdownload/street.mp4'  # 输入视频文件的路径
    rtsp_stream_url = 'rtsp://admin:admin123@192.168.20.200:554/cam/street'  # 替换为你的RTSP服务器地址
    stream_video_to_rtsp(video_file, rtsp_stream_url)
