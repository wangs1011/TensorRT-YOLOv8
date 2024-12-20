#include "postprocess.h"

// ------------------ transpose --------------------
__global__ void transpose_kernel(float* src, float* dst, int numBboxes, int numElements, int edge){
    int position = blockDim.x * blockIdx.x + threadIdx.x;
    if (position >= edge) return;

    dst[position] = src[(position % numElements) * numBboxes + position / numElements];
}


void transpose(float* src, float* dst, int numBboxes, int numElements){
    int edge = numBboxes * numElements;
    int blockSize = 256;
    int gridSize = (edge + blockSize - 1) / blockSize;
    transpose_kernel<<<gridSize, blockSize>>>(src, dst, numBboxes, numElements, edge);
}


// ------------------ decode ( get class and conf ) --------------------
__global__ void decode_kernel(float* src, float* dst, int numBboxes, int numClasses, int numMasks, float confThresh, int maxObjects, int numBoxElement){
    int position = blockDim.x * blockIdx.x + threadIdx.x;
    if (position >= numBboxes) return;

    float* pitem = src + (4 + numClasses + numMasks) * position;
    float* classConf = pitem + 4;
    float confidence = 0;
    int label = 0;
    for (int i = 0; i < numClasses; i++){
        if (classConf[i] > confidence){
            confidence = classConf[i];
            label = i;
        }
    }

    if (confidence < confThresh) return;

    int index = (int)atomicAdd(dst, 1);
    if (index >= maxObjects) return;

    float cx     = pitem[0];
    float cy     = pitem[1];
    float width  = pitem[2];
    float height = pitem[3];

    float left   = cx - width * 0.5f;
    float top    = cy - height * 0.5f;
    float right  = cx + width * 0.5f;
    float bottom = cy + height * 0.5f;

    float* pout_item = dst + 1 + index * numBoxElement;
    pout_item[0] = left;
    pout_item[1] = top;
    pout_item[2] = right;
    pout_item[3] = bottom;
    pout_item[4] = confidence;
    pout_item[5] = label;
    pout_item[6] = 1;  // 1 = keep, 0 = ignore
    for (int j = 0; j < numMasks; j++){
        pout_item[7 + j] = pitem[4 + numClasses + j];
    }
}


void decode(float* src, float* dst, int numBboxes, int numClasses, int numMasks, float confThresh, int maxObjects, int numBoxElement){
    cudaMemset(dst, 0, sizeof(int));
    int blockSize = 256;
    int gridSize = (numBboxes + blockSize - 1) / blockSize;
    decode_kernel<<<gridSize, blockSize>>>(src, dst, numBboxes, numClasses, numMasks, confThresh, maxObjects, numBoxElement);
}


// ------------------ nms --------------------
__device__ float box_iou(
    float aleft, float atop, float aright, float abottom, 
    float bleft, float btop, float bright, float bbottom
){
    float cleft = max(aleft, bleft);
    float ctop = max(atop, btop);
    float cright = min(aright, bright);
    float cbottom = min(abottom, bbottom);

    float c_area = max(cright - cleft, 0.0f) * max(cbottom - ctop, 0.0f);
    if (c_area == 0.0f) return 0.0f;

    float a_area = max(0.0f, aright - aleft) * max(0.0f, abottom - atop);
    float b_area = max(0.0f, bright - bleft) * max(0.0f, bbottom - btop);
    return c_area / (a_area + b_area - c_area);
}


__global__ void nms_kernel(float* data, float kNmsThresh, int maxObjects, int numBoxElement){
    int position = blockDim.x * blockIdx.x + threadIdx.x;
    int count = min((int)data[0], maxObjects);
    if (position >= count) return;

    // left, top, right, bottom, confidence, class, keepflag
    float* pcurrent = data + 1 + position * numBoxElement;
    float* pitem;
    for (int i = 0; i < count; i++){
        pitem = data + 1 + i * numBoxElement;
        if (i == position || pcurrent[5] != pitem[5]) continue;

        if (pitem[4] >= pcurrent[4]){
            if (pitem[4] == pcurrent[4] && i < position) continue;

            float iou = box_iou(
                pcurrent[0], pcurrent[1], pcurrent[2], pcurrent[3],
                pitem[0], pitem[1], pitem[2], pitem[3]
            );

            if (iou > kNmsThresh){
                pcurrent[6] = 0;  // 1 = keep, 0 = ignore
                return;
            }
        }
    }
}


void nms(float* data, float kNmsThresh, int maxObjects, int numBoxElement){
    int blockSize = maxObjects < 256?maxObjects:256;
    int gridSize = (maxObjects + blockSize - 1) / blockSize;
    nms_kernel<<<gridSize, blockSize>>>(data, kNmsThresh, maxObjects, numBoxElement);
}


// ------------------ process mask --------------------
__device__ float sigmoid(float data){
    return 1.0f / (1.0f + expf(-data));
}

__global__ void process_mask_cuda_kernel(float* proto, float* maskCoef, float* mask, int protoC, int maskSize){
    int position = blockDim.x * blockIdx.x + threadIdx.x;
    if (position >= maskSize) return;

    float sum = 0;
    for (int i = 0; i < protoC; i++){
        sum += maskCoef[i] * proto[position + maskSize * i];
    }
    mask[position] = sigmoid(sum);
}

