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


fig_title = '装星前电测'

# path = 'e:\\02遥感数据\\20200526T090626_CM-干扰测试\\4\\'
# os.chdir(path)
path = '装星后电测2-20ms-0515-备份'
os.chdir('e:\\02遥感数据\\各种测试本底\\' + path + '\\RAW_ImageData')

filelist = glob.glob('*.raw')
# filelist = glob.glob('SNR-*.raw')

raw_data = np.empty([len(filelist), 1030*1024], dtype=np.uint16)
# raw_data = np.empty([len(filelist), 512*380], dtype=np.uint16)

for i, filename in enumerate(filelist):
    raw_data[i] = np.fromfile(filename, dtype=np.uint16)
    
raw_std = np.std(raw_data, axis=0, ddof=0)
raw_mean = np.mean(raw_data, axis=0)
raw_snr = raw_mean / raw_std
raw_snr = raw_snr.astype(np.int32)


hist = np.bincount(raw_snr)
plt.figure()
plt.plot(hist)
plt.title(fig_title)

os.chdir('d:\\Temp_prj\\Python_prj\\Img_preprocess')
plt.savefig(path + '.png')
plt.show()
plt.close() 

# np.savetxt('2.txt', hist, fmt = "%.2f")

