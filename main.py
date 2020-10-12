# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/03/25
# Description :


import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
# from PyQt5.uic import loadUi
from gui import Ui_Form

import time
import struct
import numpy as np
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import cv2
from enum import Enum,unique


import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['font.serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False 


@unique
class enum_DPC_band(Enum):
    band_490P1 = 0
    band_490P2 = 1
    band_490P3 = 2
    band_565 = 3
    band_670P1 = 4
    band_670P2 = 5
    band_670P3 = 6
    dark_ground = 7
    band_763 = 8
    band_765 = 9
    band_865P1 = 10
    band_865P2 = 11
    band_865P3 = 12
    band_443 = 13
    band_910 = 14


class Test(QWidget, Ui_Form):
    def __init__(self):
        super(Test, self).__init__()
        self.setupUi(self)
        # 自定义内部对象
        self.img_origin_mean_sig = np.empty(0)  # 图像求平均值后的数值
        self.img_dark_sig = np.empty(0)  # 存放多幅图求平均后的本底
        self.img_sub_dark_sig = np.empty(0)  # 扣本底后的图像
        self.img_final_sig = np.empty(0)  # 最终图像值


# ----------------响应和槽函数----------------

    def click_log_clear(self):  # 清除日志界面
        self.textEdit_log.clear()

    # 图像处理 打开图像文件 求平均后保存和输出
    def click_openIMG_sig(self):
        try:
            # 读入图像的宽和高
            raw_width = self.spinBox_img_width.value()
            raw_height = self.spinBox_img_height.value()

            # 读入所有文件数据
            filelist, filt = QFileDialog.getOpenFileNames(
                self, filter='raw file(*.raw)', caption='打开图像文件')
            if len(filelist):  # 选择文件数大于0 则处理 否则不处理
                raw_data = np.empty(
                    [len(filelist), raw_width*raw_height], dtype=np.uint16)
                for i, filename in enumerate(filelist):
                    raw_data[i] = np.fromfile(filename, dtype=np.uint16)

                self.img_origin_mean_sig = np.mean(raw_data, axis=0)

                self.log_show('打开原始图像 共计' + str(len(filelist)) + '个文件')

                res = QMessageBox.question(
                    self, '图像平均完成，确认后续操作', '选是输出图像，选否暂不输出')

                if res == QMessageBox.Yes:
                    try:
                        filename, flt = QFileDialog.getSaveFileName(
                            self, filter='raw file(*.raw)', caption='图像输出')
                        self.raw_file_output(
                            filename, self.img_origin_mean_sig)
                        self.log_show('平均后的图像已输出 位于' + filename)
                    except Exception as ee:
                        self.log_show('未选择输出的文件名 平均后的图像未输出')
                        self.log_show('异常信息: '+ repr(ee))  
                else:
                    self.log_show('图像求平均后已缓存，未输出，可以进行后续操作')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e))  

    # 本底图像处理 打开本底文件后求平均 保存并输出
    def click_open_dark_sig(self):
        try:
            # 读入图像的宽和高
            raw_width = self.spinBox_img_width.value()
            raw_height = self.spinBox_img_height.value()

            # 读入所有文件数据
            filelist, filt = QFileDialog.getOpenFileNames(
                self, filter='raw file(*.raw)', caption='打开本底文件')
            if len(filelist):  # 选择文件数大于0 则处理 否则不处理
                raw_data = np.empty([len(filelist), raw_width*raw_height], dtype=np.uint16)
                for i, filename in enumerate(filelist):
                    raw_data[i] = np.fromfile(filename, dtype=np.uint16)

                self.img_dark_sig = np.mean(raw_data, axis=0)
                # 本底导入完成 使能扣本底按钮
                self.pushButton_sub_dark_sig.setEnabled(True)

                self.log_show('打开本底图像 共计' + str(len(filelist)) + '个文件')

                res = QMessageBox.question(
                    self, '本底平均完成，确认后续操作', '选是输出图像，选否暂不输出')

                if res == QMessageBox.Yes:
                    try:
                        filename, flt = QFileDialog.getSaveFileName(
                            self, filter='raw file(*.raw)', caption='本底图像输出')
                        self.raw_file_output(
                            filename, self.img_dark_sig)
                        self.log_show('平均后的本底图像已输出 位于' + filename)
                    except Exception as ee:
                        self.log_show('未选择输出的文件名 扣本底后图像未输出')
                        self.log_show('异常信息: '+ repr(ee))  
                else:
                    self.log_show('扣本底的图像已缓存，但未输出，可以继续完成其他操作')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e))  

    # 扣本底函数 
    def click_sub_dark_sig(self):
        # 图像非空判断 
        if (len(self.img_origin_mean_sig)) > 0 and (len(self.img_dark_sig) > 0):
            # 扣本底算法
            self.img_sub_dark_sig = self.img_origin_mean_sig - self.img_dark_sig
            # 扣除负数
            self.img_sub_dark_sig = np.clip(self.img_sub_dark_sig, 0, 65536)
            
            # 扣本底完成 确认操作
            res = QMessageBox.question(self, '扣本底工作完成，确认后续操作', '选是输出图像，选否暂不输出')
            self.pushButton_dis_smear.setEnabled(True) # 使能帧转移校正按钮
            
            if res == QMessageBox.Yes:
                try:
                    filename, flt = QFileDialog.getSaveFileName(
                        self, filter='raw file(*.raw)', caption='扣本底后图像输出')
                    self.raw_file_output(
                        filename, self.img_sub_dark_sig)
                    self.log_show('扣本底的图像已输出 位于' + filename)
                except Exception as ee:
                    self.log_show('未选择输出的文件名 扣本底后图像未输出')
                    self.log_show('异常信息: '+ repr(ee))  
            else:
                self.log_show('本底图像的平均值已缓存，但未输出，可以继续完成扣本底操作')
                            
        else:
            self.log_show('未导入图像')

    '''
    帧转移校正函数 
    算法：取最先转移的前N行，每列求平均，再用正常图像相同列减去平均值  
    注意：np中x表示列 y表示行
    '''    
    def click_dis_smear(self):
        # 图像非空判断        
        if len(self.img_sub_dark_sig) > 0: 
            # 扣完本底的图像 转二维矩阵 注意 X表示高 Y表示宽
            raw_width = self.spinBox_img_width.value()
            raw_height = self.spinBox_img_height.value()
            raw_data = np.array(self.img_sub_dark_sig).reshape(raw_height, raw_width)
            
            # 取暗行数据
            # 取N行时 直接用切片操作 对X进行操作取得N行 
            dark_line_start = self.spinBox_smear_start_line.value()
            dark_line_end = self.spinBox_smear_end_line.value()
            dark_lines = raw_data[dark_line_start:dark_line_end+1, :]
            # 求平均
            dark_lines_mean = np.mean(dark_lines, axis=0) 
            # 帧转移校正 按行扣暗行平均值 广播算法 矩阵每行减去向量 并扣除负值
            self.img_final_sig = np.clip(raw_data - dark_lines_mean, 0, 65530)
                        
            # 多维数组变一维 便于输出
            self.img_final_sig =  self.img_final_sig.flatten()            
            try:
                    filename, flt = QFileDialog.getSaveFileName(
                        self, filter='raw file(*.raw)', caption='帧转移校正后图像输出')
                    self.raw_file_output(filename, self.img_final_sig)
                    self.log_show('帧转移校正图像已输出 位于' + filename)
            except Exception as ee:
                self.log_show('未选择输出的文件名 帧转移校正的图像未输出')
                self.log_show('异常信息: '+ repr(ee))  
            
        else:
            self.log_show('未完成扣本底，不能进行帧转移校正')        
    
    '''
    1M30 扣本底和帧转移校正
    根据积分时间求逆矩阵 再计算
    可以一次进行多个1M30文件的帧转移校正
    输出文件在原文件后增加_dis_smearing
    '''
    def click_1M30dis_smear(self):
        # 扣本底 当无图像数据时返回
        if (len(self.img_origin_mean_sig)) <= 0 and (len(self.img_dark_sig) <= 0):
            self.log_show('未导入图像')
            return
        else:
            # 扣本底算法
            self.img_sub_dark_sig = self.img_origin_mean_sig - self.img_dark_sig
            # 扣除负数
            self.img_sub_dark_sig = np.clip(self.img_sub_dark_sig, 0, 65536)
        
        # 获取积分时间 界面中输入ms 需要转换为us
        integration_time = self.doubleSpinBox_integration.value() * 1000
        t = 1.3 / integration_time
        
        # 生成帧转移校正矩阵
        M = np.identity(1024)  # 生成单位矩阵
        for i in range(1024):  # i 表示行
            for j in range(1024):  # j 表示列
                if j < i:
                    M[i][j] = t

        M1 = np.linalg.inv(M)  # 求逆矩阵 图像与其点乘即可
        
        #帧转移校正
        raw_data = np.reshape(self.img_sub_dark_sig, (1024, 1024))
        img = np.dot(M1, raw_data)
        # 除去小于0的数据
        raw_dm = np.clip(img, 0, 4095)  
        # 文件输出
        f_out, filt = QFileDialog.getSaveFileName(self, filter='raw file(*.raw)', caption='保存校正后图像')
        if len(f_out) == 0:
            self.log_show('未选择文件')
        else:                
            with open(f_out, 'wb') as f:
                for i in raw_dm.flat:
                    foo = struct.pack('H', int(i))
                    f.write(foo)
                self.log_show('1M3O帧转移校正完成, 输出文件:' + f_out)


    '''
    速读图像DN值函数 
    1 打开文件后 读取图像区域 判断区域最大值、最小值和平均值
    2 计算重心
    
    1 根据选择情况计算重心
    2 找到重心坐标 进行nXn坐标求最大值最小值和平均值
    输出csv文件
    '''
    def click_openIMG_readDN(self):        
        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()
        
        #读入求重心的最大值和最小值
        g_max = self.spinBox_gravity_max.value()
        g_min = self.spinBox_gravity_min.value()
        
        # 读入平均值的区域
        mean_zone = self.spinBox_readDN_mean_window_size.value()
        
        # 存放全图最值和坐标
        whole_img_max = list()
        whole_img_max_X = list()
        whole_img_max_Y = list()
        zone_mean = list()  # 特征区域所有像元平均值
        # 存放重心区域最值和平均值数据
        max = list()
        min = list()
        mean = list()
        # 存放重心坐标
        center_gravity_X = list()
        center_gravity_Y = list()
        
        try:
            # 读入所有文件数据
            filelist, filt = QFileDialog.getOpenFileNames(self, filter='raw file(*.raw)', caption='打开图像文件')
            if len(filelist) == 0 :  # 选择文件数大于0 进行处理 否则不处理
                self.log_show('未选择文件')
                return                
            else:                
                # 每次读入一幅图像 即进行处理                
                for filename in filelist:
                    raw_data = np.fromfile(filename, dtype=np.uint16)
                    # 特别注意 reshape X为高 Y为宽 不能弄反
                    raw_data = np.reshape(raw_data, (raw_height, raw_width))
                    
                    # 数据清洗 在范围外的清零 避免影响重心计算
                    raw_data[raw_data < g_min] = 0
                    raw_data[raw_data > g_max] = 0
                    
                    # 计算全图最大值及坐标
                    whole_img_max.append(np.max(raw_data))                    
                    Xmax, Ymax= np.where(raw_data==np.max(raw_data))  # 坐标对计算重心也有用
                    whole_img_max_X.append(Xmax[0])
                    whole_img_max_Y.append(Ymax[0])
                    # 根据选择情况计算重心
                    if self.radioButton_readDN_max_sel.isChecked():
                        # 最大值附近求重心                        
                        max_window_size = self.spinBox_readDN_max_sel_window_size.value()

                        # 最大值附近区域范围挑选和保护  注意切片左闭右开
                        x_max_start = 0 if (Xmax[0]-max_window_size)<0 else Xmax[0]-max_window_size 
                        y_max_start = 0 if (Ymax[0]-max_window_size)<0 else Ymax[0]-max_window_size 
                        x_max_end = raw_height if (Xmax[0]+max_window_size)>=raw_height else Xmax[0]+max_window_size+1
                        y_max_end = raw_width if (Ymax[0]+max_window_size)>=raw_width else Ymax[0]+max_window_size+1
                        # 切片 窗口选取 求重心
                        img = raw_data[x_max_start:x_max_end, y_max_start:y_max_end]
                        xc, yc = self.cal_center_gravity(img)
                        #重心返回结果为相对值 需转为绝对坐标
                        xc = xc + x_max_start
                        yc = yc + y_max_start
                        
                    else:  # 手动选择区域求重心
                        # 读入图像区域窗口
                        startX = self.spinBox_startX_readdn.value()
                        startY = self.spinBox_startY_readdn.value()
                        endX = self.spinBox_endX_readdn.value()
                        endY = self.spinBox_endY_readdn.value()
                        # 切片 提取手动选择区域 按S3的行列输入的坐标 用NUMPY计算时需要对调
                        img = raw_data[startY:endY+1, startX:endX+1]
                        xc, yc = self.cal_center_gravity(img)
                        #重心返回结果为相对值 需转为绝对坐标
                        xc = xc + startY
                        yc = yc + startX
                    
                    # 求特征区域所有像素的平均值
                    zone_mean.append(round(np.mean(img),2))
                    
                    # 根据重心以及附近区域计算最值和平均值
                    x = int(round(xc))  # 取得重心整数坐标 四舍五入后取整 注round返回小数
                    y = int(round(yc))
                    # 范围挑选和保护
                    x_zone_start = 0 if (x-mean_zone)<0 else x-mean_zone                   
                    y_zone_start = 0 if (y-mean_zone)<0 else y-mean_zone
                    x_zone_end = raw_height if (x+mean_zone)>=raw_height else x+mean_zone+1
                    y_zone_end = raw_width  if (y+mean_zone)>=raw_width  else y+mean_zone+1
                    # 重心附近图像切片求最值和均值
                    tmp_img = raw_data[x_zone_start:x_zone_end, y_zone_start:y_zone_end]

                    # 保存最值 平均值 重心坐标
                    max.append(np.max(tmp_img))
                    min.append(np.min(tmp_img))
                    
                    mean.append(round(np.mean(tmp_img),2))  # 平均值保留两位小数                   
                    center_gravity_X.append(xc)
                    center_gravity_Y.append(yc)
                
                # 所有文件读完 数据保存
                # 创建dataframe用于输出 pd.Index函数用于生成从1开始的索引 
                res = pd.DataFrame({'文件名': filelist,
                                    '全图最大值': whole_img_max,
                                    '全图最大值坐标S3-X': whole_img_max_Y,
                                    '全图最大值坐标S3-Y': whole_img_max_X,
                                    '所选特征区域全像素均值': zone_mean,
                                    '光斑重心S3-X': center_gravity_Y,
                                    '光斑重心S3-Y': center_gravity_X,
                                    '重心区域最大值': max,
                                    '重心区域最小值': min,
                                    '重心区域平均值': mean
                                    }, columns=['文件名','全图最大值',
                                                '全图最大值坐标S3-X','全图最大值坐标S3-Y',
                                                '所选特征区域全像素均值','光斑重心S3-X','光斑重心S3-Y', 
                                                '重心区域最大值','重心区域最小值', 
                                                '重心区域平均值'],
                                    index=pd.Index(range(1, len(filelist)+1)))
                                
                self.log_show('处理图像 共计' + str(len(filelist)) + '个文件')
                
                # 输出文件
                outfile = 'Statistics-' + time.strftime('%Y%m%d%H%M%S.csv', time.localtime(time.time()))
                res.to_csv(outfile, header=True, encoding='gbk')
                os.system('start'+ ' ' + outfile)
                self.log_show('计算结果已输出 文件名为' + outfile)  
                                

        except Exception as e:
            self.log_show('处理过程出现异常')  
            self.log_show('异常信息: '+ repr(e))     
        
            
    '''
    图像裁剪函数
    读入起点和终点坐标 裁剪后显示和输出
    '''
    def click_img_cut(self):
        # 读入图像区域窗口
        startX = self.spinBox_cutX.value()
        startY = self.spinBox_cutY.value()
        endX = self.spinBox_cutX_end.value()
        endY = self.spinBox_cutY_end.value()

        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()
        
        # 裁剪尺寸合理性判断 不能超过图像的宽和高
        if startX >= endX :
            self.log_show('X坐标终点大于起点')
            return
        elif startY >= endY :
            self.log_show('Y坐标终点大于起点')
            return
        elif endX >= raw_width :
            self.log_show('X坐标终点大于图像尺寸')
            return
        elif endY >= raw_height :
            self.log_show('Y坐标终点大于图像尺寸')
            return
        
        try: 
            # 读入单幅图像
            filename, filt = QFileDialog.getOpenFileName(self, filter='raw file(*.raw)', caption='打开图像文件')
            if len(filename) == 0:
                self.log_show('未选择文件')
                return
            else:            
                # 读入图像 特别注意 reshape X为高 Y为宽 不能弄反            
                tmp = np.fromfile(filename, dtype=np.uint16)
                raw_data = np.reshape(tmp, (raw_height, raw_width))
                # 裁剪
                img = raw_data[startY:endY+1, startX:endX+1]
                # 显示
                plt.figure()
                plt.imshow(img, cmap='Greys_r') 
                plt.show() 
                # 输出
                fout = filename[:-4] + '_cut_x_'+str(startX)+'_y_'+str(startY)+'.raw'
                self.raw_file_output(fout, img)
                self.log_show('图像裁剪完成 输出文件 '+ fout)
        
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e)) 
    
    '''
    信噪比功能
    按照页面使用说明操作
    '''
    def click_snr_open(self):
        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()
        
        try:
            # 读入所有文件数据
            raw_dirs = QFileDialog.getExistingDirectory(self, caption='选择文件夹')
            
            # 先在所选目录中找文件
            filelist = glob.glob(raw_dirs + '\\*.raw')
            # 当前目录未找到图像文件 则在下级RAW_ImageData中找文件
            if len(filelist) == 0 :
                self.log_show(raw_dirs + '中没有图像文件,尝试在RAW_ImageData中寻找')
                filelist = glob.glob(raw_dirs + '\\RAW_ImageData\\*.raw')               
            # 未在RAW_ImageData找到文件 转手动选择
            if len(filelist) == 0 :
                self.log_show('没找到图像文件,转手动选择')
                res = QMessageBox.question(self, '请选择', '未找到RAW文件 是否手动选文件?')
                if res == QMessageBox.No:
                    self.log_show('未进行数据处理')
                    return
                else:                
                    raw_dirs = 'histogram'  # 改名用于csv文件中表头 不代表目录
                    filelist, filt = QFileDialog.getOpenFileNames(
                        self, filter='raw file(*.raw)', caption='打开图像文件') 
            else:  # 在RAW_ImageData中找到文件
                self.log_show('在RAW_ImageData文件夹中找到图像文件')             

                        
            # 计算单通道信噪比 选择一个文件夹自动读入数据 如果没有数据 则提示选择单个文件
            if self.radioButton_snr_one_channel.isChecked():
                # 读入文件数量判断 无论是选文件夹方式还是手选方式
                if len(filelist) < 3:
                    self.log_show('选择文件数量小于3，不能计算信噪比')
                    return     
                
                self.log_show('找到' + str(len(filelist)) + '个文件,正在处理...')
                                
                now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
                fout_raw = 'SNR-' + now + '.raw'
                # 计算信噪比并输出
                img = self.cal_snr(filelist, raw_width, raw_height)
                self.raw_file_output(fout_raw, img)
                self.log_show('信噪比计算完成,输出文件名：' + fout_raw)
                fout_csv = 'histogram-snr-' + now + '.csv'
                self.hist_plot(img)
                self.hist_save(img, fout_csv, raw_dirs)  # 将文件夹名称作为生成的csv首行
                os.system('start'+ ' ' + fout_csv)
                self.log_show('信噪比直方图文件：' + fout_csv)

            # 计算多通道信噪比    
            else:                 
                # 读入文件数量判断
                if (len(filelist)<45) and self.radioButton_snr_all_channel.isChecked():
                    self.log_show('选择文件数量小于45，不能计算信噪比')
                    return
                
                self.log_show('找到' + str(len(filelist)) + '个文件,正在处理...')
                
                # 记录当前时间 用作文件名
                now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) 
                
                hist_df = pd.DataFrame()  # 用于保存15个通道的直方图数值
                fwhm_df = pd.DataFrame()  # 用于保存直方图的半高宽信息
                
                # 第一层循环 ch_cnt表示图像序号 
                for ch_cnt in range(1, 16): 
                    img_file = list()  # 保存该通道的文件名
                    # 第二层循环 遍历所有文件 找出所有第i个通道的文件
                    for filename in filelist:  
                        # 生成含有该通道关键字的keyword 判断文件名是否含有该关键字
                        if filename[-6] == '_' :  # 兼容 _1.raw和 01.raw
                            keyword = '_' + str(ch_cnt) + '.raw'
                        else:
                            keyword = str(ch_cnt).zfill(2) + '.raw'
                        # 该文件名属于该通道 则加入文件名列表                        
                        if keyword in filename:
                            img_file.append(filename)
                    # 第二层循环结束 img_file中存放了所有第ch_cnt通道的图像地址 计算信噪比
                    if len(img_file) < 3 :
                        self.log_show('通道' + str(ch_cnt)+'文件数量小于3，不能计算信噪比')
                        continue
                    else:                        
                        fout_raw = 'SNR-CH' + str(ch_cnt).zfill(2) + '-' + now + '.raw'
                        df_header = 'Histogram-SNR-CH' + str(ch_cnt).zfill(2)
                        # 计算该通道信噪比
                        img = self.cal_snr(img_file, raw_width, raw_height)
                        # 取消以下两行注释 用于将信噪比文件输出
                        # self.raw_file_output(fout_raw, img)
                        # self.log_show('信噪比计算完成,输出文件名：' + fout_raw)
                        
                        # 对信噪比图像做直方图 并保存数据
                        img = img.astype(np.int32)
                        hist = np.bincount(img)
                        df_foo = pd.DataFrame({df_header:hist})  # 数组转直方图
                        hist_df = pd.concat([hist_df, df_foo], axis=1)  # 增加一列存放直方图数据
                        
                        # 对信噪比直方图曲线半高宽做统计 并保存数据
                        fwhm_dict = self.cal_FWHM(hist)                        
                        df_foo = pd.DataFrame(fwhm_dict,   
                            index=[df_header], # 由于字典一个key只有一个value 因此指定[0]表示放第0行
                            columns=['曲线峰值', '峰值横坐标','半高宽', 
                                    '半高宽中点横坐标', 
                                    '偏心程度-负数表示半高宽中点大于峰值坐标','直方图长度']
                                    )
                        fwhm_df = pd.concat([fwhm_df, df_foo], axis=0)

                fout = 'SNR-Hist-' + now + '.csv'
                hist_df.to_csv(fout, header=True, index=False, encoding='gbk')
                self.log_show('信噪比直方图文件输出，文件名：' + fout)
                os.system('start'+ ' ' + fout)
                
                fout = 'SNR-FWHM-' + now + '.csv'
                fwhm_df.to_csv(fout, header=True, index=True, encoding='gbk')
                self.log_show('信噪比直方图曲线评价文件输出，文件名：' + fout)
                
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e)) 
        
    
    '''
    计算噪声函数
    选择多幅图像 逐点计算标准差 统计标准差分布后绘图并保存曲线
    '''    
    def click_noise_std_open(self):
        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()       
                
        try:
            # 读入所有文件数据
            raw_dirs = QFileDialog.getExistingDirectory(self, caption='选择文件夹')
            
            # 先在所选目录中找文件
            filelist = glob.glob(raw_dirs + '\\*.raw')
            
            # 当前目录未找到图像文件 则在下级RAW_ImageData中找文件
            if len(filelist) == 0 :
                self.log_show(raw_dirs + '中没有图像文件, 尝试在RAW_ImageData中寻找')
                filelist = glob.glob(raw_dirs + '\\RAW_ImageData\\*.raw')
            # 未找到文件 转手动选择
            if len(filelist) == 0 :                 
                self.log_show('没找到图像文件,转手动选择')
                res = QMessageBox.question(self, '请选择', '未找到RAW文件 是否手动选文件?')
                if res == QMessageBox.No:
                    self.log_show('未进行数据处理')
                    return
                else:                
                    raw_dirs = 'histogram'  # 改名用于csv文件中表头 不代表目录
                    filelist, filt = QFileDialog.getOpenFileNames(
                        self, filter='raw file(*.raw)', caption='打开图像文件')  
            else:  # 在在RAW_ImageData中找到文件
                self.log_show('在RAW_ImageData文件夹中找到图像文件')      
            
            # 统一读入文件数量判断 无论是选文件夹方式还是手选方式
            if len(filelist) < 2:
                self.log_show('选择文件数量小于2，不能计算噪声')
                return            
            # 读入文件 生成数组
            raw_data = np.empty([len(filelist), raw_height*raw_width], dtype=np.uint16)
            for i, filename in enumerate(filelist):
                raw_data[i] = np.fromfile(filename, dtype=np.uint16)
            
            # 计算标准差 为提高精度 标准差乘以10后转整数    
            raw_std = np.std(raw_data, axis=0, ddof=0) * 10
            
            now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
            fout = 'histogram-std-' + now + '.csv'
            
            self.hist_plot(raw_std)
            self.hist_save(raw_std, fout, raw_dirs)  # 将文件夹名称作为生成的csv首行
            
            self.log_show('完成' + str(len(filelist)) + '个文件标准差计算')
            self.log_show('输出直方图数据文件' + fout)        
        
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e))    
    
    '''
    多视场拼图软件
    导入图片 二值化处理 对应像元“求平均” 重合像元处理 文件输出
    文件求平均，为保证灰度值不溢出 先除以1000 算法完成后再还原
    方法详见界面说明
    '''
    def click_multiView_open(self):
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value() 
        dn_threhold = self.spinBox_multiView_threhold.value()
        img_cnt = self.spinBox_mutilView_img_cnt.value()
        
        try:
            # 读入所有文件数据
            filelist, filt = QFileDialog.getOpenFileNames(
                self, filter='raw file(*.raw)', caption='打开图像文件')    
            
            # 文件数量判断
            if len(filelist) == 0 :
                self.log_show('未选择文件')
                return
            elif (len(filelist) % img_cnt) != 0 :
                self.log_show('文件数量不是' + str(img_cnt) + '的整数倍，不进行处理')
                return
            else :
                self.log_show('打开文件共计'+ str(len(filelist)) + '个')
            
            # 读入图像
            raw_data = np.empty([len(filelist), raw_height*raw_width], dtype=np.uint16)  
            for i, filename in enumerate(filelist):
                raw_data[i] = np.fromfile(filename, dtype=np.uint16)
            # 图像二值化 缩小 求和 求'平均'
            raw_data[raw_data < dn_threhold] = 0
            raw_data = raw_data / 1000
            img = np.sum(raw_data, axis=0)
            img = img / img_cnt
            # 重叠图像处理 阈值先缩小1000倍×2(即乘0.002) 灰度值大于该值时更改为阈值的一半 
            img[img > 0.002*dn_threhold] = (0.001*dn_threhold)/2
            # 图像灰度值复原 乘以1000
            img = img * 1000
                        
            # 图像输出
            now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
            fout = 'MultiView-' + now + '.raw'
            self.raw_file_output(fout, img)
                        
            self.log_show('多视场拼图完成，输出文件名:' + fout)
        
        
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e)) 
        
    
    
    '''
    米字形光源处理函数
    根据配置的csv文件，计算每个波段图片的光斑重心坐标、灰度值
    输出： csv文件
    '''    
    def click_ml_raw_open(self):
        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()  
        # 读入光斑尺寸 判定光斑有效的比率 计算重心DN值的像素尺寸
        light_spot_size = int(self.spinBox_light_spot_size.value() / 2)
        threshold_ratio = self.doubleSpinBox_light_spot_maxratio.value()
        ls_dn_size = self.spinBox_light_spot_dn.value()
        
        try:
            # 读入所有文件数据
            raw_dirs = QFileDialog.getExistingDirectory(self, caption='选择文件夹')
            # 先在所选目录中找文件
            filelist = glob.glob(raw_dirs + '\\*.raw')
            # 当前目录未找到图像文件 则在下级RAW_ImageData中找文件
            if len(filelist) == 0 :
                self.log_show(raw_dirs + '中没有图像文件,尝试在RAW_ImageData中寻找')
                filelist = glob.glob(raw_dirs + '\\RAW_ImageData\\*.raw')                   
            
            # 未在RAW_ImageData找到文件 转手动选择
            if len(filelist) == 0 :
                self.log_show('没找到图像文件,转手动选择')
                res = QMessageBox.question(self, '请选择', '未找到RAW文件 是否手动选文件?')
                if res == QMessageBox.No:
                    self.log_show('未进行数据处理')
                    return
                else:                     
                    filelist, filt = QFileDialog.getOpenFileNames(
                        self, filter='raw file(*.raw)', caption='打开图像文件')
            else:  # 在RAW_ImageData中找到文件
                self.log_show('在RAW_ImageData文件夹中找到图像文件')
                
            if len(filelist)<15 :
                self.log_show('文件数量小于15 无法进行数据处理')
                return
            
            # 15个通道文件求平均后的图像矩阵
            all_channel_img = np.empty([15, raw_height*raw_width])
            
            # 将文件按照波段划分 并求平均后生成15个通道的图像
            # 第一层循环 ch_cnt表示图像序号 
            for ch_cnt in range(1, 16): 
                img_file = list()  # 保存该通道的文件名
                # 第二层循环 遍历所有文件 找出所有第ch_cnt个通道的文件
                for filename in filelist:  
                    # 生成含有该通道关键字的keyword 判断文件名是否含有该关键字
                    if filename[-6] == '_' :  # 兼容 _1.raw和 01.raw
                        keyword = '_' + str(ch_cnt) + '.raw'
                    else:
                        keyword = str(ch_cnt).zfill(2) + '.raw'
                    # 该文件名属于该通道 则加入文件名列表                        
                    if keyword in filename:
                        img_file.append(filename)
                # 第二层循环结束 img_file中存放了所有第ch_cnt通道的图像地址
                # 读入文件 生成数组 求平均后保存
                raw_data = np.empty([len(img_file), raw_height*raw_width], dtype=np.uint16)
                for i, filename in enumerate(img_file):
                    raw_data[i] = np.fromfile(filename, dtype=np.uint16)
                all_channel_img[ch_cnt-1] = np.mean(raw_data, axis=0)  # 从0开始 求平均
            # 以上 文件分离结束 all_channel_img存放有15个求过平均的图像

            # 扣本底 除去负数
            # dkg_img = all_channel_img[7]
            for i in range(15):
                if i == 7:
                    continue
                else:
                    all_channel_img[i] = all_channel_img[i] - all_channel_img[7]  # 从0记录 7为本底
            all_channel_img[all_channel_img < 0 ] = 0        
            
            ##debug
            # for i in range(15):                
                # self.raw_file_output(str(i+1)+'.raw', all_channel_img[i])
            ##debug
            
            light_spot_df = pd.DataFrame()
            # 用边沿检测寻找光斑 
            for ch_cnt in range(15):  # ch_cnt表示通道序号
                if ch_cnt == 7:  #本底通道 不处理
                    continue                
                # 暂存图像矩阵后放入光斑检测函数
                foo_img = np.reshape(all_channel_img[ch_cnt], (raw_height, raw_width))
                foo_df = self.light_spot_detection(str(ch_cnt+1)+'--'+enum_DPC_band(ch_cnt).name, \
                                                    foo_img, threshold_ratio, light_spot_size, ls_dn_size)
                # 将该通道数据拼接
                light_spot_df = pd.concat([light_spot_df, foo_df], axis=0)
                
            # 输出
            now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            fout = 'light_spot_' + now + '.csv'
            light_spot_df.to_csv(fout, header=True, index=False, encoding='gbk') 
            os.system('start'+ ' ' + fout)
            self.log_show('光斑数据处理完成 输出文件' + fout)
            
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e))    
            
            
        
    
    '''
    多通道图像预处理
    按照文件名求平均 做扣本底 做帧转移后输出
    '''
    def click_openIMG_multi(self):
        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value() 
        
        try:
            # 读入所有文件数据
            raw_dirs = QFileDialog.getExistingDirectory(self, caption='选择文件夹')
            # 先在所选目录中找文件
            filelist = glob.glob(raw_dirs + '\\*.raw')
            # 当前目录未找到图像文件 则在下级RAW_ImageData中找文件
            if len(filelist) == 0 :
                self.log_show(raw_dirs + '中没有图像文件,尝试在RAW_ImageData中寻找')
                filelist = glob.glob(raw_dirs + '\\RAW_ImageData\\*.raw')                   
            
            # 未在RAW_ImageData找到文件 转手动选择
            if len(filelist) == 0 :
                self.log_show('没找到图像文件,转手动选择')
                res = QMessageBox.question(self, '请选择', '未找到RAW文件 是否手动选文件?')
                if res == QMessageBox.No:
                    self.log_show('未进行数据处理')
                    return
                else:                     
                    filelist, filt = QFileDialog.getOpenFileNames(
                        self, filter='raw file(*.raw)', caption='打开图像文件')
            else:  # 在RAW_ImageData中找到文件
                self.log_show('在RAW_ImageData文件夹中找到图像文件')
                
            if len(filelist)<15 :
                self.log_show('文件数量小于15 无法进行数据处理')
                return
            
            # 15个通道文件求平均后的图像矩阵
            all_channel_img = np.empty([15, raw_height*raw_width])
            
            # 将文件按照波段划分 并求平均后生成15个通道的图像
            # 第一层循环 ch_cnt表示图像序号 
            for ch_cnt in range(1, 16): 
                img_file = list()  # 保存该通道的文件名
                # 第二层循环 遍历所有文件 找出所有第ch_cnt个通道的文件
                for filename in filelist:  
                    # 生成含有该通道关键字的keyword 判断文件名是否含有该关键字
                    if filename[-6] == '_' :  # 兼容 _1.raw和 01.raw
                        keyword = '_' + str(ch_cnt) + '.raw'
                    else:
                        keyword = str(ch_cnt).zfill(2) + '.raw'
                    # 该文件名属于该通道 则加入文件名列表                        
                    if keyword in filename:
                        img_file.append(filename)
                # 第二层循环结束 img_file中存放了所有第ch_cnt通道的图像地址
                # 读入文件 生成数组 求平均后保存
                raw_data = np.empty([len(img_file), raw_height*raw_width], dtype=np.uint16)
                for i, filename in enumerate(img_file):
                    raw_data[i] = np.fromfile(filename, dtype=np.uint16)
                all_channel_img[ch_cnt-1] = np.mean(raw_data, axis=0)  # 从0开始 求平均
            # 以上 第一层循环结束 文件分离结束 all_channel_img存放有15个求过平均的图像

            # 扣本底 除去负数
            if self.checkBox_multi_subdkg.isChecked():
                for i in range(15):
                    all_channel_img[i] = all_channel_img[i] - all_channel_img[7]  # 从0记录 7为本底
                all_channel_img[all_channel_img < 0 ] = 0         
                # 扣完本底才做帧转移 否则不做            
                if self.checkBox_multi_smearing.isChecked():                
                    # 读入帧转移信息 暗行尺寸
                    dark_line_start = self.spinBox_smear_start_line.value()
                    dark_line_end = self.spinBox_smear_end_line.value()
                    # 每幅图像做帧转移
                    for i in range(15):
                        # 转二维矩阵
                        raw_data = np.reshape(all_channel_img[i], (raw_height, raw_width))
                        # 取N行时 直接用切片操作 对X进行操作取得N行                     
                        dark_lines = raw_data[dark_line_start:dark_line_end+1, :]
                        # 求平均
                        dark_lines_mean = np.mean(dark_lines, axis=0) 
                        # 帧转移校正并写回原变量 按行扣暗行平均值 广播算法 矩阵每行减去向量 并扣除负值
                        img_final = np.clip(raw_data - dark_lines_mean, 0, 65530)
                        all_channel_img[i] = img_final.flatten()
            # 图像输出
            now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
            for i in range(15):
                # 文件名定义
                fout = enum_DPC_band(i).name + '-' + now + '.raw'
                self.raw_file_output(fout, all_channel_img[i])
            
            self.log_show('多通道处理完成')            
            
        except Exception as e:
            self.log_show('处理过程出现异常')
            self.log_show('异常信息: '+ repr(e))  
        
    
    
    
