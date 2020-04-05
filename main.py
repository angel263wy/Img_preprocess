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

    # 单幅图像处理 打开图像文件
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

    # 单幅图像处理 打开本底文件
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

    # 单幅图像处理 扣本底函数
    def click_sub_dark_sig(self):
        # 图像非空判断 
        if (len(self.img_origin_mean_sig)) > 0 and (len(self.img_dark_sig) > 0):
            # 扣本底算法
            self.img_sub_dark_sig = self.img_origin_mean_sig - self.img_dark_sig
            # 扣除负数
            self.img_sub_dark_sig = np.clip(self.img_sub_dark_sig, 0, 65536)
            
            # 扣本底完成 确认操作
            res = QMessageBox.question(self, '扣本底工作完成，确认后续操作', '选是输出图像，选否暂不输出')

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
    
    '''    
    def click_dis_smear(self):
        # 图像非空判断
        
        self.img_sub_dark_sig = np.fromfile('0sub_bd.raw', dtype=np.uint16)
        
        if len(self.img_sub_dark_sig) > 0: 
            # 扣完本底的图像 转二维矩阵
            raw_width = self.spinBox_img_width.value()
            raw_height = self.spinBox_img_height.value()
            raw_data = np.array(self.img_sub_dark_sig).reshape(raw_width, raw_height)
            
            # 取暗行 求平均 
            dark_line_start = self.spinBox_smear_start_line.value()
            dark_line_end = self.spinBox_smear_end_line.value()
            dark_lines = np.mean(raw_data[dark_line_start:dark_line_end], axis=0) 
            
            # 扣过本底后图像 所有行减去暗行完成校正
            for i in range(raw_width):
                self.img_final_sig[i] = raw_data[:,i] - dark_lines 
            
            # 多维数组变一维 便于输出
            self.img_final_sig =  self.img_final_sig.flatten()            
            try:
                    filename, flt = QFileDialog.getSaveFileName(
                        self, filter='raw file(*.raw)', caption='帧转移校正后图像输出')
                    self.raw_file_output(
                        filename, self.img_final_sig)
                    self.log_show('扣本底的图像已输出 位于' + filename)
            except Exception as ee:
                self.log_show('未选择输出的文件名 帧转移校正的图像未输出')
            
        else:
            self.log_show('未完成扣本底，不能进行帧转移校正')
        
        # t = self.doubleSpinBox_shift.value() / self.doubleSpinBox_integration.value()
        
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
            
        
# ----------------内部函数----------------
    # 记录日志函数
    def log_show(self, foo_txt):
        now = time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime(time.time()))
        txt_out = now + foo_txt
        self.textEdit_log.append(txt_out)

    # raw文件输出
    def raw_file_output(self, fname, raw_data):
        with open(fname, 'wb') as f:
            raw_data = np.clip(raw_data, 0, 65536)  # 除去负数
            for i in raw_data:
                foo = struct.pack('H', int(i))
                f.write(foo)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywidget = Test()
    mywidget.show()
    sys.exit(app.exec_())
