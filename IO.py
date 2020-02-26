# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 20:34:42 2020

@author: YTQSann
"""

import re
import pandas as pd
import numpy as np
import networkx as nx
from matplotlib import pyplot as plt
import tkinter as tk

# 定義一個函數提取txt文件中的引文信息，並形成對應的adjacency matrix
# 輸入txt文件所在地址
def creat_adjacency_matrix(file_path = '.\savedrecs.txt'):
    # 預編譯正則表達式
    re_title_needed = re.compile(r'^PT\s|TI\s|AB\s|CR\s|PY\s|DI\s')            #感興趣類別的行首提示符
    re_title_other = re.compile(r'^[0-9A-Z]{2}\s')                             #任意兩位數字與字母開頭的提示符
    re_space = re.compile(r'^\s{3}')                                           #行首三個空格
    re_DOI = re.compile(r'([0-9a-zA-Z\-\,\s]+)(\,\sDOI\s)([0-9a-zA-Z\-\/\.\(\)\:]+)$') #包含DOI的行
    
    # 導入文本並保留有價值部分
    with open(file_path,'r',encoding='utf-8') as f:
        data_dict = {'PT':[],'TI':[],'AB':[],'CR':[[]],'PY':[],'DI':[],'CRed':[]} #用於保存所需內容的字典
        compre_dict = {'PT':False,'TI':False,'AB':False,'CR':False,'PY':False,'DI':False} #用於標識該文獻信息是否完全的字典
        ref_count = 0                                                          #用於標識當前文獻序號的變量
        for (count,value) in enumerate(f):
            if (count == 0)&(value[0] == '\ufeff'):                            #切除開頭的BOM
                temp = value[1:]
                value = temp
            
            if re_title_needed.match(value):                                   #當前行出現感興趣的類別提示符
                titleflag = True                                               #類別是否感興趣的標誌位
                title = value[:2]                                              #當前行所屬的內容類別
            elif re_title_other.match(value):                                  #當前行出現其它類別提示符
                titleflag = False
                
            if titleflag == True:                                              #當前行為感興趣提示符所在行或在其下
                value = value.strip('\n')
                if title == 'PT':
                    value = value[3:]
                    data_dict['PT'].append(value)
                    compre_dict['PT'] = True
                elif title == 'TI':
                    if re_space.match(value):                                  #若出現不以'TI'開頭的標題
                        value = value[2:]                                      #將換行後內容增加開頭的空格
                        data_dict['TI'][ref_count] = data_dict['TI'][ref_count]+value
                    else:
                        value = value[3:]
                        data_dict['TI'].append(value)
                    compre_dict['TI'] = True
                elif title == 'AB':
                    if re_space.match(value):                                  #若出現不以'AB'開頭的摘要
                        value = value[2:]
                        data_dict['AB'][ref_count] = data_dict['AB'][ref_count]+value
                    else:
                        value = value[3:]
                        data_dict['AB'].append(value)
                    compre_dict['AB'] = True
                elif title == 'CR':
                    match_DOI = re_DOI.match(value)
                    if match_DOI:
                        if ref_count == len(data_dict['CR'])-1:                #若當前文獻序號與參考文獻存儲位置匹配
                            data_dict['CR'][ref_count].append(match_DOI.group(3))
                        else:
                            data_dict['CR'].append([])                         #若不匹配（落後）則增加欄位
                            data_dict['CR'][ref_count].append(match_DOI.group(3))
                        compre_dict['CR'] = True
                elif title == 'PY':
                    value = value[3:]
                    data_dict['PY'].append(value)
                    compre_dict['PY'] = True
                elif title == 'DI':
                    value = value[3:]
                    data_dict['DI'].append(value)
                    compre_dict['DI'] = True
            elif value[:2] == 'ER':                                            #若當前行為'ER'
                for key in compre_dict:
                    if compre_dict[key] == False:                              #給缺失欄位填充none
                        data_dict[key].append(None)
                    compre_dict[key] = False                                   #重置完整性標識，準備錄入下一文獻
                ref_count = ref_count+1
        for i in range(ref_count):                                             #預留每個文獻的被引列表
            data_dict['CRed'].append([])
            
    # 利用pandas統計各文獻被引情況
    data_df = pd.DataFrame(data_dict).sort_values(by='PY').set_index(pd.Index(list(range(ref_count)))) #利用DataFrame記錄數據，按年份排序，並調整index
    graph_df = pd.DataFrame(np.zeros((ref_count,ref_count),dtype=int),
                            index=data_df.index,
                            columns=data_df.index)                             #利用DataFrame記錄adjacency matrix
    for index in data_df.index:                                                #遍歷每個文獻
        CR_temp = data_df.loc[index,'CR']                                      #取得該文獻的參考文獻
        for each in CR_temp:                                                   #遍歷該列參考文獻
            for find in data_df[data_df['PY']<=data_df.loc[index,'PY']].index: #在所有年份早於該文獻的文獻中查找
                if data_df.loc[find,'DI'] == each:                             #若有過去的文獻與該參考文獻相同
                    data_df.loc[find,'CRed'].append(data_df.loc[index,'DI'])   #將該文獻DOI寫入對應老文獻的CRed處
                    graph_df.loc[find,index] = 1
    
    # 利用networkx繪圖
    G = nx.from_pandas_adjacency(graph_df,create_using=nx.DiGraph)
    nx.draw(G,nx.drawing.layout.planar_layout(G),with_labels=True)
    plt.show()

# 定義一個描述tkGUI的類
class My_tkGUI(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.helloLabel = tk.Label(self, text='Hello, world!')
        self.helloLabel.pack()
        self.quitButton = tk.Button(self, text='Quit', command=self.quit)
        self.quitButton.pack()

# 運行
print(creat_adjacency_matrix())
        #if __name__=='__main__':
         #   my_tkGUI = My_tkGUI()
          #  my_tkGUI.master.title('Hello World')
           # my_tkGUI.mainloop()
