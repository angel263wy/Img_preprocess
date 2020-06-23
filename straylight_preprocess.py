# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/06/21
# Description :  杂光实时处理软件
# 针对每个通道 线性区 饱和区的图像求平均，判断最大DN值
'''
输入参数 main中前几行  图像宽高 拼图阈值 杂光目录
    raw_width = 1024
    raw_height = 1030
    dn_threhold_ratio = 0.85  # 拼图用的二值化 比例 即最大值的百分比作为阈值 小于该值的为0
    stray_light_path = 'f:\\sl\\'   # 杂光目录 里面应该全是5,5  3,34这类文件夹 没有其他文件夹
输出
    stray_light_path目录下新建了一个img_mean文件夹 里面有31个文件夹 对应31个状态 即14个通道线性区和饱和区 3个本底通道积分时间
    stray_light_path目录下新建了一个combine_img文件夹 用于存放拼图
'''

import numpy as np
import os
import glob
import struct
import time
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
    lin_dk80 = 29
    sat_dk1000 = 30


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
            
            if not os.path.exists(enum_Img_Sequence(img_seq).name):
                os.mkdir(enum_Img_Sequence(img_seq).name)
            os.chdir(enum_Img_Sequence(img_seq).name)
            raw_file_output(fout, img_mean)
            os.chdir(current_cwd)  # 恢复现场
            # print('out  ' + fout)
        # 第二部分结束
        
'''
拼图函数
导入文件后二值化，直接相加后输出
'''
def img_combine(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio):        
    # 队列非空 进行处理
    while band_queue.qsize() :
        band_name = band_queue.get()
        img_folder = stray_light_path + 'img_mean\\' + band_name
        # 文件夹跳转
        current_cwd = os.getcwd()  # 保护现场
        if not os.path.exists(img_folder):
            print('文件夹' + band_name + '不存在 该文件夹数据未处理')
            return
        os.chdir(img_folder)
        
        filelist = glob.glob('*.raw')
        if (len(filelist) < 2):
            print('文件夹' + band_name + '中图像数据少于2 该文件夹数据未处理')
            return
        # 读入所有文件  每读入一次进行二值化
        raw_data = np.empty([len(filelist), raw_width*raw_height], dtype=np.uint16)
        for i, filename in enumerate(filelist):
            foo_img = np.fromfile(filename, dtype=np.uint16)
            dn_threhold = dn_threhold_ratio * np.max(foo_img)
            foo_img[foo_img < dn_threhold] = 0
            raw_data[i] = foo_img
        
        img = np.sum(raw_data, axis=0)
        
        # 统一保存图片
        combine_folder = stray_light_path + 'combine_img'
        if not os.path.exists(combine_folder):
            os.mkdir(combine_folder)
        os.chdir(combine_folder)
        raw_file_output(band_name+'.raw', img)
                
        print(band_name)
        
        os.chdir(current_cwd)  # 恢复现场
    


if __name__ == "__main__":
    raw_width = 1024
    raw_height = 1030
    dn_threhold_ratio = 0.80  # 拼图用的二值化 比例 即最大值的百分比作为阈值 小于该值的为0
    stray_light_path = 'f:\\sl\\'
    os.chdir(stray_light_path)
    raw_dir = glob.glob('*')
    
    aperture_queue = Queue()  # 光阑队列 进入队列的为每个光阑的文件夹名称
    for dirs in raw_dir :
        if (dirs == 'combine_img') or (dirs == 'img_mean'):
            pass
        else:
            aperture_queue.put(dirs)
    
    
    # aperture_process(stray_light_path, aperture_queue, raw_width, raw_height)           
    
    p1 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p2 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p3 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p4 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p5 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))
    p6 = Process(target=aperture_process, args=(stray_light_path, aperture_queue, raw_width, raw_height))

    print(time.strftime('%Y%m%d-%H%M%S ', time.localtime(time.time())))
    # p_l = [p1, p2, p3]
    p_l = [p1, p2, p3, p4, p5, p6]
    for p in p_l:
        p.start()
    for p in p_l:
        p.join()
        
    # print(time.strftime('%Y%m%d-%H%M%S ', time.localtime(time.time())))
    print('aperture process end')
    
    band_queue = Queue()  # 31个文件夹队列
    for band in enum_Img_Sequence:
        band_queue.put(band.name)
    
    # img_combine(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio)
    
    q1 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    q2 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    q3 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    q4 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    q5 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    q6 = Process(target=img_combine, args=(stray_light_path, band_queue, raw_width, raw_height, dn_threhold_ratio))
    
    q_l = [q1, q2, q3, q4, q5, q6]
    for q in q_l:
        q.start()
    for q in q_l:
        q.join()
    
    
    print(time.strftime('%Y%m%d-%H%M%S ', time.localtime(time.time())))
    print('end')
    






