# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/06/21
# Description :  杂光实时处理软件
# 针对每个通道 线性区 饱和区的图像求平均，判断最大DN值


import numpy as np
import os
import glob
import struct
from enum import Enum,unique
from multiprocessing import Process, Queue

@unique
class enum_Img_Sequence(Enum):
    lin_490P1 = 0
    sat_490P1 = 1
    lin_490P2 = 2
    sat_490P2 = 3
    lin_490P3 = 4
    sat_490P3 = 5
    lin_565 = 6
    sat_565 = 7
    lin_670P1 = 8
    sat_670P1 = 9
    lin_670P2 = 10
    sat_670P2 = 11
    lin_670P3 = 12
    sat_670P3 = 13
    lin_763 = 14
    sat_763 = 15
    lin_765 = 16
    sat_765 = 17
    lin_865P1 = 18
    sat_865P1 = 19
    lin_865P2 = 20
    sat_865P2 = 21
    lin_865P3 = 22
    sat_865P3 = 23
    lin_443 = 24
    sat_443 = 25
    lin_910 = 26
    sat_910 = 27
    lin_dk20 = 28
    sat_dk30 = 29
    lin_dk1000 = 30


def raw_file_output(fname, raw_data):
    with open(fname, 'wb') as f:
        raw_data[raw_data < 0] = 0  # 除去负数
        raw_data[raw_data > 65535] = 65535  # 除去负数
        for i in raw_data.flat:            
            foo = struct.pack('H', int(i))
            f.write(foo)

'''
单个光阑处理函数
读入光阑文件文件夹 检查文件夹内目录数量 检查每个通道文件数量
每个通道文件逐像元求均值 输出最大均值 
'''
def aperture_process(sl_path, aperture_queue, raw_width, raw_height):
    os.chdir(sl_path)
    raw_path = aperture_queue.get()                 
    img_folder = glob.glob(raw_path + '\\*')  # 获取一个光阑下的所有文件夹
    if len(img_folder) == 31 :
        print('光阑编号' + raw_path + '  文件夹数量' + str(len(img_folder))+ '  数量正确')
    else:
        print('光阑编号' + raw_path + '  文件夹数量' + str(len(img_folder)) + '  不满足要求')
        return
    
    # 处理当前光阑文件夹下图像
    img_process(sl_path, img_folder, raw_width, raw_height)  
    
'''
一个光阑状态下所有文件的处理
输入 31个文件夹名称的列表
处理 判断文件夹内容
'''
def img_process(sl_path, img_dirs, raw_width, raw_height):
    os.chdir(sl_path)

    # 判断文件数量合理性
    err = False
    for img_dir in img_dirs:
        fnames = glob.glob(img_dir + '\\RAW_ImageData\\*.raw')
        if (len(fnames) != 29) and (len(fnames) != 59):
            print('文件夹 ' + img_dir + ' 文件数量' + str(len(fnames)) + ' 不正确')
            err = True
    if err:
        return

    # 处理最后一层文件夹 
    for img_seq, raw_folder in enumerate(img_dirs) :
        filelist = glob.glob(raw_folder + '\\RAW_ImageData\\*.raw')
        
        # 读入所有文件
        raw_data = np.empty([len(filelist), raw_width*raw_height], dtype=np.uint16)
        for i, filename in enumerate(filelist):
            raw_data[i] = np.fromfile(filename, dtype=np.uint16)
        # 求平均值
        img_mean = np.mean(raw_data, axis=0)
        # 输出
        # fout = 'aperture__' + raw_folder + '_' + enum_Img_Sequence(img_seq).name + '.raw'
        # print('out  ' + fout)
        
    print('ok')
    

    

if __name__ == "__main__":
    raw_width = 1024
    raw_height = 1030
    stray_light_path = 'e:\\sl\\'
    os.chdir(stray_light_path)
    raw_dir = glob.glob('*')
    
    aperture_queue = Queue()  # 光阑队列 进入队列的为每个光阑的文件夹名称
    for dirs in raw_dir :
        aperture_queue.put(dirs)
    
    aperture_process(stray_light_path, aperture_queue, raw_width, raw_height)    
    print('end')
    






