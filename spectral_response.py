# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/06/30
# Description : 光谱响应函数

'''
输入参数 main中前几行  图像宽高  起始波长点 当前波段名称 目录明显
    Start_wavelength = 418  # 起始波长
    channel_name = '443'  # 当前通道号或波段名称
    spectral_path = 'e:\\sl\\443'  # 表示某个波段的目录 目录内每个文件夹表示一个波段
输出
    波长内所有文件求平均 在spectral_path目录内新建result_folder
'''

import numpy as np
import os
import glob
import struct
import time
from multiprocessing import Process, Queue


def raw_file_output(fname, raw_data):
    with open(fname, 'wb') as f:
        raw_data[raw_data < 0] = 0  # 除去负数
        raw_data[raw_data > 65535] = 65535  # 除去负数
        for i in raw_data.flat:            
            foo = struct.pack('H', int(i))
            f.write(foo)

'''
波长处理函数
读入每个波长点文件夹 每个通道文件逐像元求均值后输出
'''
def spectrum_process(s_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name):
    os.chdir(s_path)
    # 队列非空 进行处理
    while wavelength_queue.qsize() :
        #  读入文件夹字典
        raw_path_dict = wavelength_queue.get()
        current_wavelength = str(raw_path_dict['wavelength_num'] + Start_wavelength)  # 获取当前波长点
        current_wavelength_path = raw_path_dict['wavelength_dir']  # 获取波长点的文件夹路径
        
        filelist = glob.glob(current_wavelength_path + '\\RAW_ImageData\\*.raw')  # 获得该波长点文件夹下所有文件
        if len(filelist) < 2 :
            print(current_wavelength_path + '文件夹下文件小于2 不进行处理')
            continue  # while本次循环在此处结束
        
        # 读入所有文件
        raw_data = np.empty([len(filelist), raw_width*raw_height], dtype=np.uint16)
        for i, filename in enumerate(filelist):
            raw_data[i] = np.fromfile(filename, dtype=np.uint16)
        # 求平均值
        img_mean = np.mean(raw_data, axis=0)
        
        # 输出
        fout = 'Spectral_Response-'+ channel_name + '-' + current_wavelength + '.raw'
        current_cwd = os.getcwd()  # 获取当前路径 保存现场
        fout_path = s_path + '\\result_folder'   # 生成文件保存的路径       
        if not os.path.exists(fout_path): # 文件夹不存在则创建
            os.mkdir(fout_path)
        os.chdir(fout_path)  # 进入文件保存的路径
        raw_file_output(fout, img_mean)
        os.chdir(current_cwd)  # 恢复现场
        print(current_wavelength + '波长点文件输出')
        



if __name__ == "__main__":
    raw_width = 1024
    raw_height = 1030    
    Start_wavelength = 418  # 起始波长
    channel_name = '443'  # 当前通道号或波段号
    spectral_path = 'e:\\sl\\443'  # 表示某个波段的目录 目录内每个文件夹表示一个波段
    
    os.chdir(spectral_path)
    
    raw_dir = glob.glob('*')
    
    wavelength_queue = Queue()  # 波长队列 进入队列的为每个波长点的文件夹名称
    for cnt,dirs in enumerate(raw_dir) :
        wavelength_dir_dict = {'wavelength_num':cnt, 'wavelength_dir':dirs}  # 将波长顺序与目录匹配 用于生成波长相关文件
        wavelength_queue.put(wavelength_dir_dict)
    
    p1 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))
    p2 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))
    p3 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))
    # p4 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))
    # p5 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))
    # p6 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name))

    print(time.strftime('%Y-%m-%d-%H:%M:%S ', time.localtime(time.time())))
    p_l = [p1, p2, p3]
    # p_l = [p1, p2, p3, p4, p5, p6]
    for p in p_l:
        p.start()
    for p in p_l:
        p.join()
        
        
    print(time.strftime('%Y-%m-%d-%H:%M:%S ', time.localtime(time.time())))
    print('end')