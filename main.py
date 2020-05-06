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
                        self.log_show('异常信息: '+ repr(ee))  
                else:
                    self.log_show('图像求平均后已缓存，未输出，可以进行后续操作')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('文件打开失败')
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
            self.log_show('文件打开失败')
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
        # 存放区域最值和平均值数据
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
                        # 求最大值坐标
                        # Xmax, Ymax = np.where(raw_data==np.max(raw_data))
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
                    mean.append(np.mean(tmp_img))                    
                    center_gravity_X.append(xc)
                    center_gravity_Y.append(yc)
                
                # 所有文件读完 数据保存
                # 创建dataframe用于输出 pd.Index函数用于生成从1开始的索引 
                res = pd.DataFrame({'文件名': filelist,
                                    '全图最大值': whole_img_max,
                                    '全图最大值坐标S3-X': whole_img_max_Y,
                                    '全图最大值坐标S3-Y': whole_img_max_X,
                                    '光斑重心S3-X': center_gravity_Y,
                                    '光斑重心S3-Y': center_gravity_X,
                                    '重心区域最大值': max,
                                    '重心区域最小值': min,
                                    '重心区域平均值': mean
                                    }, columns=['文件名','全图最大值',
                                                '全图最大值坐标S3-X','全图最大值坐标S3-Y',
                                                '光斑重心S3-X','光斑重心S3-Y', 
                                                '重心区域最大值','重心区域最小值', 
                                                '重心区域平均值'],
                                    index=pd.Index(range(1, len(filelist)+1)))
                                
                self.log_show('处理图像 共计' + str(len(filelist)) + '个文件')
                
                # 输出文件
                outfile = time.strftime('%Y%m%d%H%M%S.csv', time.localtime(time.time()))
                res.to_csv(outfile, header=True, encoding='gbk')
                
                self.log_show('计算结果已输出 文件名为' + outfile)  
                                

        except Exception as e:
            self.log_show('文件打开失败')  
            self.log_show('异常信息: '+ repr(e))     
        
            
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
        cenx = np.sum(img * mx) / np.sum(img)
        ceny = np.sum(img * my) / np.sum(img)
        
        return cenx, ceny


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywidget = Test()
    mywidget.show()
    sys.exit(app.exec_())