void process_mask_cuda(float* protoDevice, float* maskCoefDevice, float* maskDevice, int protoC, int protoH, int protoW){
    int maskSize = protoH * protoW;
    int blockSize = 256;
    int gridSize = (maskSize + blockSize - 1) / blockSize;
    process_mask_cuda_kernel<<<gridSize, blockSize>>>(protoDevice, maskCoefDevice, maskDevice, protoC, maskSize);
}


// ------------------ crop mask --------------------
__global__ void crop_mask_kernel(float* mask, float* bbox, int maskH, int maskW){
    int ix = threadIdx.x + blockIdx.x * blockDim.x;
    int iy = threadIdx.y + blockIdx.y * blockDim.y;
    int idx = ix + iy * maskW;

    if (ix < maskW && iy < maskH){
        if (ix < bbox[0] || ix > bbox[2] || iy < bbox[1] || iy > bbox[3]){
            mask[idx] = 0.0f;
        }
    }

}

void crop_mask(float* maskDevice, float* downBboxDevice, int maskH, int maskW){
    dim3 blockSize(32, 32);
    dim3 gridSize((maskW + blockSize.x - 1) / blockSize.x, (maskH + blockSize.y - 1) / blockSize.y);
    crop_mask_kernel<<<gridSize, blockSize>>>(maskDevice, downBboxDevice, maskH, maskW);
}


// ------------------ cut mask --------------------
__global__ void cut_mask_kernel(float* mask, float* cutMask, int cutMaskTop, int cutMaskLeft, int cutMaskH, int cutMaskW, int maskW){
    int ix = threadIdx.x + blockIdx.x * blockDim.x;
    int iy = threadIdx.y + blockIdx.y * blockDim.y;
    int idx = ix + iy * cutMaskW;

    if (ix >= cutMaskW || iy >= cutMaskH) return;

    int mask_ix = ix + cutMaskLeft;
    int mask_iy = iy + cutMaskTop;
    int mask_idx = mask_ix + mask_iy * maskW;

    cutMask[idx] = mask[mask_idx];
}

void cut_mask(float* maskDevice, float* cutMaskDevice, int cutMaskTop, int cutMaskLeft, int cutMaskH, int cutMaskW, int maskW){
    dim3 blockSize(32, 32);
    dim3 gridSize((cutMaskW + blockSize.x - 1) / blockSize.x, (cutMaskH + blockSize.y - 1) / blockSize.y);
    cut_mask_kernel<<<gridSize, blockSize>>>(maskDevice, cutMaskDevice, cutMaskTop, cutMaskLeft, cutMaskH, cutMaskW, maskW);
}


// ------------------ bilinear resize mask --------------------
__global__ void resize_kernel(float* srcMask, int srcMaskH, int srcMaskW, float* dstMask, int dstMaskH, int dstMaskW){
    int ix = threadIdx.x + blockIdx.x * blockDim.x;
    int iy = threadIdx.y + blockIdx.y * blockDim.y;
    int idx = ix + iy * dstMaskW;

    if (ix >= dstMaskW || iy >= dstMaskH) return;

    float scaleY = (float)dstMaskH / (float)srcMaskH;
    float scaleX = (float)dstMaskW / (float)srcMaskW;

    // (ix,iy)为目标图像坐标
    // (before_x,before_y)为原图坐标
    float beforeX = float(ix + 0.5) / scaleX - 0.5;
    float beforeY = float(iy + 0.5) / scaleY - 0.5;
    // 原图像坐标四个相邻点
    // 获得变换前最近的四个顶点,取整
    int topY = static_cast<int>(beforeY);
    int bottomY = topY + 1;
    int leftX = static_cast<int>(beforeX);
    int rightX = leftX + 1;
    //计算变换前坐标的小数部分
    float u = beforeX - leftX;
    float v = beforeY - topY;

    if (topY >= srcMaskH - 1){  // 对应原图的坐标位于最后一行
        topY = srcMaskH - 1;
        bottomY = srcMaskH - 1;
    }
    if (leftX >= srcMaskW - 1){  // 对应原图的坐标位于最后一列
        leftX = srcMaskW - 1;
        rightX = srcMaskW - 1;
    }

    dstMask[idx] = (1. - u) * (1. - v) * srcMask[leftX + topY * srcMaskW]
                 + (u) * (1. - v) * srcMask[rightX + topY * srcMaskW]
                 + (1. - u) * (v) * srcMask[leftX + bottomY * srcMaskW]
                 + u * v * srcMask[rightX + bottomY * srcMaskW];
            
}

void resize(float* srcMaskDevice, int srcMaskH, int srcMaskW, float* dstMaskDevice, int dstMaskH, int dstMaskW){
    dim3 blockSize(32, 32);
    dim3 gridSize((dstMaskW + blockSize.x - 1) / blockSize.x, (dstMaskH + blockSize.y - 1) / blockSize.y);
    resize_kernel<<<gridSize, blockSize>>>(srcMaskDevice, srcMaskH, srcMaskW, dstMaskDevice, dstMaskH, dstMaskW);
}
