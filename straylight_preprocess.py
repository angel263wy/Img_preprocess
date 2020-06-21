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

# 每次成像的枚举类型
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
    sat_dk80 = 29
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
每个通道文件逐像元求均值 
'''
def aperture_process(sl_path, aperture_queue, raw_width, raw_height):
    
    os.chdir(sl_path)
    # 队列非空 进行处理
    while aperture_queue.qsize() :
        # 第一部分 导入文件夹 判断文件夹数量
        raw_path = aperture_queue.get()  # 杂光光阑编号 例如5-5 或者 1-4                 
        img_folder = glob.glob(raw_path + '\\*')  # 获取一个光阑下的所有文件夹 存储31个文件夹
        if len(img_folder) == 31 :
            print('光阑编号' + raw_path + '  文件夹数量' + str(len(img_folder))+ '  数量正确')
        else:
            print('光阑编号' + raw_path + '  文件夹数量' + str(len(img_folder)) + '  不满足要求')
            return
        
        
        # 第二部分 处理当前光阑文件夹下图像
        # 1.判断文件数量合理性
        err = False
        for img_dir in img_folder:
            fnames = glob.glob(img_dir + '\\RAW_ImageData\\*.raw')
            if (len(fnames) != 29) and (len(fnames) != 59):
                print('文件夹 ' + img_dir + ' 文件数量' + str(len(fnames)) + ' 不正确')
                err = True
        if err:
            return   
                
        # 2.处理最后一层文件夹  img_folder即31个文件夹的列表
        for img_seq, raw_folder in enumerate(img_folder) :
            filelist = glob.glob(raw_folder + '\\RAW_ImageData\\*.raw')
            
            # 读入所有文件
            raw_data = np.empty([len(filelist), raw_width*raw_height], dtype=np.uint16)
            for i, filename in enumerate(filelist):
                raw_data[i] = np.fromfile(filename, dtype=np.uint16)
            # 求平均值
            img_mean = np.mean(raw_data, axis=0)
            
            # 输出  raw_path例如4-3 
            fout = 'aperture__' + raw_path + '_' + enum_Img_Sequence(img_seq).name + '.raw'
            current_cwd = os.getcwd()  # 获取当前路径 保存现场
            fout_path = sl_path + '\\img_mean'   # 生成文件保存的路径       
            if not os.path.exists(fout_path): # 文件夹不存在则创建
                os.mkdir(fout_path)
            os.chdir(fout_path)  # 进入文件保存的路径         
            raw_file_output(fout, img_mean)
            os.chdir(current_cwd)  # 恢复现场
            print('out  ' + fout)

if __name__ == "__main__":
    raw_width = 1024
    raw_height = 1030
    stray_light_path = 'e:\\sl\\'
    os.chdir(stray_light_path)
    raw_dir = glob.glob('*')
    
    aperture_queue = Queue()  # 光阑队列 进入队列的为每个光阑的文件夹名称
    for dirs in raw_dir :
        aperture_queue.put(dirs)
    
    # aperture_process(stray_light_path, aperture_queue, raw_width, raw_height)   
    
    p1 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p2 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p3 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))

    p_l = [p1, p2, p3]
    for p in p_l:
        p.start()

    for p in p_l:
        p.join()
    
    print('end')
    






