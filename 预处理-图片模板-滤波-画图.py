# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/05/03
# Description : 1M30图片预处理 生成模板 均值滤波 画图


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import struct
import cv2

def raw_file_output(fname, raw_data):
    with open(fname, 'wb') as f:
        raw_data[raw_data < 0] = 0  # 除去负数
        for i in raw_data.flat:          
            foo = struct.pack('H', int(i))
            f.write(foo)
            
img1 = np.fromfile('1len.raw', dtype=np.uint16)  # 增加偏振片的图像
img2 = np.fromfile('2nolen.raw', dtype=np.uint16)  # 未加偏振片的图像 
img1[img1 < 10] = 0 # 扣除本底
img1[img1 > 230] = 218 # 扣除亮点
img1[img1 > 0] = 1  # 生成模板
img3 = img2 * img1  # 逐像元相乘 增加滤光片的区域被保留 滤光片外的区域置零 DN值变为无效
raw_file_output('temp.raw', img3)

# 图像相除 得到相对透过率
img1 = np.fromfile('1len.raw', dtype=np.uint16)
img2 = np.fromfile('temp.raw', dtype=np.uint16)
img2[img2 == 0] = 1  # 避免除零错误
img3 = (img1 / img2) * 100000
raw_file_output('temp.raw', img3)
print('end')

# 均值滤波 画图
cmap = cm.jet  # jet样式 数值大的红色 数字小的蓝色
img = np.fromfile('div-12.raw', dtype=np.uint16)
img = np.reshape(img, (400, 400))
img = cv2.blur(img, (25, 25))  # 均值滤波 选择该像素附件25X25像素求平均值作为该数值
imax = np.max(img)
img = img / imax  # 均值滤波后归一化到0~1范围内，最大值为1，其余值为与最大值之比
plt.imshow(img, clim=(0.9, 1), cmap=cmap)  # 仅显示0.9~1.0的范围
plt.colorbar()
plt.show()



