import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import struct
import cv2
import os
import glob

import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['font.serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False 

def raw_file_output(fname, raw_data):
    with open(fname, 'wb') as f:
        raw_data[raw_data < 0] = 0  # 除去负数
        raw_data[raw_data > 65535] = 65535  # 除去负数
        for i in raw_data.flat:            
            foo = struct.pack('H', int(i))
            f.write(foo)


# fig_title = '02干扰测试-X4转接盒悬空-T-热敏接插件端接地-PIN全通'  # 图片标题

# path = 'd:\\share\\123'
# os.chdir(path)
path = '20200528T175606_02干扰测试--X4转接盒悬空203A-读出板T+T-对地0.1u电容-电机转'
os.chdir('e:\\02遥感数据\\' + path + '\\RAW_ImageData')

filelist = glob.glob('*.raw')
# filelist = glob.glob('DPC_P085_C*.raw')

raw_data = np.empty([len(filelist), 1030*1024], dtype=np.uint16)
# raw_data = np.empty([len(filelist), 512*380], dtype=np.uint16)

for i, filename in enumerate(filelist):
    raw_data[i] = np.fromfile(filename, dtype=np.uint16)
    
# raw_std = np.std(raw_data, axis=0, ddof=0)
# raw_mean = np.mean(raw_data, axis=0)
# raw_snr = raw_mean / raw_std
# raw_snr = raw_snr.astype(np.int32)


raw_std = np.std(raw_data, axis=0, ddof=0) * 10
raw_std = raw_std.astype(np.int32)
hist = np.bincount(raw_std)
# raw_file_output('ok.raw', raw_snr)
plt.figure()
plt.plot(hist)
# plt.title(fig_title)
plt.title(path)

# hist = np.bincount(raw_snr)
# # raw_file_output('ok.raw', raw_snr)
# plt.figure()
# plt.plot(hist)
# # plt.title(fig_title)
# plt.title(path)

os.chdir('d:\\Temp_prj\\Python_prj\\Img_preprocess')
# plt.savefig(path + '.png')
plt.show()
plt.close() 

np.savetxt('1.csv', hist, fmt = '%d', delimiter=',', header='直方图', comments='')

