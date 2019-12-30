# coding=utf-8
import pandas as pd
import numpy as np
from numpy import *
import matplotlib.pyplot as plt
from scipy import signal
import os
import re


# 将csv文件名写入txt文件
def pre_done():
    open('csv_file_name.txt', 'w').close()
    fo = open("csv_file_name.txt", "r+")
    file_name = os.listdir("csv_source")
    for fn in file_name:
        fo.write(fn + "\n")


# 从txt文件确定raw文件、summary文件
def get_csv_name():
    raw_summary = []
    for csv_file_i in open('csv_file_name.txt').read().split('\n'):
        for csv_file_j in open('csv_file_name.txt').read().split('\n'):
            if csv_file_i != csv_file_j and len(csv_file_i) > 0 and len(csv_file_j) > 0:
                distance_i = int(re.split('[_ .]', csv_file_i)[-2])
                distance_j = int(re.split('[_ .]', csv_file_j)[-2])
                name_type_i = re.split('[_ .]', csv_file_i)[0]
                name_type_j = re.split('[_ .]', csv_file_j)[0]
                if distance_i == distance_j and name_type_i != name_type_j:
                    if 'raw' in csv_file_i and 'summary' in csv_file_j and not [csv_file_i, csv_file_j] in raw_summary:
                        raw_summary.append([csv_file_i, csv_file_j])
                    elif 'summary' in csv_file_i and 'raw' in csv_file_j and not [csv_file_j, csv_file_i] in raw_summary:
                        raw_summary.append([csv_file_j, csv_file_i])
    return raw_summary


# 函数预处理
pre_done()
return_value = get_csv_name()


# 获取raw中的ECG\PCG数据
data_ECG_raw = []
data_PCG_raw = []
for raw in range(0, len(return_value)):
    data_raw = pd.read_csv(('csv_source/%s' % return_value[raw][0]), names=['A', 'ECG', 'PCG', 'D'])
    data_ECG_raw.append(np.asarray(data_raw['ECG']))
    data_PCG_raw.append(np.asarray(data_raw['PCG']))


# 获取summary中的r、x(r-s)、r_width数据
data_summary = []
for summary in range(0, len(return_value)):
    f = open(('csv_source/%s' % return_value[summary][1]), 'r', encoding='ISO-8859-1')
    lines = f.readlines()
    f.close()
    sts = []
    sts1 = []
    for line in lines:
        sts.append(line.split(','))  # 获取summary中所有的数据（包括采集时间等）
    if sts[6][0] == "1":
        for line in sts[6:len(sts)-3]:  # 获取summary表中的第六行到倒数第三行之间的数据（筛除掉采集时间等）
            sts1.append(line)
    else:
        for line in sts[7:len(sts)-3]:  # 获取summary表中的第六行到倒数第三行之间的数据（筛除掉采集时间等）
            sts1.append(line)
    y = np.asarray(sts1)  # 筛除掉无用数据后转为数组
    for x in y:
        file_value = int(re.split('[_ .]', return_value[summary][0])[-3])
        new_sum = int(x[3])-file_value  # R列减去文件名中数值（distance）后的数据
        x[3] = str(new_sum)
    y1 = [[x[0] for x in y], [x[3] for x in y], [x[4] for x in y], [x[6] for x in y], [str(int(x[3])+int(x[4])) for x in y], [str(int(x[3])+int(x[6])) for x in y], [x[8] for x in y]]
    # 将序号、r、x(r-s)、x(r-t)、s、t、r_width存储在数组中
    y2 = mat(y1)  # 转换成矩阵
    y3 = y2.T  # 矩阵倒置
    data_summary.append(array(y3))  # 矩阵转为数组


# 获取所有RR_width的mean平均值
rr_width = []
for summary_i in range(0, len(data_summary)):
    for summary_j in data_summary[summary_i]:
        rr_width.append(int(summary_j[6]))
