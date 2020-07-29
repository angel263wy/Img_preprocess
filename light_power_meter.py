# -*- coding: UTF-8 -*-
# Author      : WangYi
# Date        : 2020/06/30
# Description : 光功率计读数处理

'''
配合地检软件光功率计输出文件的处理
读入每个波长点的文件，对功率列单位转换后求平均后输出 

'''

import numpy as np
import pandas as pd
import os
import glob
import struct
import time

band = '443'
filepath = 'e:\\sl\\GUANGPU\\' + band
os.chdir(filepath)
filelist = glob.glob('*.csv')
start_wavelength = 423
fout = band +'_light_power-30du.csv'

light_power_df = pd.DataFrame()  # 保存该波长的所有文件

for wavelength_cnt, filename in enumerate(filelist):
    wavelength_csv = pd.read_csv(filename, sep=',', header=0)  
    
    power = wavelength_csv.iloc[ : , 2:4]  # 仅获取功率和单位
    # 统一单位 如果是nW 修改为uW
    for i in range(len(power.iloc[:,1])):
        if power.iloc[i,1] == 'nW':
            power.iloc[i, 0] = power.iloc[i, 0]/1000
    mean_power = power.iloc[:, 0].mean()  # 读取第二列求平均
        
    wavelength = start_wavelength + wavelength_cnt  # 获取当前波长
    foo_df = pd.DataFrame({'wavelength':wavelength, 'light_power': mean_power},
                        columns=['wavelength', 'light_power'], index=[0])
    light_power_df = pd.concat([light_power_df, foo_df], axis = 0)

os.chdir('..')
light_power_df.to_csv(fout, header=True, index=False, encoding='gbk')  


