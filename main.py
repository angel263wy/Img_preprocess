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
                        self.log_show('平均后的图像已输出 文件名为' + filename)
                    except Exception as ee:
                        self.log_show('未选择输出的文件名 平均后的图像未输出')

            else:
                self.log_show('未选择文件')

        except Exception as e:
            self.log_show('文件打开失败')

    # 单幅图像处理 打开本底文件

    def click_open_dark_sig(self):
        pass

    # 单幅图像处理 扣本底函数

    def click_sub_dark_sig(self):
        pass

    def click_dis_smear(self):
        pass

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