aver_rr_width = int(average(rr_width))
x = []
for i in range(0,aver_rr_width):
    x.append(i)


# 获取ECG中所有raw中R点及其对应的ECG值 raw中把ECG分出若干周期的数组
several_period_ecg_rr = []
for r_s_i in range(0, len(data_ECG_raw)):
    points = []
    for raw_elements_i in range(0, len(data_ECG_raw[r_s_i])):
        for summary_elements_i in data_summary[r_s_i]:
            if raw_elements_i == int(summary_elements_i[1]):
                points.append(raw_elements_i)
    for point_i in range(0, len(points)):
        for point_j in range(0, len(points)):
            if point_j == point_i + 1:
                before = points[point_i]
                behind = points[point_j]
                several_period_ecg_rr.append(data_ECG_raw[r_s_i][int(before) - 1:int(behind)])
# 将ECG周期数据按width mean值重采样
resample_period_ecg_rr = []
for i in range(0, len(several_period_ecg_rr)):
    resample_period_ecg_rr.append(signal.resample(several_period_ecg_rr[i], aver_rr_width))
# 将ECG周期按照Y轴mean
average_period_ecg_y = []
period_ecg_y = array(mat(resample_period_ecg_rr).T)
for i in range(0, len(period_ecg_y)):
    average_period_ecg_y.append(round(average(period_ecg_y[i])))
# 绘制ECG图像
ax1 = plt.subplot(224)
ax2 = plt.subplot(223)
for i in range(0,len(resample_period_ecg_rr)):
    plt.plot(x, np.asarray(resample_period_ecg_rr[i]))
    plt.sca(ax1)
plt.plot(x, average_period_ecg_y)
plt.sca(ax2)


# 获取PCG中待比较raw中R点及其对应的PCG值 # 待比较raw中把PCG分出若干周期的数组
several_period_pcg_rr = []
for r_s_i in range(0, len(data_PCG_raw)):
    points = []
    for raw_elements_i in range(0, len(data_PCG_raw[r_s_i])):
        for summary_elements_i in data_summary[r_s_i]:
            if raw_elements_i == int(summary_elements_i[1]):
                points.append(raw_elements_i)
    for point_i in range(0, len(points)):
        for point_j in range(0, len(points)):
            if point_j == point_i + 1:
                before = points[point_i]
                behind = points[point_j]
                several_period_pcg_rr.append(data_PCG_raw[r_s_i][int(before) - 1:int(behind)])
# 将PCG周期数据按width mean值重采样
resample_period_pcg_rr = []
for i in range(0, len(several_period_pcg_rr)):
    resample_period_pcg_rr.append(signal.resample(several_period_pcg_rr[i], aver_rr_width))
# 将PCG按照Y轴mean
average_period_pcg_y = []
period_pcg_y = array(mat(resample_period_pcg_rr).T)
for i in range(0, len(period_pcg_y)):
    average_period_pcg_y.append(round(average(period_pcg_y[i]), 2))
# 绘制PCG图像
ax3 = plt.subplot(222)
ax4 = plt.subplot(221)
for i in range(0,len(resample_period_pcg_rr)):
    plt.plot(x, np.asarray(resample_period_pcg_rr[i]))
    plt.sca(ax3)
    plt.setp(plt.gca(), xticklabels=[])
plt.plot(x, average_period_pcg_y)
plt.sca(ax4)
plt.setp(plt.gca(), xticklabels=[])
plt.savefig("figures/PNG.png")


# 将PCG\ECG值存入csv文件
first_four_column = []
for i in range(0, len(average_period_ecg_y)):
    first_four_column.append(0)
four_column = []
for i in range(0, len(first_four_column)):
    four_column.append([first_four_column[i], average_period_ecg_y[i], average_period_pcg_y[i], first_four_column[i]])
dataframe = pd.DataFrame(four_column)
dataframe.to_csv("good_csv/good.csv", header=False, index=False)

input("Training good_csv has finished...")









