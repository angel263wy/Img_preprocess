'''
单幅图片光斑检测工具
'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import struct
import cv2
import os
import glob

import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['font.serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False 

def raw_file_output(fname, raw_data):
    with open(fname, 'wb') as f:
        raw_data[raw_data < 0] = 0  # 除去负数
        raw_data[raw_data > 65535] = 65535  # 除去负数
        for i in raw_data.flat:            
            foo = struct.pack('H', int(i))
            f.write(foo)

'''
计算重心函数
'''
def cal_center_gravity(img):        
    # 获取宽度和高度 计算坐标矩阵 及矩阵中每个元素坐标值与元素数值一致        
    height, width = img.shape
    x = np.arange(0, width)
    y = np.arange(0, height)
    #mx和my均为(heigt,width)矩阵 
    # y每行均为0,1,2...width mx第0行全0,第1行全1,第2行全2...最后一行全为height 
    my, mx = np.meshgrid(x,y)  
    # 计算重心 DN值乘以坐标值的累加和 / 全图像DN值累加和
    img_sum = np.sum(img)
    if img_sum == 0:
        cenx = 0
        ceny = 0
    else:                
        cenx = np.sum(img * mx) / np.sum(img)
        ceny = np.sum(img * my) / np.sum(img)
    
    return cenx, ceny

# 以下参数修改
fname = '1.raw'
raw_width = 512
raw_height = 380
light_spot_size = int(100 / 2)  # 光斑尺寸
ratio = 0.5 # 0.5表示当图像灰度值大于最大值X0.5时，认为光斑有效
dn_size = 1 # 1表示重心坐标3×3像素灰度值求平均


raw_data = np.fromfile(fname, dtype=np.uint16)
raw_data = np.reshape(raw_data, (raw_height, raw_width))
threhold = ratio * np.max(raw_data)
# 二值图像threshold函数 THRESH_BINARY指大于threhold用1表示
retval, foo_raw	= cv2.threshold(raw_data, threhold, 1, cv2.THRESH_BINARY)
foo_raw = foo_raw.astype(np.uint8)  # 二值化后转8位图像
# 寻找边沿函数 RETR_EXTERNAL指仅找外边沿 CHAIN_APPROX_SIMPLE指简化返回坐标
contours, hierarchy	= cv2.findContours(foo_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for i in range(len(contours)):
    # 获取光斑坐标    
    y = contours[i][0][0][0]
    x = contours[i][0][0][1]
    
    # 构造光斑区域范围  注意保护边沿视场 注意切片左闭右开
    x_start = 0 if (x-light_spot_size)<0 else x-light_spot_size 
    y_start = 0 if (y-light_spot_size)<0 else y-light_spot_size 
    x_end = raw_height if (x+light_spot_size)>=raw_height else x+light_spot_size+1
    y_end = raw_width if (y+light_spot_size)>=raw_width else y+light_spot_size+1
    # 构造掩膜图 光斑区域内为1 光斑区域外为0
    mask_img = np.zeros((raw_height, raw_width))
    mask_img[x_start:x_end+1, y_start:y_end+1] = 1
    light_spot_img = raw_data * mask_img
    
    # 扣掉残留本底 否则边沿光斑计算出现问题
    foo_th = 0.1 * np.max(light_spot_img)
    light_spot_img[light_spot_img < foo_th] = 0
    
    cenx,ceny = cal_center_gravity(light_spot_img)
    light_spot_dn = np.mean(raw_data[int(cenx-dn_size):int(cenx+dn_size+1),\
                                        int(ceny-dn_size):int(ceny+dn_size+1)])
    
    print(i,cenx,ceny, light_spot_dn)
    
    

print('ok')


