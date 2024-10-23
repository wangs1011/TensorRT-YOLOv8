"""
yolov8模型推理 服务化

"""
import os.path
import random
import cv2
import numpy as np
import torch

from ultralytics.nn.autobackend import AutoBackend
from ultralytics.utils import ops
from flask import Flask, request
from PIL import Image

import io
import json
import time
MODEL_PATH = r"weight/yolov8/yolov8s.pt"  # 模型的所在文件夹smoke_fire_person_x_20230303
GPU_ID = 'cpu'

class YOLOV8DetectionInfer:
    def __init__(self, weights, device, conf_thres, iou_thres) -> None:
        self.imgsz = 640
        self.device = device
        self.model = AutoBackend(weights, device=torch.device(device))
        self.model.eval()
        self.names = self.model.names
        self.half = False
        self.conf = conf_thres
        self.iou = iou_thres
        self.color = {"font": (255, 255, 255)}
        self.color.update(
            {self.names[i]: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
             for i in range(len(self.names))})

    def infer(self, img_src):
        # print(type(img_path))
        # img_src = cv2.imread(img_path)
        print(type(img_src))
        img = self.precess_image(img_src, self.imgsz, self.half, self.device)
        preds = self.model(img)
        det = ops.non_max_suppression(preds, self.conf, self.iou, classes=None, agnostic=False, max_det=300,
                                      nc=len(self.names))
        for i, pred in enumerate(det):
            lw = max(round(sum(img_src.shape) / 2 * 0.003), 2)  # line width
            tf = max(lw - 1, 1)  # font thickness
            sf = lw / 3  # font scale
            pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], img_src.shape)
            results = pred.cpu().detach().numpy()

        print('YOLOV8DetectionInfer 服务\t模型识别结果:' + str(results))

        return results
        # cv2.imwrite(os.path.join(save_path, os.path.split(img_path)[-1]), img_src)

    def draw_box(self, img_src, box, conf, cls_name, lw, sf, tf):
        color = self.color[cls_name]
        label = f'{cls_name} {conf}'
        p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
        # 绘制矩形框
        cv2.rectangle(img_src, p1, p2, color, thickness=lw, lineType=cv2.LINE_AA)
        # text width, height
        w, h = cv2.getTextSize(label, 0, fontScale=sf, thickness=tf)[0]
        # label fits outside box
        outside = box[1] - h - 3 >= 0
        p2 = p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3
        # 绘制矩形框填充
        cv2.rectangle(img_src, p1, p2, color, -1, cv2.LINE_AA)
        # 绘制标签
        cv2.putText(img_src, label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2),
                    0, sf, self.color["font"], thickness=2, lineType=cv2.LINE_AA)

    @staticmethod
    def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), scaleup=True, stride=32):
        # Resize and pad image while meeting stride-multiple constraints
        shape = im.shape[:2]  # current shape [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not scaleup:  # only scale down, do not scale up (for better val mAP)
            r = min(r, 1.0)

        # Compute padding
        ratio = r, r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
        # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
        return im, ratio, (dw, dh)

    def precess_image(self, img_src, img_size, half, device):
        # Padded resize
        img = self.letterbox(img_src, img_size)[0]
        # Convert
        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(device)

        img = img.half() if half else img.float()  # uint8 to fp16/32
        img = img / 255  # 0 - 255 to 0.0 - 1.0
        if len(img.shape) == 3:
            img = img[None]  # expand for batch dim
        return img



model = YOLOV8DetectionInfer(MODEL_PATH, GPU_ID, 0.45, 0.45)
app = Flask(__name__)

@app.route('/yolov8_test', methods=['POST'])
def detect():
    #  日志记录
    alarm_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    sp = alarm_time.split(' ')
    log_dir = './logs/yolov8_test/'
    log_path = os.path.join(log_dir, "info", sp[0])
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    headers_path = os.path.join(log_dir, "requests", sp[0])
    if not os.path.exists(headers_path):
        os.makedirs(headers_path, exist_ok=True)
    detect_result = []
    try:
        start_time = time.time()
        log_str = ''
        #  开始检测
        a = request.files
        for i in request.files:
            bytes_image = request.files[i].read()
            bi_image = io.BytesIO(bytes_image)
            img = Image.open(bi_image)
            img = np.array(img)
            detect_res = model.infer(img)
            scales=1
            for one in detect_res:
                one_result = {'name': model.names[int(one[5])], 'score': float(one[4]), 'x': int(one[0] / scales),
                              'y': int(one[1] / scales),
                              'width': int((one[2] - one[0]) / scales),
                              'height': int((one[3] - one[1]) / scales)}
                detect_result.append(one_result)

    except Exception as e:
        print(e)

    print(detect_result)
    return json.dumps(detect_result)



if __name__ == '__main__':
    app.run('0.0.0.0', port=23777)

    # save_path = "./runs"
    #
    # if not os.path.exists(save_path):
    #     os.mkdir(save_path)
    #
    #
    # img_path = r"/Users/wshuo/Downloads/ren1.jpeg"
    # model.infer(img_path)
