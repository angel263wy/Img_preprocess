'''
图像快速判错工具
读入目录内所有图像
逐像元比较灰度值与设定值的大小 如果超过设定值则输出文件名以及图像灰度值
'''

import numpy as np
import os
import glob
from multiprocessing import Process, Queue


'''
多进程函数
形参： file_queue--文件列表 用队列方式输出文件 max_dn--图像最大DN值 用于判断
'''
def judge(file_queue, max_dn):
    while file_queue.qsize():
        fname = file_queue.get()
        raw_data = np.fromfile(fname, dtype=np.uint16)
        for j in raw_data:
            if j > max_dn :
                print(fname + '  ' + str(j))


if __name__ == "__main__":
    max_dn = 405
    path = 'd:\\GF-5B\\DPC\\2-光机头部\\装星干扰\\整星电测图像\\0514-20ms'  
    
    os.chdir(path)
    filelist = glob.glob('*.raw')
    print(len(filelist))
    
    file_queue = Queue()
    for fname in filelist:
        file_queue.put(fname)
        
    p1 = Process(target=judge, args=(file_queue, max_dn))
    p2 = Process(target=judge, args=(file_queue, max_dn))
    p3 = Process(target=judge, args=(file_queue, max_dn))
    
    p_l = [p1, p2, p3]
    for p in p_l:
        p.start()

    for p in p_l:
        p.join()
        
    print('end\n')