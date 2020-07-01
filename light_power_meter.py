# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/06/30
# Description : 光功率计读数处理

'''

'''

import numpy as np
import pandas as pd
import os
import glob
import struct
import time


filepath = 'e:\\sl\\GUANGPU\\565'
os.chdir(filepath)
filelist = glob.glob('*.csv')
start_wavelength = 533
fout = '565_light_power.csv'

light_power_df = pd.DataFrame()  # 保存该波长的所有文件

for wavelength_cnt, filename in enumerate(filelist):
    wavelength_csv = pd.read_csv(filename, sep=',', header=0)  
    mean_power = wavelength_csv.iloc[:, 2].mean()  # 读取第二列求平均
    wavelength = start_wavelength + wavelength_cnt  # 获取当前波长
    foo_df = pd.DataFrame({'wavelength':wavelength, 'light_power': mean_power},
                        columns=['wavelength', 'light_power'], index=[0])
    light_power_df = pd.concat([light_power_df, foo_df], axis = 0)

os.chdir('..')
light_power_df.to_csv(fout, header=True, index=False, encoding='gbk')  


