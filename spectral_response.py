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
import pandas as pd
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
读入每个波长点文件夹 每个通道文件逐像元求均值后输出 获取最大值放入队列

输入： s_path 某波段文件夹的目录 内含所有波长点的文件夹
wavelength_queue 波长文件夹的目录队列 用于获取
raw_width，raw_height 图像尺寸
Start_wavelength 该波段起始波长点 用于将文件夹拆分为波段
channel_name 当前通道号 
wavelength_maxDN_queue 该波长点图像逐像元平均后 最大灰度值队列 
'''
def spectrum_process(s_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name, wavelength_maxDN_queue):
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
        # 产生波长及最大灰度值字典并放入队列 
        img_maxdn_dict = {'wavelength':current_wavelength, 'max_dn':np.max(img_mean)}
        wavelength_maxDN_queue.put(img_maxdn_dict) 
        
        
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
        
    else: # 队列已空 处理完毕 将none传入最大值队列 结束最大值处理
        wavelength_maxDN_queue.put(None)


'''
波长最大值处理函数
输入：通道名称 波长最大值队列
处理： 死循环获取队列元素 形成pd 直到读到表示none的结束符 循环结束后输出
'''
def wavelength_maxDN(channel_name, wavelength_maxDN_queue):
    # 处理最大灰度值队列
    wavelength_maxDN_df = pd.DataFrame()
    while True:
        max_dict = wavelength_maxDN_queue.get()
        
        if max_dict == None:  # 处理完成标志 
            break   
        # 将字典转df后拼接
        foo_df = pd.DataFrame(max_dict, index=[0], columns=['wavelength', 'max_dn'])
        wavelength_maxDN_df = pd.concat([wavelength_maxDN_df, foo_df], axis=0)
    
    # 排序后输出
    wavelength_maxDN_df.sort_values(by=['wavelength'], ascending=True, inplace=True)
    now = time.strftime('%Y%m%d%H%M%S-', time.localtime(time.time()))
    fout = now + channel_name + '_max_dn.csv'
    wavelength_maxDN_df.to_csv(fout, header=True, index=True, encoding='gbk')  
    print('图像最大值统计文件输出 文件名为' + fout) 
        

if __name__ == "__main__":
    raw_width = 1024
    raw_height = 1030    
    Start_wavelength = 418  # 起始波长
    channel_name = '443'  # 当前通道号或波段号
    spectral_path = 'e:\\sl\\443'  # 表示某个波段的目录 目录内每个文件夹表示一个波段
    
    os.chdir(spectral_path)
    
    raw_dir = glob.glob('*')
    
    wavelength_maxDN_queue = Queue()  # 单波长图像全图最大灰度值队列 给各进程保存用 最后统一输出
    
    wavelength_queue = Queue()  # 波长队列 进入队列的为每个波长点的文件夹名称
    for cnt,dirs in enumerate(raw_dir) :
        wavelength_dir_dict = {'wavelength_num':cnt, 'wavelength_dir':dirs}  # 将波长顺序与目录匹配 用于生成波长相关文件
        wavelength_queue.put(wavelength_dir_dict)
    
    p1 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name, wavelength_maxDN_queue))
    p2 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name, wavelength_maxDN_queue))
    p3 = Process(target=spectrum_process, args=(spectral_path, wavelength_queue, raw_width, raw_height, Start_wavelength, channel_name, wavelength_maxDN_queue))
    
    p4 = Process(target=wavelength_maxDN, args=(channel_name, wavelength_maxDN_queue))

    print(time.strftime('%Y-%m-%d-%H:%M:%S ', time.localtime(time.time())))
    p_l = [p1, p2, p3, p4]

    for p in p_l:
        p.start()
    for p in p_l:
        p.join()
        
        
    print(time.strftime('%Y-%m-%d-%H:%M:%S ', time.localtime(time.time())))
    print('end')