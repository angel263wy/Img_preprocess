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
import queue


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
                else:
                    self.log_show('图像求平均后已缓存，未输出，可以进行后续操作')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('文件打开失败')

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
                else:
                    self.log_show('扣本底的图像已缓存，但未输出，可以继续完成其他操作')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('文件打开失败')

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
        
        # 读入所有文件数据        
        filelist, filt = QFileDialog.getOpenFileNames(self, filter='raw file(*.raw)', caption='打开待校正的文件')
        if len(filelist):  # 选择文件数大于0 则处理 否则不处理            
            # 读入数据 转为矩阵 点乘计算帧转移 输出
            for filename in filelist:
                raw_data = np.fromfile(filename, dtype=np.uint16)
                raw_data = np.reshape(raw_data, (1024, 1024))
                img = np.dot(M1, raw_data)
                # 除去小于0的数据
                raw_dm = np.clip(img, 0, 4095)  
                # 文件输出
                f_out = filename[ :-4] + '_dis_smearing.raw'
                with open(f_out, 'wb') as f:
                    for i in raw_dm.flat:
                        foo = struct.pack('H', int(i))
                        f.write(foo)
                    self.log_show('1M3O帧转移校正完成, 输出文件:' + f_out)

        else:
            self.log_show('未选择文件')
        
            
    '''
    速读图像DN值函数 
    打开文件后 读取图像区域
    判断最大值、最小值和平均值
    输出csv文件
    '''
    def click_openIMG_readDN(self):
        try:
            # 读入图像的宽和高
            raw_width = self.spinBox_img_width.value()
            raw_height = self.spinBox_img_height.value()

            # 读入所有文件数据
            filelist, filt = QFileDialog.getOpenFileNames(
                self, filter='raw file(*.raw)', caption='打开图像文件')
            if len(filelist):  # 选择文件数大于0 则处理 否则不处理
                # 创建三维空数组 并读入图像  
                # 特别注意 reshape X为高 Y为宽 不能弄反
                raw_data = np.empty((len(filelist), raw_height, raw_width), dtype=np.uint16)
                for i, filename in enumerate(filelist):
                    tmp = np.fromfile(filename, dtype=np.uint16)
                    raw_data[i] = np.reshape(tmp, (raw_height, raw_width))

                # 读入图像区域窗口
                startX = self.spinBox_startX_readdn.value()
                startY = self.spinBox_startY_readdn.value()
                endX = self.spinBox_endX_readdn.value()
                endY = self.spinBox_endY_readdn.value()
                                
                # 获取图像中最大值 最小值和平均值
                # S3中X和Y 与np的XY正好相反 而np与常识中的行列一致 即X为行 Y为列
                # 取区域时 为了和S3方向一致 X和Y的位置需要对调
                max = list()
                min = list()
                mean = list()
                for i, filename in enumerate(filelist):
                    tmp = raw_data[i, startY:endY+1, startX:endX+1]
                    max.append(np.max(tmp))
                    min.append(np.min(tmp))
                    mean.append(np.mean(tmp))
                
                # 创建dataframe用于输出 pd.Index函数用于生成从1开始的索引 
                res = pd.DataFrame({'文件名': filelist,
                                    '最大值': max,
                                    '最小值': min,
                                    '平均值': mean
                                    }, columns=['文件名', '最大值', '最小值', '平均值'],
                                    index=pd.Index(range(1, len(filelist)+1)))
                                
                self.log_show('打开图像文件 共计' + str(len(filelist)) + '个文件')
                
                # 输出文件
                outfile = time.strftime('%Y%m%d%H%M%S.csv', time.localtime(time.time()))
                res.to_csv(outfile, header=True, encoding='gbk')
                
                self.log_show('计算结果已输出 文件名为' + outfile)                
                
            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('文件打开失败')       
        
            
    '''
    图像裁剪函数
    读入X和Y 选择最后的方向尺寸进行裁剪后输出
    '''
    def click_img_cut(self):
        # 读入图像区域窗口
        startX = self.spinBox_cutX.value()
        startY = self.spinBox_cutY.value()
        cut_size = self.spinBox_cut_size.value()

        # 读入图像的宽和高
        raw_width = self.spinBox_img_width.value()
        raw_height = self.spinBox_img_height.value()
        
        # 裁剪尺寸合理性判断 不能超过图像的宽和高
        if startX + cut_size > raw_width-1 :
            self.log_show('裁剪区域超过图像尺寸')
            return
        elif startY + cut_size > raw_height-1:
            self.log_show('裁剪区域超过图像尺寸')
            return
        
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
            img = raw_data[startY:startY+cut_size, startX:startX+cut_size]
            # 输出
            fout = filename[:-4] + '_cut_size_'+str(cut_size)+'X'+str(cut_size)+'.raw'
            self.raw_file_output(fout, img)
            self.log_show('图像裁剪完成 输出文件 '+ fout)

        
            
        
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
            for i in raw_data.flatten():
                foo = struct.pack('H', int(i))
                f.write(foo)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywidget = Test()
    mywidget.show()
    sys.exit(app.exec_())
