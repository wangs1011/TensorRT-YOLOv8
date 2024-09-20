"""
提取视频中的音频，并保存
"""

from moviepy.editor import VideoFileClip



video_path = '/Users/wshuo/Music/武林外传音频/武林外传01：郭女侠怒砸同福店，佟掌柜妙点迷路人.rmvb'
mp3_path = '/Users/wshuo/Music/武林外传音频/001.mp3'

'''
@Project ：视频转音频 
@File    ：movie2mp3_.py
@IDE     ：PyCharm 
@Author  ：一晌小贪欢（278865463@qq.com）
@Date    ：2024/2/29 13:20 
'''

import os
from ffmpy3 import FFmpeg

# filepath：待处理视频的文件路径
filepath = "/Users/wshuo/Music/武林外传"
filename = os.listdir(filepath)

print("待处理的视频文件:")
print(filename)
print("\n")

# output_dir：输出音频文件的路径
output_dir = "/Users/wshuo/Music/武林外传音频"

# 读取上次已导出的音频文件名（防止多次运行，出现overwrited的错误）
exit_filename = os.listdir(output_dir)
print("已导出的音频文件: ")
print(exit_filename)

for i in range(len(filename)):
    # 改文件的后缀名
    changefile = filepath + "/" + filename[i]
    change_postfix_name =(filename[i].replace('wmv', 'mp3')
                          .replace('flv', 'mp3')
                          .replace('rmvb', 'mp3')

                          ) # 另外的视频格式请自行添加

    outputfile = output_dir + "/" + change_postfix_name
    if change_postfix_name in exit_filename:
        continue
    print(changefile)
    # 利用FFmpeg进行转换
    fpg = FFmpeg(inputs={changefile: None},
                 outputs={outputfile: '-vn -ar 44100 -ac 2 -ab 192 -f mp3'})  # mp3也可以换成wav等格式
    print(fpg.cmd)
    fpg.run()

print("\n任务完成！！！")