# ----------------内部函数----------------
    # 记录日志函数
    def log_show(self, foo_txt):
        now = time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))
        txt_out = now + foo_txt
        self.textEdit_log.append(txt_out)

    # raw文件输出
    def raw_file_output(self, fname, raw_data):
        with open(fname, 'wb') as f:
            raw_data[raw_data < 0] = 0  # 除去负数
            raw_data[raw_data > 65535] = 65535  # 除去异常大值
            for i in raw_data.flatten():
                foo = struct.pack('H', int(i))
                f.write(foo)
    
    '''
    计算重心函数
    算法:   大于最大值和小于最小值的像素清零 
            每个像素所在坐标值乘以DN值 求和后除以全像面图像DN值之和   
            使用meshgird函数生成坐标矩阵 用于元素乘以对应坐标值
    '''
    def cal_center_gravity(self, img):        
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
        
        # 保留两位小数返回
        return round(cenx,2),  round(ceny,2)
        # return cenx, ceny

    '''
    逐点计算信噪比函数
    输入：文件列表 图像宽和高度
    算法：每个点平均值除以方差 文件总数小于2则输出全零图像
    输出：信噪比数据  numpy数组 一维数组 长度为宽×高
    '''
    def cal_snr(self, filelist, width, height):        
        raw_data = np.empty([len(filelist), width*height], dtype=np.uint16)  
        
        for i, filename in enumerate(filelist):
            raw_data[i] = np.fromfile(filename, dtype=np.uint16)
        # 逐点求平均
        raw_mean = np.mean(raw_data, axis=0)
        # 求标准差 ddof=0表示对总体计算 不是抽样样本计算
        raw_std = np.std(raw_data, axis=0, ddof=0)
        raw_std[raw_std == 0 ] = 0.0001  # 标准差为0 避免信噪比无穷大
        # 计算信噪比 当标准差为0时 认为信噪比无穷大 用65535表示
        raw_data = raw_mean / raw_std      
        raw_data[raw_data > 9999] == 65535                 
        
        return raw_data
    
    
    '''
    噪声统计函数
    输入：直方图数组
    算法：半高宽：找数组最大值，除以2，统计数组中所有大于半个最大值的个数
        偏心程度：最大位置 - 半高宽中点位置
    输出：字典类型 汉字类型的key  最大值 最大值位置 半高宽 半高宽中点 偏心程度
    '''
    def cal_FWHM(self, hist_array):
        # 求最大值位置   
        hist_max_pos = np.argmax(hist_array)  # 最大值对应的索引
        # 求半高宽
        hist_max = np.max(hist_array)
        fwhm = len(hist_array[hist_array > (hist_max/2)])  # 布尔索引 x[x>1]返回数组x中所有大于1的数 求长度即可
        # 求半高宽中点和偏心程度
        pos_array = np.argwhere(hist_array > (hist_max/2))  # 获取半高宽所有点坐标
        pos_array = pos_array.flatten()
        fwhm_mid_pos = pos_array[int(len(pos_array)/2)]  # 长度的一半作为索引选出中间值
        std_off_center = hist_max_pos - fwhm_mid_pos  # 偏心程度

        fwhm_dict = {'曲线峰值': hist_max,
                    '峰值横坐标':hist_max_pos,
                    '半高宽':fwhm,
                    '半高宽中点横坐标':fwhm_mid_pos,
                    '偏心程度-负数表示半高宽中点大于峰值坐标':std_off_center,
                    '直方图长度':str(len(hist_array))}
        return fwhm_dict

    '''
    直方图生成和曲线绘制
    形参 raw_data--用于统计直方图的文件
    输入 图像的直方图
    处理 转为直方图并绘图
    '''    
    def hist_plot(self, raw_data):
        raw_data = raw_data.astype(np.int32)
        hist = np.bincount(raw_data)
        plt.figure()
        plt.plot(hist) 
        plt.show()        
        # plt.close('all') 

    '''
    直方图数据生成
    形参 raw_data--用于统计直方图的文件
    outfilename--输出csv文件的文件名
    csv_header--生成csv文件的首行信息
    输入 图像的直方图
    处理 绘图 生成csv文件
    '''       
    def hist_save(self, raw_data, outfilename, csv_header='histogram'):    
        raw_data = raw_data.astype(np.int32)
        hist = np.bincount(raw_data)
        
        # 计算直方图参数 返回字典类型
        hist_dict = self.cal_FWHM(hist)
        
        # pandas形成csv文件输出
        df1 = pd.DataFrame({csv_header: hist})  # 第一个df 用于保存直方图数组
        # 第二个df 用于保存直方图的信息  index指定行位置 colums指定列顺序
        df2 = pd.DataFrame(hist_dict,   
                            index=[0], # 由于字典一个key只有一个value 因此指定[0]表示放第0行
                            columns=['曲线峰值', '峰值横坐标','半高宽', 
                                    '半高宽中点横坐标', 
                                    '偏心程度-负数表示半高宽中点大于峰值坐标','直方图长度']
                                    )
        df = pd.concat([df1, df2], axis=1)  # 不同维度df拼接 空白单元格自动用nan补充

        df.to_csv(outfilename, header=True, index=False, encoding='gbk')


    '''
    光斑检测函数 
    输入:
        ch_cnt 通道编号
        raw_data 已经变为二维数组的图像文件
        max_dn_ratio 判定光斑有效的比例 
        ls_dn_size 求光斑附件N×N个像素灰度平均值
    '''
    def light_spot_detection(self, ch_cnt, raw_data, max_dn_ratio, light_spot_size, ls_dn_size):
        # 获取图像尺寸
        raw_height, raw_width = raw_data.shape
        # 判定光斑有效的阈值 便于二值化
        threhold = max_dn_ratio * np.max(raw_data)  
        # 二值图像threshold函数 THRESH_BINARY指大于threhold用1表示 返回图像放在foo_raw中
        retval, foo_raw	= cv2.threshold(raw_data, threhold, 1, cv2.THRESH_BINARY)
        foo_raw = foo_raw.astype(np.uint8)  # 二值化后转8位图像
        # 寻找边沿函数 RETR_EXTERNAL指仅找外边沿 CHAIN_APPROX_SIMPLE指简化返回坐标
        contours, hierarchy	= cv2.findContours(foo_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 该图像中所有光斑信息列表
        channel = list()
        center_x = list()
        center_y = list()
        center_dn = list()
        # 针对每找到的光斑进行处理
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
            
            # 求重心坐标 求重心坐标附近DN值
            cenx,ceny = self.cal_center_gravity(light_spot_img)
            light_spot_dn = np.mean(raw_data[int(cenx-ls_dn_size):int(cenx+ls_dn_size+1),\
                                            int(ceny-ls_dn_size):int(ceny+ls_dn_size+1)])
            center_x.append(cenx)
            center_y.append(ceny)
            center_dn.append(light_spot_dn)
            channel.append(ch_cnt + '-' + str(i))
        
        light_spot_df = pd.DataFrame({'S3-x':center_y, 'S3-y':center_x, 
                                    'dn':center_dn, 'channel':channel},
                                        columns=['channel', 'S3-x', 'S3-y', 'dn'])
        return light_spot_df

        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywidget = Test()
    mywidget.show()
    sys.exit(app.exec_())
