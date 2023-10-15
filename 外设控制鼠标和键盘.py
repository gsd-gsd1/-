"""主控制UI
    用户显示界面

"""
import keyboard
import pynput
import threading
from tkinter.ttk import Notebook, Combobox
import numpy as np
import tkinter as tk
from tkinter import *
import serial
import serial.tools.list_ports
from queue import Queue
import time
import pyautogui
import pyautogui as pg
import re


# 分离坐标数据
def divide_position_data(data):
    # 检查数据格式
    data_get = []
    pattern = r"\d+"
    numbers = re.findall(pattern, data)
    for number in numbers:
        data_get.append(int(number))
    if len(data_get) != 2:
        print("数据格式错误！")
        return []
    return data_get


# 判断字符串是否为数字
def is_number(s):
    try:  # 如果能运行float(s)语句，返回True（字符串s是浮点数）
        float(s)
        return True
    except ValueError:  # ValueError为Python的一种标准异常，表示"传入无效的参数"
        pass  # 如果引发了ValueError这种异常，不做任何事情（pass：不做任何事情，一般用做占位语句）
    try:
        import unicodedata  # 处理ASCii码的包
        unicodedata.numeric(s)  # 把一个表示数字的字符串转换为浮点数返回的函数
        return True
    except (TypeError, ValueError):
        pass
    return False


class UI:
    def __init__(self, master):
        """定义相关变量"""
        # 定义串口相关变量
        self.COMPort = None  # 端口号
        self.COMBaud = None  # 波特率
        self.COMCheck = None  # 校验位
        self.COMDataBit = None  # 数据位
        self.COMStopBit = None  # 停止位
        self.COMList = None  # 串口列表
        self.COMObj = None  # 串口对象
        self.ReadBuff = None  # 数据读取缓冲区
        self.WriteBuff = None  # 数据写缓冲区域
        self.Is_Adjust = False  # 进入设备调试功能
        self.COM_Queue = Queue(maxsize=1024)  # 消息队列，通知其他线程,最大缓存1024
        self.Data_Queue = Queue(maxsize=1024)  # 数据队列，通知其他线程

        # 定义键盘控制的相关变量
        self.KeyBoard_CheckBox_Is_Control = tk.IntVar()  # 选择框变量
        self.KeyBoard_Is_Control = False  # 判断是否使用键盘进行控制
        self.KeyBoard_Exit = False  # 表示EXIT被按下

        # 定义鼠标控制的相关变量
        self.Mouse_CheckBox_Is_Control = tk.IntVar()
        self.Mouse_Remember_Position = []  # 鼠标的记录位置
        self.Mouse_Remember_gap = 0.01  # 记录时的采样间隔
        self.Mouse_Is_Control = False  # 表示是否对鼠标进行控制
        self.Mouse_Click_Control = None  # 鼠标按键的控制，下拉框的方式（左键，右键，中键）
        self.Mouse_Click_Mode = 1  # 鼠标点击模式，是点击一下还是长摁
        self.Mouse_Is_Remember = False  # 是否进行鼠标移动的记录，False为停止记录，True为开始记录
        self.Mouse_Execute_Time = 2  # 鼠标运动的时间快慢，一般由串口发送的数据来决定，所以串口需要记录变化的时间(完全模拟，动一次一个周期)
        self.Mouse_Is_Rectangle = False  # 鼠标的移动是一个矩形
        self.Mouse_Is_Circle = False  # 鼠标的移动是一个圆形
        self.Mouse_Is_Line = False  # 鼠标的移动是一条直线
        self.Mouse_Is_Automatic = True  # 选择控制模式
        self.Mouse_Automatic_Is_Control = False  # 标记控制是否已经开始
        self.Th_Inform = False  # 线程之间的通信标识

        # 设备信息获取相关变量
        self.Device_Number = 0

        # 鼠标监听事件相关变量
        self.Mouse_Click_Listener_line = 0
        self.Mouse_Click_Listener_Rectangle = 0
        self.Mouse_Click_Listener_Circle = 0

        # 鼠标相关控件变量定义
        self.Mouse_Choose_Mode = tk.IntVar()  # 鼠标的控制模式, 有全自动模式和半自动模式（手动控制位置）
        self.Mouse_Mode_Automatic_Mode = tk.StringVar()  # 自动化模式选择，有矩形，直线，记忆，圆形
        self.Mouse_Mode_Control_Mode = tk.StringVar()  # 模拟控制的按键，包括左键、右键，中键
        self.Mouse_Mode_Click_Mode = tk.StringVar()  # 鼠标的控制方式，长按或是单击
        self.Position_Line_Is_Change = False  # 标记直线坐标是否发生改变
        self.Position_Rectangle_Is_Change = False  # 标记矩形坐标是否发生改变
        self.Position_Circle_Is_Change = False  # 标记圆形坐标是否发生改变
        self.Position_Memory_Is_Change = False  # 标记记忆坐标是否发生改变
        self.Mouse_Is_Controlling = False  # 是否正在进行控制
        self.mouse_drag = None  # 判断是否拖拽
        self.Mouse_Is_Drag = False  # 判断是否按下

        self.line_position_divide = []  # 缓存直线坐标
        self.rectangle_position_divide = []  # 缓存矩形坐标
        self.circle_position_divide = []  # 缓存圆形坐标
        self.memory_position_divide = []  # 缓存记忆坐标

        self.rectangle_position_all = []  # 记录所有推算点

        self.circle_x = 0
        self.circle_y = 0
        self.circle_tha_step = 0
        self.circle_r = 0

        self.memory_last_rectangle_position = 0  # 记录矩形上次的坐标
        self.memory_last_memory_position = 0  # 记录记忆的上次的坐标

        # 直线
        self.Mouse_Mode_Automatic_Line_Start_Position = tk.StringVar()
        self.Mouse_Mode_Automatic_Line_Position = []  # 保存直线坐标
        self.Mouse_Mode_Automatic_Line_Stop_Position = tk.StringVar()
        # 矩形
        self.Mouse_Mode_Automatic_Rectangle_Start_Position = tk.StringVar()
        self.Mouse_Mode_Automatic_Rectangle_Position = []  # 保存矩形坐标
        self.Mouse_Mode_Automatic_Rectangle_Stop_Position = tk.StringVar()
        # 圆形
        self.Mouse_Mode_Automatic_Circle_Start_Position = tk.StringVar()
        self.Mouse_Mode_Automatic_Circle_Position = []  # 保存矩形坐标
        self.Mouse_Mode_Automatic_Circle_Stop_Position = tk.StringVar()
        # 半自动控制相关
        self.Mouse_Mode_Half_Automatic_Move_Calculate = tk.IntVar()  # 设置移动多少距离点击一次
        self.Mouse_Mode_Half_Automatic_Move_Calculate_Con = tk.IntVar()  # 控件的存储

        self.Mouse_Mode_Half_Automatic_Time_Stop = tk.DoubleVar()  # 设置多少时间停止鼠标按下
        self.Mouse_Mode_Half_Automatic_Time_Stop_Con = tk.DoubleVar()  # 控件的存储

        self.Mouse_Mode_Half_Automatic_Last_Click_Position = 0  # 初始化上一次控制的位置
        self.Mouse_Mode_Half_Automatic_Last_Sum_division = 0  # 差距的总和

        self.Mouse_Mode_Half_Automatic_Start_Time = 0  # 计时器，记录运行开始时间
        self.time_gap_sum = 0  # 时间的累积
        self.Time_Num_Check = False

        # ................ 在正式开发时具体考虑.........................
        # 其他实验功能    以后开发
        self.Is_Control_By_Mouse = False  # 鼠标是否反向控制设备？
        # 鼠标反向控制时需要设置
        self.Mouse_Cycle_Times = 1  # 完成一次周期时，设备控制几下
        self.Is_Control_By_Memory = False  # 是否监控内存，根据内存的变化来进行额外设备的控制？

        # 相关快捷键变量
        self.KeyBoard_Combine_Key_Start_Remember = "ctrl+shift+r"  # 用来记录开始进行鼠标监听的快捷键
        self.KeyBoard_Combine_Key_Stop_Remember = "ctrl+shift+s"  # 用来记录停止鼠标监听的快捷键
        self.KeyBoard_Combine_Key_Start_Control = "ctrl+shift+c"  # 开始进行鼠标控制
        self.KeyBoard_Combine_Key_Stop_Control = "ctrl+shift+x"  # 停止鼠标控制

        # 定义相关位置变量
        self.row_position_base = tk.IntVar()
        self.col_position_base = tk.IntVar()

        """相关参数初始化"""
        self.Mouse_Choose_Mode.set(1)  # 控制模式变量初始化
        self.Mouse_Mode_Half_Automatic_Time_Stop_Con.set(1.5)
        self.Mouse_Mode_Half_Automatic_Move_Calculate_Con.set(6)

        """首页界面创建"""
        master_frame = Frame(master, name='master_frame', width=1200, height=1000)
        master_frame.grid_propagate(False)
        master.title('外设模拟点击程序')
        master.resizable(0, 0)
        # 分页
        note = Notebook(master_frame, name='note')
        # 菜单
        menubar = tk.Menu(master)

        # 定义空的菜单单元
        fileMenu = tk.Menu(menubar, tearoff=0)  # tearoff意为下拉
        editMenu = tk.Menu(menubar, tearoff=0)
        toolMenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='文件', menu=fileMenu)
        master.config(menu=menubar)
        master_frame.grid()
        # 放置分页
        note.grid(row=0, column=0, ipadx=300, ipady=260)

        """创建分页1---------主界面"""
        frame_main = Frame(note)
        note.add(frame_main, text="主界面")

        """初始化相关变量"""
        # 位置相关
        self.col_position_base = 1
        self.row_position_base = 3

        """串口相关"""
        '''端口号相关布局'''
        self.COMPort_Label = Label(frame_main, text="***串口相关***")
        self.COMPort_Label.grid(row=self.row_position_base * 0, column=self.col_position_base * 0, rowspan=3)
        # 端口号标签
        self.COMPort_Label = Label(frame_main, text="端口号: ")
        self.COMPort_Label.grid(row=self.row_position_base * 1, column=self.col_position_base * 0, rowspan=3)
        # 端口号下拉框
        self.COMPort_Combobox = Combobox(frame_main)
        self.COMPort_Combobox["value"] = [""]
        self.COMPort_Combobox['state'] = 'readonly'
        self.COMPort_Combobox.current(0)
        self.COMPort_Combobox.grid(row=self.row_position_base * 1, column=self.col_position_base * 1, rowspan=3)
        self.COMPort_Combobox.bind('<<ComboboxSelected>>', self.Get_COMPort_Select)
        # 初始化
        self.Get_COMPort_Select(1)

        '''波特率相关布局'''
        # 波特率标签
        self.COMBaud_Label = Label(frame_main, text="波特率: ")
        self.COMBaud_Label.grid(row=self.row_position_base * 2, column=self.col_position_base * 0, rowspan=3)
        # 波特率下拉框
        self.COMBaud_Combobox = Combobox(frame_main)
        self.COMBaud_Combobox['value'] = ('4800', '9600', '14400', '19200',
                                          '38400', '57600', '115200', '128000'
                                          , '230400', '256000', '460800')
        self.COMBaud_Combobox['state'] = 'readonly'
        self.COMBaud_Combobox.grid(row=self.row_position_base * 2, column=self.col_position_base * 1, rowspan=3)
        self.COMBaud_Combobox.current(6)
        self.COMBaud_Combobox.bind('<<ComboboxSelected>>', self.Get_Baud_Select)
        # 初始化
        self.Get_Baud_Select(arge=1)

        '''校验位相关布局'''
        # 校验位标签
        self.COMCheck_Label = Label(frame_main, text="校验位: ")
        self.COMCheck_Label.grid(row=self.row_position_base * 3, column=self.col_position_base * 0, rowspan=3)
        # 校验位下拉框
        self.COMCheck_Combobox = Combobox(frame_main)
        self.COMCheck_Combobox["value"] = ('无', '奇', '偶')
        self.COMCheck_Combobox['state'] = 'readonly'
        self.COMCheck_Combobox.grid(row=self.row_position_base * 3, column=self.col_position_base * 1, rowspan=3)
        self.COMCheck_Combobox.current(0)
        self.COMCheck_Combobox.bind('<<ComboboxSelected>>', self.Get_Check_Select)
        # 初始化
        self.Get_Check_Select(arge=1)

        '''数据位相关布局'''
        # 数据位标签
        self.COMDataBit_Label = Label(frame_main, text="数据位: ")
        self.COMDataBit_Label.grid(row=self.row_position_base * 4, column=self.col_position_base * 0, rowspan=3)
        # 数据位下拉框
        self.COMDataBit_Combobox = Combobox(frame_main)
        self.COMDataBit_Combobox['value'] = ('5', '6', '7', '8')
        self.COMDataBit_Combobox['state'] = 'readonly'
        self.COMDataBit_Combobox.grid(row=self.row_position_base * 4, column=self.col_position_base * 1, rowspan=3)
        self.COMDataBit_Combobox.current(3)
        self.COMDataBit_Combobox.bind('<<ComboboxSelected>>', self.Get_Data_Bit_Select)
        # 初始化
        self.Get_Data_Bit_Select(arge=1)

        '''停止位相关布局'''
        # 停止位标签
        self.COMStopBit_Label = Label(frame_main, text="停止位: ")
        self.COMStopBit_Label.grid(row=self.row_position_base * 5, column=self.col_position_base * 0, rowspan=3)
        # 停止位下拉框
        self.COMStopBit_Combobox = Combobox(frame_main)
        self.COMStopBit_Combobox['value'] = ('1', '2')
        self.COMStopBit_Combobox['state'] = 'readonly'
        self.COMStopBit_Combobox.grid(row=self.row_position_base * 5, column=self.col_position_base * 1, rowspan=3)
        self.COMStopBit_Combobox.current(0)
        self.COMDataBit_Combobox.bind('<<ComboboxSelected>>', self.Get_Stop_Bit_Select)
        # 初始化
        self.Get_Stop_Bit_Select(arge=1)

        '''打开串口按钮'''
        self.COMPortOpen_Btn = Button(frame_main, text="打开串口", command=self.Open_COMPort)
        self.COMPortOpen_Btn.grid(row=self.row_position_base * 1, column=self.col_position_base * 2, rowspan=3)
        '''关闭串口按钮'''
        self.COMPortClose_Btn = Button(frame_main, text="关闭串口", command=self.Close_COMPort)
        self.COMPortClose_Btn.grid(row=self.row_position_base * 2, column=self.col_position_base * 2, rowspan=3)

        '''设备校正按钮'''
        self.COMAdjust_Button = Button(frame_main, text="设备校正", command=self.Th_Adjust_Device)
        self.COMAdjust_Button.grid(row=self.row_position_base * 5, column=self.col_position_base * 2, rowspan=3)

        """键盘监控相关"""
        '''键盘监控相关布局'''
        self.KeyBoard_Label = Label(frame_main, text="***键盘相关***")
        self.KeyBoard_Label.grid(row=self.row_position_base * 6, column=self.col_position_base * 0, rowspan=3)
        # 开启键盘监控勾选框
        self.KeyBoard_Start_Monitor = Checkbutton(frame_main, text="开启键盘监听",
                                                  variable=self.KeyBoard_CheckBox_Is_Control,
                                                  command=self.KeyBoard_Is_Open)
        self.KeyBoard_Start_Monitor.grid(row=self.row_position_base * 7, column=self.col_position_base * 0, rowspan=3)

        """鼠标监控相关"""
        '''鼠标监控相关布局'''
        self.Mouse_Label = Label(frame_main, text='***鼠标相关***')
        self.Mouse_Label.grid(row=self.row_position_base * 8, column=self.col_position_base * 0, rowspan=3)

        # 开启鼠标控制
        self.Mouse_Start_Control = Checkbutton(frame_main, text="允许控制鼠标",
                                               variable=self.Mouse_CheckBox_Is_Control,
                                               command=self.Mouse_Check_IsOpen
                                               )
        self.Mouse_Start_Control.grid(row=self.row_position_base * 9, column=self.col_position_base * 0, rowspan=3)

        # 按键控制模式-左键控制，右键控制，中键控制
        self.Mouse_Click_Control_Label = Label(frame_main, text="选择鼠标控制键")
        self.Mouse_Click_Control_Label.grid(row=self.row_position_base * 10,
                                            column=self.col_position_base * 0,
                                            rowspan=3)
        self.Mouse_Click_Control_Combobox = Combobox(frame_main, textvariable=self.Mouse_Mode_Control_Mode)
        self.Mouse_Click_Control_Combobox['value'] = ('左键',
                                                      '右键',
                                                      '中键')
        self.Mouse_Click_Control_Combobox.current(0)
        self.Mouse_Click_Control_Combobox.grid(row=self.row_position_base * 10,
                                               column=self.col_position_base * 1,
                                               rowspan=3)
        self.Mouse_Click_Control_Combobox['state'] = 'readonly'  # 只读模式

        # 鼠标点击模式控制，是单击模式还是长按模式
        self.Mouse_Mode_Click_Mode_Label = Label(frame_main, text="选择鼠标点击\n模式")
        self.Mouse_Mode_Click_Mode_Label.grid(row=self.row_position_base * 11,
                                              column=self.col_position_base * 0,
                                              rowspan=3)
        self.Mouse_Click_Click_Combobox = Combobox(frame_main, textvariable=self.Mouse_Mode_Click_Mode)
        self.Mouse_Click_Click_Combobox['value'] = ('单击',
                                                    '长按')
        self.Mouse_Click_Click_Combobox.current(0)
        self.Mouse_Click_Click_Combobox.grid(row=self.row_position_base * 11,
                                             column=self.col_position_base * 1,
                                             rowspan=3)
        self.Mouse_Click_Click_Combobox['state'] = 'readonly'  # 只读模式
        self.Mouse_Click_Click_Combobox.bind('<<ComboboxSelected>>', self.Half_Automatic_Mode_Change)
        # 全自动控制模式（选定预设范围，鼠标的控制完全自动化，建立与外设的通信）
        self.Mouse_Mode_Automatic_Radiobutton = Radiobutton(frame_main, text='全自动控制模式',
                                                            variable=self.Mouse_Choose_Mode,
                                                            value=1,
                                                            command=self.Change_Execute_Mode)
        self.Mouse_Mode_Automatic_Radiobutton.grid(row=self.row_position_base * 12,
                                                   column=self.col_position_base * 0,
                                                   rowspan=3)
        # 自动化模式下的移动模式选择(下拉框的方式)
        # 标签
        self.Mouse_Mode_Automatic_Mode_Label = Label(frame_main, text='全自动模式选择')
        self.Mouse_Mode_Automatic_Mode_Label.grid(row=self.row_position_base * 13,
                                                  column=self.col_position_base * 0,
                                                  rowspan=3)
        # 下拉框
        self.Mouse_Mode_Automatic_Combobox = Combobox(frame_main, textvariable=self.Mouse_Mode_Automatic_Mode)
        self.Mouse_Mode_Automatic_Combobox['value'] = ('直线模式',
                                                       '矩形模式',
                                                       '圆形模式',
                                                       '记忆模式')
        self.Mouse_Mode_Automatic_Combobox.current(0)
        self.Mouse_Mode_Automatic_Combobox.grid(row=self.row_position_base * 13,
                                                column=self.col_position_base * 1,
                                                rowspan=3)
        self.Mouse_Mode_Automatic_Combobox['state'] = 'readonly'  # 只读模式
        self.Mouse_Mode_Automatic_Combobox.bind('<<ComboboxSelected>>', self.Mouse_Automatic_Mode_Manager)

        '''直线模式相关控件'''
        # 提示标签-起始位置
        self.Mouse_Mode_Automatic_Line_Start_Label = Label(frame_main, text='选择直线\n起始坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Line_Start_Label.grid(row=self.row_position_base * 14,
                                                        column=self.col_position_base * 0,
                                                        rowspan=3)
        self.Mouse_Mode_Automatic_Line_Start_Position_Entry = Entry(frame_main,
                                                                    textvariable=self.Mouse_Mode_Automatic_Line_Start_Position)
        self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid(row=self.row_position_base * 14,
                                                                 column=self.col_position_base * 1,
                                                                 rowspan=3,
                                                                 sticky=tk.EW,
                                                                 padx=3)
        # 提示标签-终止位置
        self.Mouse_Mode_Automatic_Line_Stop_Label = Label(frame_main, text='选择直线\n终止坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Line_Stop_Label.grid(row=self.row_position_base * 15,
                                                       column=self.col_position_base * 0,
                                                       rowspan=3)
        self.Mouse_Mode_Automatic_Line_Stop_Position_Entry = Entry(frame_main,
                                                                   textvariable=self.Mouse_Mode_Automatic_Line_Stop_Position)
        self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid(row=self.row_position_base * 15,
                                                                column=self.col_position_base * 1,
                                                                rowspan=3,
                                                                sticky=tk.EW,
                                                                padx=3)
        # 初始化控制模式界面
        self.Mouse_Control_Manager()

        '''矩形模式相关控件'''
        # 提示标签-起始位置
        self.Mouse_Mode_Automatic_Rectangle_Start_Label = Label(frame_main, text='选择矩形\n起始坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid(row=self.row_position_base * 14,
                                                             column=self.col_position_base * 0,
                                                             rowspan=3)
        self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry = Entry(frame_main,
                                                                         textvariable=self.Mouse_Mode_Automatic_Rectangle_Start_Position)
        self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid(row=self.row_position_base * 14,
                                                                      column=self.col_position_base * 1,
                                                                      rowspan=3,
                                                                      sticky=tk.EW,
                                                                      padx=3)
        # 提示标签-终止位置
        self.Mouse_Mode_Automatic_Rectangle_Stop_Label = Label(frame_main, text='选择矩形\n终止坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid(row=self.row_position_base * 15,
                                                            column=self.col_position_base * 0,
                                                            rowspan=3)
        self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry = Entry(frame_main,
                                                                        textvariable=self.Mouse_Mode_Automatic_Rectangle_Stop_Position)
        self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid(row=self.row_position_base * 15,
                                                                     column=self.col_position_base * 1,
                                                                     rowspan=3,
                                                                     sticky=tk.EW,
                                                                     padx=3)

        '''圆形模式相关控件'''
        # 提示标签-起始位置
        self.Mouse_Mode_Automatic_Circle_Start_Label = Label(frame_main, text='选择圆心\n起始坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Circle_Start_Label.grid(row=self.row_position_base * 14,
                                                          column=self.col_position_base * 0,
                                                          rowspan=3)
        self.Mouse_Mode_Automatic_Circle_Start_Position_Entry = Entry(frame_main,
                                                                      textvariable=self.Mouse_Mode_Automatic_Circle_Start_Position)
        self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid(row=self.row_position_base * 14,
                                                                   column=self.col_position_base * 1,
                                                                   rowspan=3,
                                                                   sticky=tk.EW,
                                                                   padx=3)
        # 提示标签-终止位置
        self.Mouse_Mode_Automatic_Circle_Stop_Label = Label(frame_main, text='选择半径\n终止坐标')
        # 起始坐标输入框
        self.Mouse_Mode_Automatic_Circle_Stop_Label.grid(row=self.row_position_base * 15,
                                                         column=self.col_position_base * 0,
                                                         rowspan=3)
        self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry = Entry(frame_main,
                                                                     textvariable=self.Mouse_Mode_Automatic_Circle_Stop_Position)
        self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid(row=self.row_position_base * 15,
                                                                  column=self.col_position_base * 1,
                                                                  rowspan=3,
                                                                  sticky=tk.EW,
                                                                  padx=3)
        '''记忆模式'''
        self.Mouse_Mode_Automatic_Memory_Label = Label(frame_main, text='请使用键盘进行快捷键控制')
        self.Mouse_Mode_Automatic_Memory_Label.grid(row=self.row_position_base * 15,
                                                    column=self.col_position_base * 1,
                                                    rowspan=3)

        # 辅助获取坐标按钮
        self.Mouse_Mode_Automatic_Get_Position_Button = Button(frame_main, text='辅助获取坐标',
                                                               command=self.Mouse_Automatic_Mode_Auxiliary_Get_Position)
        self.Mouse_Mode_Automatic_Get_Position_Button.grid(row=self.row_position_base * 14,
                                                           column=self.col_position_base * 2,
                                                           rowspan=3,
                                                           sticky=tk.EW,
                                                           padx=3
                                                           )

        # 确认坐标按钮
        self.Mouse_Mode_Automatic_Line_Confirm_Position_Button = Button(frame_main, text='确认坐标',
                                                                        command=self.Mouse_Automatic_Saving_Position)
        self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid(row=self.row_position_base * 16,
                                                                    column=self.col_position_base * 1,
                                                                    rowspan=3,
                                                                    sticky=tk.EW,
                                                                    padx=3
                                                                    )

        # 半自动控制模式
        self.Mouse_Mode_Half_Automatic_Radiobutton = Radiobutton(frame_main, text='半自动控制模式',
                                                                 variable=self.Mouse_Choose_Mode,
                                                                 value=2,
                                                                 command=self.Change_Execute_Mode)
        self.Mouse_Mode_Half_Automatic_Radiobutton.grid(row=self.row_position_base * 12,
                                                        column=self.col_position_base * 1,
                                                        rowspan=3)
        self.Mouse_Mode_Half_Automatic_Move_Label = Label(frame_main, text='移动多少距离\n算一次点击')
        self.Mouse_Mode_Half_Automatic_Move_Label.grid(row=self.row_position_base * 13,
                                                       column=self.col_position_base * 0,
                                                       rowspan=3)
        self.Mouse_Mode_Half_Automatic_Move_Entry = Entry(frame_main,
                                                          textvariable=self.Mouse_Mode_Half_Automatic_Move_Calculate_Con)
        self.Mouse_Mode_Half_Automatic_Move_Entry.grid(row=self.row_position_base * 13,
                                                       column=self.col_position_base * 1,
                                                       rowspan=3)
        self.Mouse_Mode_Half_Automatic_Time_Label = Label(frame_main, text='停止多少时间\n松开鼠标')
        self.Mouse_Mode_Half_Automatic_Time_Label.grid(row=self.row_position_base * 13,
                                                       column=self.col_position_base * 0,
                                                       rowspan=3)
        self.Mouse_Mode_Half_Automatic_Time_Entry = Entry(frame_main,
                                                          textvariable=self.Mouse_Mode_Half_Automatic_Time_Stop_Con)
        self.Mouse_Mode_Half_Automatic_Time_Entry.grid(row=self.row_position_base * 13,
                                                       column=self.col_position_base * 1,
                                                       rowspan=3)
        self.Mouse_Mode_Half_Automatic_Confirm_Button = Button(frame_main, text='确认修改',
                                                               command=self.Half_Automatic_Confirm_Command)
        self.Mouse_Mode_Half_Automatic_Confirm_Button.grid(row=self.row_position_base * 13,
                                                           column=self.col_position_base * 2,
                                                           rowspan=3)
        # 初始化控制模式界面
        self.Mouse_Control_Manager()
        self.Mouse_Automatic_Mode_Manager()
        self.Change_Execute_Mode()
        self.Half_Automatic_Confirm_Command()

        '''创建并运行相关长启动线程'''
        # 监听端口线程
        self.Th_SearchPort = threading.Thread(target=self.Monitor_COMPort)
        self.Th_SearchPort.setDaemon(True)
        self.Th_SearchPort.start()
        # 监听串口数据线程
        self.Th_ReadData = threading.Thread(target=self.Read_COMPort_Data)
        self.Th_ReadData.setDaemon(True)
        self.Th_ReadData.start()
        # 处理串口接收数据线程
        self.Th_DealReadData = threading.Thread(target=self.Deal_ReadData)
        self.Th_DealReadData.setDaemon(True)
        self.Th_DealReadData.start()

        # 键盘监听数据线程
        self.Th_KeyBoard_Monitor = threading.Thread(target=self.Monitor_KeyBoard)
        self.Th_KeyBoard_Monitor.setDaemon(True)
        self.Th_KeyBoard_Monitor.start()

        # 创建按压监听线程
        self.Th_Check_Drag_Global = threading.Thread(target=self.Th_Check_Drag)
        self.Th_Check_Drag_Global.setDaemon(True)
        self.Th_Check_Drag_Global.start()

        """创建分页二"""
        # 创建设置热键分页
        frame_setting = Frame(note)
        note.add(frame_setting, text="热键设置")
        '''创建相关UI'''
        # 初始化相关变量
        self.Setting_KeyBoard_Remember_Start = tk.StringVar()
        self.Setting_KeyBoard_Remember_Stop = tk.StringVar()
        self.Setting_KeyBoard_Start_Control = tk.StringVar()
        self.Setting_KeyBoard_Stop_Control = tk.StringVar()
        # 初始化界面
        self.Setting_KeyBoard_Title_Label = Label(frame_setting, text='*****  相关热键设置  *****')
        self.Setting_KeyBoard_Title_Label.grid(row=self.row_position_base * 0,
                                               column=self.col_position_base * 0, rowspan=3)
        # 开始鼠标路径记录热键
        self.Setting_KeyBoard_Remember_Start_Label = Label(frame_setting, text='开启鼠标位置记录热键')
        self.Setting_KeyBoard_Remember_Start_Entry = Entry(frame_setting,
                                                           textvariable=self.Setting_KeyBoard_Remember_Start)
        self.Setting_KeyBoard_Remember_Start_Label.grid(row=self.row_position_base * 1,
                                                        column=self.col_position_base * 0, rowspan=3)
        self.Setting_KeyBoard_Remember_Start_Entry.grid(row=self.row_position_base * 1,
                                                        column=self.col_position_base * 1, rowspan=3)
        # 停止鼠标路径记录热键
        self.Setting_KeyBoard_Remember_Stop_Label = Label(frame_setting, text='关闭鼠标位置记录热键')
        self.Setting_KeyBoard_Remember_Stop_Entry = Entry(frame_setting,
                                                          textvariable=self.Setting_KeyBoard_Remember_Stop)
        self.Setting_KeyBoard_Remember_Stop_Label.grid(row=self.row_position_base * 2,
                                                       column=self.col_position_base * 0, rowspan=3)
        self.Setting_KeyBoard_Remember_Stop_Entry.grid(row=self.row_position_base * 2,
                                                       column=self.col_position_base * 1, rowspan=3)

        # 开始鼠标点击控制热键
        self.Setting_KeyBoard_Start_Control_Label = Label(frame_setting, text='开启鼠标控制热键')
        self.Setting_KeyBoard_Start_Control_Entry = Entry(frame_setting,
                                                          textvariable=self.Setting_KeyBoard_Start_Control)
        self.Setting_KeyBoard_Start_Control_Label.grid(row=self.row_position_base * 3,
                                                       column=self.col_position_base * 0, rowspan=3)
        self.Setting_KeyBoard_Start_Control_Entry.grid(row=self.row_position_base * 3,
                                                       column=self.col_position_base * 1, rowspan=3)

        # 关闭鼠标点击控制热键
        self.Setting_KeyBoard_Stop_Control_Label = Label(frame_setting, text='关闭鼠标控制热键')
        self.Setting_KeyBoard_Stop_Control_Entry = Entry(frame_setting,
                                                         textvariable=self.Setting_KeyBoard_Stop_Control)
        self.Setting_KeyBoard_Stop_Control_Label.grid(row=self.row_position_base * 4,
                                                      column=self.col_position_base * 0, rowspan=3)
        self.Setting_KeyBoard_Stop_Control_Entry.grid(row=self.row_position_base * 4,
                                                      column=self.col_position_base * 1, rowspan=3)

        # 保存设置按钮
        self.Setting_KeyBoard_Saving_Button = Button(frame_setting, text="保存修改", command=self.Saving_Data)
        self.Setting_KeyBoard_Saving_Button.grid(row=self.row_position_base * 8,
                                                 column=self.col_position_base * 1, rowspan=3)
        # 初始化文件变量
        self.Initial_KeyBoard()
        pg.FAILSAFE = True  # 避免出现紧急情况
        pyautogui.PAUSE = 0.0001  # 修改最小移动速率

    """串口相关函数"""

    # 设置串口端口相关初始变量
    def Get_COMPort_Select(self, arge):
        if arge == 1:
            print('端口号初始化显示！')
        elif arge == 2:
            print('获取到串口数据！')
        self.COMPort = self.COMPort_Combobox.get()

    # 设置波特率相关初始变量
    def Get_Baud_Select(self, arge):
        if arge == 1:
            print('波特率初始化显示！')
        self.COMBaud = self.COMBaud_Combobox.get()

    # 设置校验位相关初始变量
    def Get_Check_Select(self, arge):
        if arge == 1:
            print('校验位初始化显示！')
        if self.COMCheck_Combobox.get() == '无':
            self.COMCheck = serial.PARITY_NONE
        elif self.COMCheck_Combobox.get() == '奇':
            self.COMCheck = serial.PARITY_ODD
        elif self.COMCheck_Combobox.get() == '偶':
            self.COMCheck = serial.PARITY_EVEN

    # 设置数据位相关初始变量
    def Get_Data_Bit_Select(self, arge):
        if arge == 1:
            print('数据位初始化显示！')
        self.COMDataBit = self.COMDataBit_Combobox.get()

    # 设置停止位相关初始变量
    def Get_Stop_Bit_Select(self, arge):
        if arge == 1:
            print('停止位初始化显示！')
        self.COMStopBit = self.COMStopBit_Combobox.get()

    # 串口检测线程 常启动
    def Monitor_COMPort(self):
        Is_Get = False
        while True:
            # 检测存在的端口
            if self.COMObj is None:  # 只要端口未连接那就一直检测
                self.COMList = list(serial.tools.list_ports.comports())
                Is_Get = True
                time.sleep(1)  # 线程休眠，防止占用过高
            if Is_Get and len(self.COMList) != 0:
                port_str_list = []  # 缓冲数组
                for i in range(len(self.COMList)):
                    lines = str(self.COMList[i])
                    str_list = lines.split(" ")
                    port_str_list.append(str_list[0])
                self.COMPort_Combobox["value"] = port_str_list
                self.COMPort_Combobox.current(0)
                self.Get_COMPort_Select(2)
                Is_Get = False
            time.sleep(0.001)

    # 打开串口
    def Open_COMPort(self):
        if self.COMBaud == "" \
                or self.COMDataBit == "" \
                or self.COMCheck == "" \
                or self.COMStopBit == "" \
                or self.COMPort == "":
            print("请输入正确的串口格式！")
            return
        Port = self.COMPort
        BaudRate = int(self.COMBaud)
        ByteSize = int(self.COMDataBit)
        Parity = self.COMCheck
        StopBits = int(self.COMStopBit)
        if self.COMObj is not None:
            print("不要重复点击串口！")
        else:
            self.COMObj = serial.Serial(port=Port,
                                        baudrate=BaudRate,
                                        bytesize=ByteSize,
                                        parity=Parity,
                                        stopbits=StopBits,
                                        timeout=1)
            print("串口打开成功！")
            # 向从设备发送设备信息请求
            self.Write_COMPort_Data("Device_InFo")

    # 关闭串口
    def Close_COMPort(self):
        if self.COMObj is not None:
            try:
                self.Device_Number = 0
                self.COMObj.close()
            except:
                self.COMObj = None
                print("连接被中断，请检查连接！")
            print("串口已关闭！")
        else:
            print('未连接到串口！')

    # 读取串口数据线程
    def Read_COMPort_Data(self):
        while True:
            if self.COMObj is not None:
                try:
                    read_data = self.COMObj.read(self.COMObj.in_waiting)  # 读取数据
                    if read_data != b'':
                        self.ReadBuff = read_data
                        # print(self.ReadBuff)
                except:
                    self.COMObj = None
                    self.COMList.clear()
                    self.COMPort_Combobox["value"] = self.COMList
                    self.COMPort_Combobox.set("")
                    print("端口数据读取失败！请检查连线！")

                try:
                    self.ReadBuff = self.ReadBuff.decode("utf-8")
                    if len(self.ReadBuff) > 0:
                        self.COM_Queue.put(self.ReadBuff)  # 向消息处理线程发送数据
                except:
                    pass

            time.sleep(0.001)

    # 数据发送-向设备发送数据 输入变量为data
    def Write_COMPort_Data(self, data):
        if self.COMObj is not None and self.COMObj.isOpen():
            try:
                self.COMObj.write(data.encode("utf-8"))  # 向设备发送数据
                print("数据发送成功！")
            except:
                self.COMObj = None
                self.COMList.clear()
                self.COMPort_Combobox["value"] = self.COMList
                self.COMPort_Combobox.set("")
                print("端口数据写入失败！请检查连线！")

    """键盘监控主要函数"""

    # 监听键盘事件功能是否开始
    def KeyBoard_Is_Open(self):
        if self.KeyBoard_CheckBox_Is_Control.get() == 0:
            self.KeyBoard_Is_Control = False
            print("失去键盘监听执行权限！")
        elif self.KeyBoard_CheckBox_Is_Control.get() == 1:
            self.KeyBoard_Is_Control = True
            print("获取键盘监听执行权限！")

    # 键盘监听事件管理函数
    def Monitor_KeyBoard(self):
        # 创建相关监听函数
        # 创建子线程
        # 记录鼠标位移线程
        keyboard.add_hotkey(self.KeyBoard_Combine_Key_Start_Remember,
                            self.KeyBoard_Start_Recode_Mouse_Position)
        # 停止鼠标位移线程
        keyboard.add_hotkey(self.KeyBoard_Combine_Key_Stop_Remember,
                            self.KeyBoard_Stop_Recode_Mouse_Position)

        # 开始控制鼠标线程
        keyboard.add_hotkey(self.KeyBoard_Combine_Key_Start_Control,
                            self.Mouse_Control_Manager)

        # 停止控制鼠标线程
        keyboard.add_hotkey(self.KeyBoard_Combine_Key_Stop_Control,
                            self.Mouse_Control_Stop)

        keyboard.wait('ctrl+q')  # 一直监听前面的程序

    '''键盘按钮按下处理函数'''

    # 开始记录鼠标移动位置坐标
    def KeyBoard_Start_Recode_Mouse_Position(self):
        if self.KeyBoard_Is_Control:
            if self.Mouse_Is_Remember is not True:
                if self.Mouse_Automatic_Is_Control:
                    print("正在进行控制，请勿重新记录位置！")
                    return
                self.Mouse_Is_Remember = True
                self.Mouse_Remember_Position = []  # 清空之前的记录数组
                self.Position_Memory_Is_Change = True  # 说明数据发生了变化
                th_remember_mouse_position = threading.Thread(target=self.Th_KeyBoard_Start_Recode_Mouse_Position)
                th_remember_mouse_position.setDaemon(True)
                th_remember_mouse_position.start()
            else:
                print("正在采集数据，请不要重复采集数据！")
        else:
            print("请勾选键盘监听选择框进行相关控制！")

    # 相关位置记录线程
    def Th_KeyBoard_Start_Recode_Mouse_Position(self):
        if self.KeyBoard_Is_Control:
            print("开始进行鼠标位置记录")
            max_num = 5000  # 最多记录两万组坐标
            n = 1
            while self.Mouse_Is_Remember:
                if n >= max_num:
                    print("超出最大记录坐标！强制退出记录")
                    self.Mouse_Is_Remember = False
                    break
                if not self.KeyBoard_Is_Control:
                    print("键盘控制权限丢失，停止记录")
                    break
                x, y = pg.position()  # 获取当前鼠标的坐标(像素)
                self.Mouse_Remember_Position.append((x, y))
                time.sleep(self.Mouse_Remember_gap)  # 采样间隔
                n = n + 1
        else:
            print("请勾选键盘监听选择框进行相关控制！")

    # 停止记录鼠标移动位置坐标
    def KeyBoard_Stop_Recode_Mouse_Position(self):
        if self.Mouse_Automatic_Is_Control:
            print("正在进行控制，请勿重新记录位置！")
            return
        if self.KeyBoard_Is_Control:
            print("停止记录鼠标位置！")
            if self.Mouse_Is_Remember:
                print("鼠标位置记录完毕！")
                self.Mouse_Is_Remember = False
        else:
            print("请勾选键盘监听选择框进行相关控制！")

    # 数据处理线程-数据接收预处理，与接收时间的计算
    def Deal_ReadData(self):
        while True:
            if self.Is_Adjust is not True:
                n = 0
                # 记录当前时间
                StartTime = time.time()
                read_data = self.COM_Queue.get()
                read_data = read_data.strip().replace('\n', '').replace('\r', '')
                # print(read_data)
                if len(read_data) == 1:
                    # 记录当前时间
                    EndTime = time.time()
                    Time_Gap = int((EndTime - StartTime) * 1000)
                    if read_data == '#':
                        self.Device_Number = int(self.COM_Queue.get())
                        if self.COM_Queue.get().replace('\r', '').replace('\n', '') != '#':
                            print("接收数据有误！已重置为10，请重新连接设备！")
                            self.Device_Number = 10
                        else:
                            print("检测设备数量:", self.Device_Number)
                    if read_data == "P":
                        print("设备数据为: ")
                        n = 0
                        while True:
                            data = self.COM_Queue.get().replace('\r', '').replace('\n', '')
                            if n > 1000:
                                print('传输数据发送错误')
                                break
                            if data == "P":
                                print("退出对设备数据的监测！")
                                break
                            # 设备数据
                            print('设备数据', data)
                            n = n + 1
                            time.sleep(0.01)
                    if read_data == '*':
                        print("设备自检存在异常，请检查连线或者重新校准设备！")
                    if self.KeyBoard_Is_Control:
                        if self.Mouse_Is_Control:
                            if self.Mouse_Automatic_Is_Control:
                                self.Data_Queue.put((read_data, Time_Gap))
                else:
                    # 记录当前时间
                    EndTime = time.time()
                    Time_Gap = int((EndTime - StartTime) * 1000) / len(read_data)  # 均分
                    if read_data == '#':
                        self.Device_Number = int(self.COM_Queue.get())
                        if self.COM_Queue.get().replace('\r', '').replace('\n', '') != '#':
                            print("接收数据有误！已重置为10，请重新连接设备！")
                            self.Device_Number = 10
                        else:
                            print("检测设备数量:", self.Device_Number)
                    if read_data == 'P':
                        print("设备数据为: ")
                        n = 0
                        while True:
                            data = self.COM_Queue.get().replace('\r', '').replace('\n', '')
                            if n > 1000:
                                print('传输数据发送错误')
                                break
                            if data == 'P':
                                break
                            # 设备数据
                            print(data)
                            n = n + 1
                            time.sleep(0.01)
                    if read_data == '*':
                        print("设备自检存在异常，请检查连线或者重新校准设备！")
                    if self.KeyBoard_Is_Control:
                        if self.Mouse_Is_Control:
                            if self.Mouse_Automatic_Is_Control:
                                for data in read_data:
                                    self.Data_Queue.put((data, Time_Gap))
            else:
                self.Th_Inform = True
                time.sleep(0.01)

    """鼠标控制主要函数"""

    def Mouse_Check_IsOpen(self):
        if self.Mouse_CheckBox_Is_Control.get() == 1:
            self.Mouse_Is_Control = True  # 允许鼠标控制
            print('鼠标控制-获取权限！')
        else:
            self.Mouse_Is_Control = False
            print('鼠标控制-失去权限！')

    # 开始控制鼠标-多种控制方式的管理函数
    def Mouse_Control_Manager(self):
        if self.KeyBoard_Is_Control:
            if self.Mouse_Is_Control:
                if self.Mouse_Automatic_Is_Control is not True:
                    self.Mouse_Automatic_Is_Control = True
                    # 开启控制线程
                    th_mouse_start_control = threading.Thread(target=self.Th_Mouse_Start_Control)
                    th_mouse_start_control.setDaemon(True)
                    th_mouse_start_control.start()
                    print("开始控制鼠标！")
                else:
                    print("请不要重复控制，先终止当前的控制线程，再重新创建线程！")
            else:
                print("请勾选鼠标控制选择框进行相关控制！")
        else:
            print("请勾选键盘监听选择框进行相关控制！")

    # 停止鼠标控制
    def Mouse_Control_Stop(self):
        if self.KeyBoard_Is_Control:
            if self.Mouse_Automatic_Is_Control:
                print("尝试停止鼠标控制")
                self.Mouse_Automatic_Is_Control = False
        else:
            print("请勾选键盘监听选择框进行相关控制！")

    # 鼠标控制线程
    def Th_Mouse_Start_Control(self):
        while True:
            # 获取数据
            read_data = None
            time_gap = None
            try:
                read_data, time_gap = self.Data_Queue.get(timeout=0.05)  # 50ms的超时时间
            except:
                pass
            # if read_data is not None and time_gap is not None:
            #     print("数据: " + read_data + " 时间间隔: " + str(time_gap) + 'ms')
            if self.Mouse_Is_Control is not True:
                print("因为鼠标控制权限被取消，退出控制")
                break
            if self.KeyBoard_Is_Control is not True:
                print("因为键盘控制权限被取消，退出控制")
                break
            if self.Mouse_Automatic_Is_Control is not True:
                print("鼠标控制停止成功！")
                break
            # 根据相关的设置执行相关的控制
            if self.Mouse_Is_Automatic:  # 如果是全自动模式
                # 设置最长执行时间
                if read_data is not None:
                    if time_gap > 2000:
                        time_gap = 2000  # 设置最长执行时间
                if self.Mouse_Mode_Automatic_Mode.get() == '直线模式' and \
                        len(self.Mouse_Mode_Automatic_Line_Position) > 0:
                    # 根据设备数将区间进行等分
                    if self.Position_Line_Is_Change:
                        self.line_position_divide = []
                        # 获取两点坐标
                        x1 = self.Mouse_Mode_Automatic_Line_Position[0][0]
                        y1 = self.Mouse_Mode_Automatic_Line_Position[0][1]
                        x2 = self.Mouse_Mode_Automatic_Line_Position[1][0]
                        y2 = self.Mouse_Mode_Automatic_Line_Position[1][1]
                        dis_x = x2 - x1
                        dis_y = y2 - y1
                        try:
                            dis_x_step = dis_x / self.Device_Number
                            dis_y_step = dis_y / self.Device_Number
                            self.line_position_divide.append((x1, y1))  # 加入自身位置 10个点分成9段
                            for i in range(self.Device_Number):
                                self.line_position_divide.append(
                                    (int(x1 + (i + 1) * dis_x_step), int(y1 + (i + 1) * dis_y_step)))
                        except:
                            print("注意！设备数为0！")
                        self.Position_Line_Is_Change = False
                    # 执行鼠标控制命令
                    if read_data is not None:
                        if is_number(read_data):  # 如果是数字
                            precision = 5  # 步长
                            direction_position = self.line_position_divide[int(read_data)]  # 全部都是从0开始
                            # 判断拖动的方式
                            if self.Mouse_Mode_Click_Mode.get() == "单击":
                                mouse = pynput.mouse.Controller()
                                # 计算函数
                                k = (self.line_position_divide[0][1] - self.line_position_divide[1][1]) / (
                                        self.line_position_divide[0][0] - self.line_position_divide[1][0])
                                # if abs(k) < 10:
                                #     x, y = mouse.position
                                #     time_divide = time_gap / (abs(x - direction_position[0]) / precision)
                                #     if direction_position[0] - x < 0:
                                #         precision = - precision
                                #     for i in np.arange(x, direction_position[0], precision):
                                #         x1 = i
                                #         y1 = k * (x1 - self.line_position_divide[1][0]) + self.line_position_divide[1][1]
                                #         mouse.position = (x1, y1)
                                #         if self.Mouse_Automatic_Is_Control is not True:
                                #             break
                                #         time.sleep(time_divide / 1000)
                                # else:
                                #     mouse.position = (direction_position[0], direction_position[1])
                                #     time.sleep(time_gap / 1000)
                                mouse.position = (direction_position[0], direction_position[1])
                                time.sleep(0.01)
                                # time.sleep(time_gap / 1000)
                                # 判断执行的方式
                                if self.Mouse_Mode_Control_Mode.get() == "左键":
                                    mouse.click(pynput.mouse.Button.left, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                    mouse.click(pynput.mouse.Button.right, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                    mouse.click(pynput.mouse.Button.middle, count=1)

                            elif self.Mouse_Mode_Click_Mode.get() == "长按":
                                if self.mouse_drag is None:
                                    self.mouse_drag = pynput.mouse.Controller()
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                if self.Mouse_Is_Drag is not True:
                                    self.Mouse_Is_Drag = True
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                # 计算函数
                                # k = (self.line_position_divide[0][1] - self.line_position_divide[1][1]) / (
                                #         self.line_position_divide[0][0] - self.line_position_divide[1][0])
                                # x, y = self.mouse_drag.position
                                # time_divide = time_gap / (abs(x - direction_position[0]) / precision)
                                # if direction_position[0] - x < 0:
                                #     precision = -1
                                # for i in np.arange(x, direction_position[0], precision):
                                #     x1 = i
                                #     y1 = k * (x1 - self.line_position_divide[1][0]) + self.line_position_divide[1][1]
                                #     self.mouse_drag.position = (x1, y1)
                                #     if self.Mouse_Automatic_Is_Control is not True:
                                #         break
                                self.mouse_drag.position = (direction_position[0], direction_position[1])
                                time.sleep(0.01)
                                # time.sleep(time_gap / 1000)
                elif self.Mouse_Mode_Automatic_Mode.get() == '矩形模式' and \
                        len(self.Mouse_Mode_Automatic_Rectangle_Position) > 0:
                    if self.Position_Rectangle_Is_Change:
                        self.rectangle_position_divide = []
                        self.memory_last_rectangle_position = 0  # 初始化上次的位置
                        temp = []
                        # 获取左上角坐标与右下角坐标
                        x1 = self.Mouse_Mode_Automatic_Rectangle_Position[0][0]
                        y1 = self.Mouse_Mode_Automatic_Rectangle_Position[0][1]
                        x2 = self.Mouse_Mode_Automatic_Rectangle_Position[1][0]
                        y2 = self.Mouse_Mode_Automatic_Rectangle_Position[1][1]
                        # 将所有坐标从二维转变为一维
                        precision = 0.1
                        step_x12 = 1
                        step_x21 = 1
                        step_y12 = 1
                        step_y21 = 1
                        if x1 < x2:
                            step_x12 = 1 * precision
                            step_x21 = -1 * precision
                        else:
                            step_x12 = -1 * precision
                            step_x21 = 1 * precision
                        if y1 < y2:
                            step_y12 = 1 * precision
                            step_y21 = -1 * precision
                        else:
                            step_y12 = -1 * precision
                            step_y21 = 1 * precision
                        for i in np.arange(x1, x2, step_x12):
                            temp.append((i, y1))
                        for i in np.arange(y1, y2, step_y12):
                            temp.append((x2, i))
                        for i in np.arange(x2, x1, step_x21):
                            temp.append((i, y2))
                        for i in np.arange(y2, y1, step_y21):
                            temp.append((x1, i))
                        self.rectangle_position_all = temp
                        try:
                            step = int(len(temp) / (self.Device_Number + 1))
                            for i in range(self.Device_Number + 1):
                                self.rectangle_position_divide.append((int(temp[i * step][0]), int(temp[i * step][1])))
                        except:
                            print("注意！设备数为0！")
                        self.Position_Rectangle_Is_Change = False
                    # 执行鼠标控制命令
                    if read_data is not None:
                        if is_number(read_data):  # 如果是数字
                            direction_position = self.rectangle_position_divide[int(read_data)]  # 全部都是从0开始
                            # 判断拖动的方式
                            if self.Mouse_Mode_Click_Mode.get() == "单击":
                                mouse = pynput.mouse.Controller()
                                # 根据上一次的坐标来判断是前进还是后退
                                step_move = int(
                                    len(self.rectangle_position_all) / (self.Device_Number * 5))  # 默认为正向
                                if step_move == 0:
                                    step_move = 1
                                if self.memory_last_rectangle_position > int(read_data):
                                    step_move = -step_move
                                else:
                                    step_move = step_move
                                step = int(len(self.rectangle_position_all) / self.Device_Number)
                                self.rectangle_position_all = np.array(self.rectangle_position_all)
                                time_divide = time_gap / (step / abs(step_move))
                                for i in np.arange(self.memory_last_rectangle_position * step, int(read_data) * step,
                                                   step_move):
                                    if i > len(self.rectangle_position_all) or i < 0:
                                        continue
                                    mouse.position = (
                                        self.rectangle_position_all[i][0], self.rectangle_position_all[i][1])
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                                # time.sleep(time_gap / 1000)
                                # 判断执行的方式
                                if self.Mouse_Mode_Control_Mode.get() == "左键":
                                    mouse.click(pynput.mouse.Button.left, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                    mouse.click(pynput.mouse.Button.right, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                    mouse.click(pynput.mouse.Button.middle, count=1)
                                self.memory_last_rectangle_position = int(read_data)  # 更新位置
                            elif self.Mouse_Mode_Click_Mode.get() == "长按":
                                if self.mouse_drag is None:
                                    self.mouse_drag = pynput.mouse.Controller()
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                if self.Mouse_Is_Drag is not True:
                                    self.Mouse_Is_Drag = True
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                # 根据上一次的坐标来判断是前进还是后退
                                step_move = int(len(self.rectangle_position_all) / (
                                        self.Device_Number * 5))  # 默认为正向, 最多200个点
                                if step_move == 0:
                                    step_move = 1
                                if self.memory_last_rectangle_position > int(read_data):
                                    step_move = -step_move
                                else:
                                    step_move = step_move
                                step = int(len(self.rectangle_position_all) / self.Device_Number)
                                self.rectangle_position_all = np.array(self.rectangle_position_all)
                                time_divide = time_gap / (step / abs(step_move))
                                for i in np.arange(self.memory_last_rectangle_position * step, int(read_data) * step,
                                                   step_move):
                                    if i > len(self.rectangle_position_all) or i < 0:
                                        continue
                                    self.mouse_drag.position = (
                                        self.rectangle_position_all[i][0], self.rectangle_position_all[i][1])
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                                self.memory_last_rectangle_position = int(read_data)  # 更新位置
                elif self.Mouse_Mode_Automatic_Mode.get() == '圆形模式' and \
                        len(self.Mouse_Mode_Automatic_Circle_Position) > 0:
                    precision = 10  # 1度
                    if self.Position_Circle_Is_Change:
                        self.circle_position_divide = []
                        # 获取圆心坐标与半径
                        x1 = int((self.Mouse_Mode_Automatic_Circle_Position[0][0] +
                                  self.Mouse_Mode_Automatic_Circle_Position[1][0]) / 2)
                        y1 = int((self.Mouse_Mode_Automatic_Circle_Position[0][1] +
                                  self.Mouse_Mode_Automatic_Circle_Position[1][1]) / 2)
                        d1 = abs(
                            self.Mouse_Mode_Automatic_Circle_Position[1][0] -
                            self.Mouse_Mode_Automatic_Circle_Position[0][0])
                        d2 = abs(
                            self.Mouse_Mode_Automatic_Circle_Position[1][1] -
                            self.Mouse_Mode_Automatic_Circle_Position[0][1])
                        d = min(d1, d2)
                        self.circle_r = int(d / 2)
                        self.circle_x = x1
                        self.circle_y = y1
                        self.circle_tha_step = 360 / (self.Device_Number + 1)
                        try:
                            tha_step = 360 / (self.Device_Number + 1)  # 获取角度
                            for i in range(self.Device_Number + 1):
                                self.circle_position_divide.append(tha_step * i)
                        except:
                            print("注意！设备数为0！")
                        self.Position_Circle_Is_Change = False
                    # 执行鼠标控制命令
                    if read_data is not None:
                        if is_number(read_data):  # 如果是数字
                            direction_tha = self.circle_position_divide[int(read_data)]  # 获取角度
                            # 判断拖动的方式
                            if self.Mouse_Mode_Click_Mode.get() == "单击":
                                mouse = pynput.mouse.Controller()
                                x1, y1 = pg.position()
                                current_tha = 0
                                if y1 != self.circle_y and x1 != self.circle_x:
                                    current_tha = np.arctan((y1 - self.circle_y) / (x1 - self.circle_x)
                                                            )
                                else:
                                    if x1 == self.circle_x and y1 > self.circle_y:
                                        current_tha = np.pi * 0.5
                                    else:
                                        current_tha = np.pi * 1.5
                                    if y1 == self.circle_y and x1 > self.circle_x:
                                        current_tha = 0
                                    else:
                                        current_tha = np.pi
                                current_tha = current_tha * 180 / np.pi
                                if x1 < self.circle_x and y1 > self.circle_y:
                                    current_tha = current_tha + 180
                                elif x1 < self.circle_x and y1 < self.circle_y:
                                    current_tha = current_tha + 180
                                elif x1 > self.circle_x and y1 < self.circle_y:
                                    current_tha = current_tha + 360
                                time_divide = 1
                                try:
                                    time_divide = time_gap / (abs(direction_tha - current_tha) / precision)
                                except:
                                    pass
                                if current_tha > direction_tha:
                                    precision = -precision
                                for i in np.arange(current_tha, direction_tha, precision):
                                    x2 = int(self.circle_x + self.circle_r * np.cos(i / 180 * np.pi))
                                    y2 = int(self.circle_y + self.circle_r * np.sin(i / 180 * np.pi))
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                        # 判断执行的方式
                                    mouse.position = (x2, y2)
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                                if self.Mouse_Mode_Control_Mode.get() == "左键":
                                    mouse.click(pynput.mouse.Button.left, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                    mouse.click(pynput.mouse.Button.right, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                    mouse.click(pynput.mouse.Button.middle, count=1)
                            elif self.Mouse_Mode_Click_Mode.get() == "长按":
                                if self.mouse_drag is None:
                                    self.mouse_drag = pynput.mouse.Controller()
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                if self.Mouse_Is_Drag is not True:
                                    self.Mouse_Is_Drag = True
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                # 计算坐标
                                x1, y1 = pg.position()
                                current_tha = 0
                                if y1 != self.circle_y and x1 != self.circle_x:
                                    current_tha = np.arctan((y1 - self.circle_y) / (x1 - self.circle_x)
                                                            )
                                else:
                                    if x1 == self.circle_x and y1 > self.circle_y:
                                        current_tha = np.pi * 0.5
                                    else:
                                        current_tha = np.pi * 1.5
                                    if y1 == self.circle_y and x1 > self.circle_x:
                                        current_tha = 0
                                    else:
                                        current_tha = np.pi
                                current_tha = current_tha * 180 / np.pi
                                if x1 < self.circle_x and y1 > self.circle_y:
                                    current_tha = current_tha + 180
                                elif x1 < self.circle_x and y1 < self.circle_y:
                                    current_tha = current_tha + 180
                                elif x1 > self.circle_x and y1 < self.circle_y:
                                    current_tha = current_tha + 360
                                time_divide = 1
                                try:
                                    time_divide = time_gap / (abs(direction_tha - current_tha) / precision)
                                except:
                                    pass
                                if current_tha > direction_tha:
                                    precision = -precision
                                for i in np.arange(current_tha, direction_tha, precision):
                                    x2 = int(self.circle_x + self.circle_r * np.cos(i / 180 * np.pi))
                                    y2 = int(self.circle_y + self.circle_r * np.sin(i / 180 * np.pi))
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                        # 判断执行的方式
                                    self.mouse_drag.position = (x2, y2)
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                elif self.Mouse_Mode_Automatic_Mode.get() == '记忆模式' and \
                        len(self.Mouse_Remember_Position) > 0:
                    if self.Position_Memory_Is_Change:
                        self.memory_position_divide = []
                        self.memory_last_memory_position = 0
                        # 分布添加
                        try:
                            step = int(len(self.Mouse_Remember_Position) / self.Device_Number)
                            for i in range(self.Device_Number):
                                self.memory_position_divide.append((int(self.Mouse_Remember_Position[i * step][0]),
                                                                    int(self.Mouse_Remember_Position[i * step][1])))
                        except:
                            print("注意！设备数为0！")
                        self.Position_Memory_Is_Change = False
                    # 执行鼠标控制命令
                    if read_data is not None:
                        if is_number(read_data):  # 如果是数字
                            direction_position = self.memory_position_divide[int(read_data)]  # 全部都是从0开始
                            # 判断拖动的方式
                            if self.Mouse_Mode_Click_Mode.get() == "单击":
                                mouse = pynput.mouse.Controller()
                                # 根据上一次的坐标来判断是前进还是后退
                                step_move = int(
                                    len(self.Mouse_Remember_Position) / (self.Device_Number * 50))  # 默认为正向
                                if step_move == 0:
                                    step_move = 1
                                if self.memory_last_memory_position > int(read_data):
                                    step_move = -step_move
                                else:
                                    step_move = step_move
                                step = int(len(self.Mouse_Remember_Position) / self.Device_Number)
                                self.Mouse_Remember_Position = np.array(self.Mouse_Remember_Position)
                                time_divide = time_gap / (step / abs(step_move))
                                for i in np.arange(self.memory_last_memory_position * step,
                                                   int(read_data) * step, step_move):
                                    if i > len(self.Mouse_Remember_Position) or i < 0:
                                        continue
                                    mouse.position = (
                                        self.Mouse_Remember_Position[i][0], self.Mouse_Remember_Position[i][1])
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                                # 判断执行的方式
                                if self.Mouse_Mode_Control_Mode.get() == "左键":
                                    mouse.click(pynput.mouse.Button.left, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                    mouse.click(pynput.mouse.Button.right, count=1)
                                elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                    mouse.click(pynput.mouse.Button.middle, count=1)
                                self.memory_last_memory_position = int(read_data)  # 更新位置
                            elif self.Mouse_Mode_Click_Mode.get() == "长按":
                                if self.mouse_drag is None:
                                    self.mouse_drag = pynput.mouse.Controller()
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                if self.Mouse_Is_Drag is not True:
                                    self.Mouse_Is_Drag = True
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        self.mouse_drag.press(pynput.mouse.Button.left)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        self.mouse_drag.press(pynput.mouse.Button.right)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        self.mouse_drag.press(pynput.mouse.Button.middle)
                                # 根据上一次的坐标来判断是前进还是后退
                                step_move = int(len(self.Mouse_Remember_Position) / (
                                        self.Device_Number * 100))  # 默认为正向, 最多200个点
                                if step_move == 0:
                                    step_move = 1
                                if self.memory_last_memory_position > int(read_data):
                                    step_move = -step_move
                                else:
                                    step_move = step_move
                                step = int(len(self.Mouse_Remember_Position) / self.Device_Number)
                                self.Mouse_Remember_Position = np.array(self.Mouse_Remember_Position)
                                # time_divide = time_gap / (step / abs(step_move))
                                for i in np.arange(self.memory_last_memory_position * step,
                                                   int(read_data) * step,
                                                   step_move):
                                    if i > len(self.Mouse_Remember_Position) or i < 0:
                                        continue
                                    self.mouse_drag.position = (
                                        self.Mouse_Remember_Position[i][0], self.Mouse_Remember_Position[i][1])
                                    if self.Mouse_Automatic_Is_Control is not True:
                                        break
                                    time.sleep(0.01)
                                    # time.sleep(time_divide / 1000)
                                self.memory_last_memory_position = int(read_data)  # 更新位置
                else:
                    print('路径端点未选择，退出控制！')
                    break
            else:  # 如果是半自动模式
                if self.Mouse_Mode_Click_Mode.get() == "单击":
                    if read_data is not None:
                        if is_number(read_data):  # 如果是数字
                            if self.Mouse_Mode_Half_Automatic_Move_Calculate.get() is None or self.Mouse_Mode_Half_Automatic_Move_Calculate.get() == 0:
                                # 说明输入错误
                                print("参数输入错误，请重新输入！")
                                self.Mouse_Mode_Half_Automatic_Move_Calculate.set(1)
                                break
                            else:
                                # 获取设置的值
                                current_position = int(read_data)
                                # 计算累计差距
                                self.Mouse_Mode_Half_Automatic_Last_Sum_division = self.Mouse_Mode_Half_Automatic_Last_Sum_division + abs(
                                    current_position - self.Mouse_Mode_Half_Automatic_Last_Click_Position)
                                # 获取设置的值
                                move_set = self.Mouse_Mode_Half_Automatic_Move_Calculate.get()
                                if self.Mouse_Mode_Half_Automatic_Last_Sum_division > move_set:
                                    mouse = pynput.mouse.Controller()
                                    # 判断执行的方式
                                    if self.Mouse_Mode_Control_Mode.get() == "左键":
                                        mouse.click(pynput.mouse.Button.left, count=1)
                                    elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                        mouse.click(pynput.mouse.Button.right, count=1)
                                    elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                        mouse.click(pynput.mouse.Button.middle, count=1)
                                    self.Mouse_Mode_Half_Automatic_Last_Sum_division = 0  # 重新开始计数
                                self.Mouse_Mode_Half_Automatic_Last_Click_Position = current_position  # 更新
                elif self.Mouse_Mode_Click_Mode.get() == '长按':
                    if self.Mouse_Mode_Half_Automatic_Time_Stop.get() is None or self.Mouse_Mode_Half_Automatic_Time_Stop.get() == 0:
                        # 说明输入错误
                        print("参数输入错误，请重新输入！")
                        self.Mouse_Mode_Half_Automatic_Move_Calculate.set(1)
                        break
                    else:
                        current_time = time.time()
                        if self.mouse_drag is None:  # 创建鼠标控件
                            self.mouse_drag = pynput.mouse.Controller()
                        # 如果存在运动，并且大于2，那才开始执行按压控制
                        if read_data is not None:
                            if is_number(read_data):  # 如果是数字
                                # 获取设置的值
                                current_position = int(read_data)
                                # 计算累计差距
                                self.Mouse_Mode_Half_Automatic_Last_Sum_division = self.Mouse_Mode_Half_Automatic_Last_Sum_division + abs(
                                    current_position - self.Mouse_Mode_Half_Automatic_Last_Click_Position)
                                self.time_gap_sum = self.time_gap_sum + time_gap / 1000
                                # 默认差距至少得2
                                if self.Mouse_Mode_Half_Automatic_Last_Sum_division > 2:
                                    self.Mouse_Mode_Half_Automatic_Start_Time = time.time()
                                    # 检测时间是否满足要求
                                    if self.time_gap_sum < self.Mouse_Mode_Half_Automatic_Time_Stop.get():
                                        self.Time_Num_Check = True
                                    else:
                                        # print(self.time_gap_sum, self.Mouse_Mode_Half_Automatic_Time_Stop.get())
                                        pass
                                    self.Mouse_Mode_Half_Automatic_Last_Sum_division = 0
                                    self.Mouse_Mode_Half_Automatic_Last_Click_Position = current_position  # 更新
                                    self.time_gap_sum = 0  # 清零

                        time_sub = current_time - self.Mouse_Mode_Half_Automatic_Start_Time
                        # 如果维持的时间超过设定的时间，处于运行态时才处理
                        if time_sub > self.Mouse_Mode_Half_Automatic_Time_Stop.get() and self.Time_Num_Check:
                            # 如果两次时间过长，那就取消按压，并取消计数
                            self.Time_Num_Check = False
                            # 判断执行的方式
                            if self.Mouse_Mode_Control_Mode.get() == "左键":
                                self.mouse_drag.release(pynput.mouse.Button.left)
                            elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                self.mouse_drag.release(pynput.mouse.Button.right)
                            elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                self.mouse_drag.release(pynput.mouse.Button.middle)
                        # 如果条件满足，那就执行按压并维持按压
                        if self.Mouse_Is_Drag is not True and self.Time_Num_Check:
                            self.Mouse_Is_Drag = True
                            # 判断执行的方式
                            if self.Mouse_Mode_Control_Mode.get() == "左键":
                                self.mouse_drag.press(pynput.mouse.Button.left)
                            elif self.Mouse_Mode_Control_Mode.get() == "右键":
                                self.mouse_drag.press(pynput.mouse.Button.right)
                            elif self.Mouse_Mode_Control_Mode.get() == "中键":
                                self.mouse_drag.press(pynput.mouse.Button.middle)

        self.Mouse_Automatic_Is_Control = False
        if self.mouse_drag is not None:
            if self.Mouse_Mode_Control_Mode.get() == "左键":
                self.mouse_drag.release(pynput.mouse.Button.left)
            elif self.Mouse_Mode_Control_Mode.get() == "右键":
                self.mouse_drag.release(pynput.mouse.Button.right)
            elif self.Mouse_Mode_Control_Mode.get() == "中键":
                self.mouse_drag.release(pynput.mouse.Button.middle)
            self.mouse_drag = None  # 重置
        print("退出控制线程！")

    # 半自动选项确认按钮
    def Half_Automatic_Confirm_Command(self):
        self.Mouse_Mode_Half_Automatic_Time_Stop.set(self.Mouse_Mode_Half_Automatic_Time_Stop_Con.get())
        self.Mouse_Mode_Half_Automatic_Move_Calculate.set(self.Mouse_Mode_Half_Automatic_Move_Calculate_Con.get())

    # 选择控制模式函数，包括全自动模式和半自动模式，部分控键的隐藏与显示
    def Change_Execute_Mode(self):
        if self.Mouse_Choose_Mode.get() == 1:
            print('全自动模式')
            self.Mouse_Is_Automatic = True
            # 显示相关控件
            # 显示下拉框以及标签
            self.Mouse_Mode_Automatic_Combobox.grid()
            self.Mouse_Mode_Automatic_Mode_Label.grid()
            # 显示直线
            self.Mouse_Mode_Automatic_Line_Start_Label.grid()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid()
            # 显示按钮控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid()
            # 隐藏半自动模式下所有控件
            self.Mouse_Mode_Half_Automatic_Move_Entry.grid_remove()
            self.Mouse_Mode_Half_Automatic_Move_Label.grid_remove()
            self.Mouse_Mode_Half_Automatic_Time_Entry.grid_remove()
            self.Mouse_Mode_Half_Automatic_Time_Label.grid_remove()
            self.Mouse_Mode_Half_Automatic_Confirm_Button.grid_remove()
        elif self.Mouse_Choose_Mode.get() == 2:
            print('半自动模式')
            self.Mouse_Is_Automatic = False
            # 显示半自动模式下所有控件
            # 有条件的显示
            if self.Mouse_Click_Click_Combobox.get() == '单击':
                self.Mouse_Mode_Half_Automatic_Move_Entry.grid()
                self.Mouse_Mode_Half_Automatic_Move_Label.grid()
            elif self.Mouse_Click_Click_Combobox.get() == '长按':
                self.Mouse_Mode_Half_Automatic_Time_Entry.grid()
                self.Mouse_Mode_Half_Automatic_Time_Label.grid()
            self.Mouse_Mode_Half_Automatic_Confirm_Button.grid()
            # 隐藏全自动模式下所有控件
            # 隐藏直线
            self.Mouse_Mode_Automatic_Line_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid_remove()
            # 隐藏矩形
            self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid_remove()
            # 隐藏圆形
            self.Mouse_Mode_Automatic_Circle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid_remove()
            # 隐藏记忆标签
            self.Mouse_Mode_Automatic_Memory_Label.grid_remove()
            # 隐藏控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid_remove()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid_remove()
            # 隐藏下拉框以及标签
            self.Mouse_Mode_Automatic_Combobox.grid_remove()
            self.Mouse_Mode_Automatic_Mode_Label.grid_remove()
            # 初始化相关参数
            self.Mouse_Mode_Half_Automatic_Last_Click_Position = 0
            self.Mouse_Mode_Half_Automatic_Last_Sum_division = 0
            self.Mouse_Mode_Half_Automatic_Start_Time = 0

    # 半自动模式的控制切换
    def Half_Automatic_Mode_Change(self, *arge):
        if self.Mouse_Choose_Mode.get() == 2:
            if self.Mouse_Click_Click_Combobox.get() == '单击':
                # 显示
                self.Mouse_Mode_Half_Automatic_Move_Entry.grid()
                self.Mouse_Mode_Half_Automatic_Move_Label.grid()
                # 隐藏
                self.Mouse_Mode_Half_Automatic_Time_Entry.grid_remove()
                self.Mouse_Mode_Half_Automatic_Time_Label.grid_remove()
            elif self.Mouse_Click_Click_Combobox.get() == '长按':
                # 显示
                self.Mouse_Mode_Half_Automatic_Time_Entry.grid()
                self.Mouse_Mode_Half_Automatic_Time_Label.grid()
                # 隐藏
                self.Mouse_Mode_Half_Automatic_Move_Entry.grid_remove()
                self.Mouse_Mode_Half_Automatic_Move_Label.grid_remove()

    # 自动模式下个方法的控件的显示与隐藏
    def Mouse_Automatic_Mode_Manager(self, *arge):
        if self.Mouse_Mode_Automatic_Mode.get() == '直线模式':
            print('直线模式')
            # 隐藏其他控件，显示直线相关的控件
            # 显示当前控件
            self.Mouse_Mode_Automatic_Line_Start_Label.grid()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid()
            # 显示按钮控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid()
            # 隐藏矩形
            self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid_remove()
            # 隐藏圆形
            self.Mouse_Mode_Automatic_Circle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid_remove()
            # 隐藏记忆标签
            self.Mouse_Mode_Automatic_Memory_Label.grid_remove()
        elif self.Mouse_Mode_Automatic_Mode.get() == '矩形模式':
            print('矩形模式')
            # 隐藏其他控件，显示矩形相关的控件
            self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid()
            self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid()
            # 显示按钮控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid()
            # 隐藏其他控件
            # 隐藏直线
            self.Mouse_Mode_Automatic_Line_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid_remove()
            # 隐藏圆形
            self.Mouse_Mode_Automatic_Circle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid_remove()
            # 隐藏记忆标签
            self.Mouse_Mode_Automatic_Memory_Label.grid_remove()
        elif self.Mouse_Mode_Automatic_Mode.get() == '圆形模式':
            print('圆形模式')
            # 隐藏其他控件，显示矩形相关的控件
            self.Mouse_Mode_Automatic_Circle_Start_Label.grid()
            self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid()
            self.Mouse_Mode_Automatic_Circle_Stop_Label.grid()
            self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid()
            # 显示按钮控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid()
            # 隐藏其他控件
            # 隐藏直线
            self.Mouse_Mode_Automatic_Line_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid_remove()
            # 隐藏矩形
            self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid_remove()
            # 隐藏记忆标签
            self.Mouse_Mode_Automatic_Memory_Label.grid_remove()
        elif self.Mouse_Mode_Automatic_Mode.get() == '记忆模式':
            print('记忆模式')
            # 隐藏其他控件，显示记忆模式相关的控件
            self.Mouse_Mode_Automatic_Memory_Label.grid()
            # 隐藏直线
            self.Mouse_Mode_Automatic_Line_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Line_Stop_Position_Entry.grid_remove()
            # 隐藏矩形
            self.Mouse_Mode_Automatic_Rectangle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position_Entry.grid_remove()
            # 隐藏圆形
            self.Mouse_Mode_Automatic_Circle_Start_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Start_Position_Entry.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Label.grid_remove()
            self.Mouse_Mode_Automatic_Circle_Stop_Position_Entry.grid_remove()
            # 隐藏控件
            self.Mouse_Mode_Automatic_Get_Position_Button.grid_remove()
            self.Mouse_Mode_Automatic_Line_Confirm_Position_Button.grid_remove()

    # 辅助获取鼠标坐标
    def Mouse_Automatic_Mode_Auxiliary_Get_Position(self):
        if self.Mouse_Automatic_Is_Control:
            print("正在进行控制，请勿重新记录位置！")
            return
        if self.Mouse_Mode_Automatic_Mode.get() == '直线模式':
            print('开始获取坐标(直线)')
            th_get_line_position = threading.Thread(target=self.Th_Get_Line_Position)
            th_get_line_position.setDaemon(True)
            th_get_line_position.start()
        elif self.Mouse_Mode_Automatic_Mode.get() == '矩形模式':
            print('开始获取坐标(矩形)')
            th_get_rectangle_position = threading.Thread(target=self.Th_Get_Rectangle_Position)
            th_get_rectangle_position.setDaemon(True)
            th_get_rectangle_position.start()
        elif self.Mouse_Mode_Automatic_Mode.get() == '圆形模式':
            print('开始获取坐标(圆形)')
            th_get_circle_position = threading.Thread(target=self.Th_Get_Circle_Position)
            th_get_circle_position.setDaemon(True)
            th_get_circle_position.start()
        elif self.Mouse_Mode_Automatic_Mode.get() == '记忆模式':
            print('记忆模式')

    # 创建直线获取坐标线程
    def Th_Get_Line_Position(self):
        # 创建鼠标监听事件
        with pynput.mouse.Listener(
                on_move=self.Automatic_Line_On_Move,
                on_click=self.Automatic_Line_On_Click
        ) as listener:
            listener.join()

    # 创建矩形获取坐标线程
    def Th_Get_Rectangle_Position(self):
        # 创建鼠标监听事件
        with pynput.mouse.Listener(
                on_move=self.Automatic_Rectangle_On_Move,
                on_click=self.Automatic_Rectangle_On_Click
        ) as listener:
            listener.join()

    # 创建圆形获取坐标线程
    def Th_Get_Circle_Position(self):
        # 创建鼠标监听事件
        with pynput.mouse.Listener(
                on_move=self.Automatic_Circle_On_Move,
                on_click=self.Automatic_Circle_On_Click
        ) as listener:
            listener.join()

    # 获取直线相关鼠标移动事件函数
    def Automatic_Line_On_Move(self, x, y):
        if self.Mouse_Click_Listener_line == 0:
            self.Mouse_Mode_Automatic_Line_Start_Position.set('(' + str(x) + ', ' + str(y) + ')')
        elif self.Mouse_Click_Listener_line == 1:
            self.Mouse_Mode_Automatic_Line_Stop_Position.set('(' + str(x) + ', ' + str(y) + ')')

    # 相关直线相关鼠标点击事件函数
    def Automatic_Line_On_Click(self, x, y, button, pressed):
        if not pressed:
            self.Mouse_Click_Listener_line = self.Mouse_Click_Listener_line + 1
        if self.Mouse_Click_Listener_line == 2:
            print("直线坐标获取完毕！")
            self.Mouse_Click_Listener_line = 0
            return False

    # 获取矩形相关鼠标移动事件函数
    def Automatic_Rectangle_On_Move(self, x, y):
        if self.Mouse_Click_Listener_Rectangle == 0:
            self.Mouse_Mode_Automatic_Rectangle_Start_Position.set('(' + str(x) + ', ' + str(y) + ')')
        elif self.Mouse_Click_Listener_Rectangle == 1:
            self.Mouse_Mode_Automatic_Rectangle_Stop_Position.set('(' + str(x) + ', ' + str(y) + ')')

    # 相关矩形相关鼠标点击事件函数
    def Automatic_Rectangle_On_Click(self, x, y, button, pressed):
        if not pressed:
            self.Mouse_Click_Listener_Rectangle = self.Mouse_Click_Listener_Rectangle + 1
        if self.Mouse_Click_Listener_Rectangle == 2:
            print("矩形坐标获取完毕！")
            self.Mouse_Click_Listener_Rectangle = 0
            return False

    # 获取圆形相关鼠标移动事件函数
    def Automatic_Circle_On_Move(self, x, y):
        if self.Mouse_Click_Listener_Circle == 0:
            self.Mouse_Mode_Automatic_Circle_Start_Position.set('(' + str(x) + ', ' + str(y) + ')')
        elif self.Mouse_Click_Listener_Circle == 1:
            self.Mouse_Mode_Automatic_Circle_Stop_Position.set('(' + str(x) + ', ' + str(y) + ')')

    # 相关圆形相关鼠标点击事件函数
    def Automatic_Circle_On_Click(self, x, y, button, pressed):
        if not pressed:
            self.Mouse_Click_Listener_Circle = self.Mouse_Click_Listener_Circle + 1
        if self.Mouse_Click_Listener_Circle == 2:
            print("圆形坐标获取完毕！")
            self.Mouse_Click_Listener_Circle = 0
            return False

    # 拖拽检测线程
    def Th_Check_Drag(self):
        # 创建鼠标监听事件
        with pynput.mouse.Listener(
                on_click=self.Is_Drag_on_click
        ) as listener:
            listener.join()

    # 拖拽检测函数
    def Is_Drag_on_click(self, x, y, button, pressed):
        if not pressed:
            self.Mouse_Is_Drag = False

    # 保存坐标数据
    def Mouse_Automatic_Saving_Position(self):
        if self.Mouse_Mode_Automatic_Mode.get() == '直线模式':
            # 清除原来的数据
            self.Mouse_Mode_Automatic_Line_Position = []
            self.Mouse_Mode_Automatic_Line_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Line_Start_Position.get())
            )
            self.Mouse_Mode_Automatic_Line_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Line_Stop_Position.get())
            )
            # 检查是否越界
            sW, sH = pg.size()
            if len(self.Mouse_Mode_Automatic_Line_Position[0]) == 0 or \
                    len(self.Mouse_Mode_Automatic_Line_Position[1]) == 0:
                print("输入数据有误，重新输入")
                return
            if self.Mouse_Mode_Automatic_Line_Position[0][0] > sW or \
                    self.Mouse_Mode_Automatic_Line_Position[0][1] > sH or \
                    self.Mouse_Mode_Automatic_Line_Position[1][0] > sW or \
                    self.Mouse_Mode_Automatic_Line_Position[1][1] > sH:
                self.Mouse_Mode_Automatic_Line_Position = []
                print("输入数据越界，请重新输入")
            if self.Mouse_Mode_Automatic_Line_Position[0][0] == self.Mouse_Mode_Automatic_Line_Position[1][0] and \
                    self.Mouse_Mode_Automatic_Line_Position[0][1] == self.Mouse_Mode_Automatic_Line_Position[1][1]:
                self.Mouse_Mode_Automatic_Line_Position = []
                print("无法构成直线，请重新输入")
            # 更新输入框数据(防止出现负数)
            if len(self.Mouse_Mode_Automatic_Line_Position) > 0:
                self.Mouse_Mode_Automatic_Line_Start_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Line_Position[0][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Line_Position[0][1]) +
                    ')'
                )
                self.Mouse_Mode_Automatic_Line_Stop_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Line_Position[1][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Line_Position[1][1]) +
                    ')'
                )
                self.Position_Line_Is_Change = True  # 说明数据发生了变化
            else:
                self.Mouse_Mode_Automatic_Line_Start_Position.set('')
                self.Mouse_Mode_Automatic_Line_Stop_Position.set('')
        elif self.Mouse_Mode_Automatic_Mode.get() == '矩形模式':
            print('矩形模式')
            # 清除原来的数据
            self.Mouse_Mode_Automatic_Rectangle_Position = []
            self.Mouse_Mode_Automatic_Rectangle_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Rectangle_Start_Position.get())
            )
            self.Mouse_Mode_Automatic_Rectangle_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Rectangle_Stop_Position.get())
            )
            # 检查是否越界
            sW, sH = pg.size()
            if len(self.Mouse_Mode_Automatic_Rectangle_Position[0]) == 0 or len(
                    self.Mouse_Mode_Automatic_Rectangle_Position[1]) == 0:
                print("输入数据有误，重新输入")
                return
            if self.Mouse_Mode_Automatic_Rectangle_Position[0][0] > sW or \
                    self.Mouse_Mode_Automatic_Rectangle_Position[0][1] > sH or \
                    self.Mouse_Mode_Automatic_Rectangle_Position[1][0] > sW or \
                    self.Mouse_Mode_Automatic_Rectangle_Position[1][1] > sH:
                self.Mouse_Mode_Automatic_Rectangle_Position = []
                print("输入数据越界，请重新输入")
            if self.Mouse_Mode_Automatic_Rectangle_Position[0][0] == self.Mouse_Mode_Automatic_Rectangle_Position[1][
                0] or \
                    self.Mouse_Mode_Automatic_Rectangle_Position[0][1] == \
                    self.Mouse_Mode_Automatic_Rectangle_Position[1][1]:
                self.Mouse_Mode_Automatic_Rectangle_Position = []
                print("无法构成矩形，请重新输入")
            # 更新输入框数据(防止出现负数)
            if len(self.Mouse_Mode_Automatic_Rectangle_Position) > 0:
                self.Mouse_Mode_Automatic_Rectangle_Start_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Rectangle_Position[0][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Rectangle_Position[0][1]) +
                    ')'
                )
                self.Mouse_Mode_Automatic_Rectangle_Stop_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Rectangle_Position[1][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Rectangle_Position[1][1]) +
                    ')'
                )
                self.Position_Rectangle_Is_Change = True  # 说明数据发生了变化
            else:
                self.Mouse_Mode_Automatic_Rectangle_Start_Position.set('')
                self.Mouse_Mode_Automatic_Rectangle_Stop_Position.set('')
        elif self.Mouse_Mode_Automatic_Mode.get() == '圆形模式':
            print('圆形模式')
            # 矩形的内接圆比较合适
            self.Mouse_Mode_Automatic_Circle_Position = []
            self.Mouse_Mode_Automatic_Circle_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Circle_Start_Position.get())
            )
            self.Mouse_Mode_Automatic_Circle_Position.append(
                divide_position_data(self.Mouse_Mode_Automatic_Circle_Stop_Position.get())
            )
            # 检查是否越界
            sW, sH = pg.size()
            if len(self.Mouse_Mode_Automatic_Circle_Position[0]) == 0 or len(
                    self.Mouse_Mode_Automatic_Circle_Position[1]) == 0:
                print("输入数据有误，重新输入")
                return
            if self.Mouse_Mode_Automatic_Circle_Position[0][0] > sW or \
                    self.Mouse_Mode_Automatic_Circle_Position[0][1] > sH or \
                    self.Mouse_Mode_Automatic_Circle_Position[1][0] > sW or \
                    self.Mouse_Mode_Automatic_Circle_Position[1][1] > sH:
                self.Mouse_Mode_Automatic_Circle_Position = []
                print("输入数据越界，请重新输入")
            if self.Mouse_Mode_Automatic_Circle_Position[0][0] == self.Mouse_Mode_Automatic_Circle_Position[1][0] and \
                    self.Mouse_Mode_Automatic_Circle_Position[0][1] == self.Mouse_Mode_Automatic_Circle_Position[1][1]:
                self.Mouse_Mode_Automatic_Circle_Position = []
                print("无法构成圆形，请重新输入")

            # 更新输入框数据(防止出现负数)
            if len(self.Mouse_Mode_Automatic_Circle_Position) > 0:
                self.Mouse_Mode_Automatic_Circle_Start_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Circle_Position[0][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Circle_Position[0][1]) +
                    ')'
                )
                self.Mouse_Mode_Automatic_Circle_Stop_Position.set(
                    '(' +
                    str(self.Mouse_Mode_Automatic_Circle_Position[1][0]) +
                    ', ' +
                    str(self.Mouse_Mode_Automatic_Circle_Position[1][1]) +
                    ')'
                )
                self.Position_Circle_Is_Change = True  # 说明数据发生了变化
            else:
                self.Mouse_Mode_Automatic_Circle_Start_Position.set('')
                self.Mouse_Mode_Automatic_Circle_Stop_Position.set('')
        elif self.Mouse_Mode_Automatic_Mode.get() == '记忆模式':
            print('记忆模式')
        print("数据保存成功！")

    """其他功能函数"""
    '''校正设备函数'''

    def Th_Adjust_Device(self):
        th_adjust_device = threading.Thread(target=self.Adjust_Device)
        th_adjust_device.setDaemon(True)
        th_adjust_device.start()

    def Adjust_Device(self):
        if self.COMObj is not None:
            # 停止其他一切监听线程，所有消息都从这处理，直到设备处理完毕
            self.Is_Adjust = True
            self.Write_COMPort_Data("Device_Adjust")
            while True:
                if self.Th_Inform:
                    break
                time.sleep(0.01)  # 给1秒钟，让其他线程停止运行
            start_adjust = False
            n = 0
            while True:
                if n > 1000:
                    break
                read_data = self.COM_Queue.get().replace('\r', '').replace('\n', '')
                if read_data == '+':  # 说明开始设备校准
                    print("校准开始！")
                    start_adjust = True
                    n = 0
                if read_data == '-':
                    print("校准结束！")
                    start_adjust = False
                    break
                if start_adjust:
                    # 打印设备的提示消息
                    print(read_data)
                    n = 0
                n = n + 1
                time.sleep(0.001)
            self.Is_Adjust = False
            self.Th_Inform = False

    '''保存相关设置函数'''

    # 保存相关设置按钮函数
    def Saving_Data(self):
        # 保存变量到全局变量
        self.KeyBoard_Combine_Key_Start_Remember = self.Setting_KeyBoard_Remember_Start.get()
        self.KeyBoard_Combine_Key_Stop_Remember = self.Setting_KeyBoard_Remember_Stop.get()
        self.KeyBoard_Combine_Key_Start_Control = self.Setting_KeyBoard_Start_Control.get()
        self.KeyBoard_Combine_Key_Stop_Control = self.Setting_KeyBoard_Stop_Control.get()
        # 保存数据到文件
        self.Saving_Data_File()

    # 初始化热键函数
    def Initial_KeyBoard(self):
        self.Read_Data_File()

    # 读取文件内容
    def Read_Data_File(self):
        file_path = './data.dat'
        file = None
        try:
            file = open(file_path, 'r')
        except:
            print("创建初始化文件")
            self.Saving_Data_File()
        try:
            # 读取数据
            data = file.readline()
            self.KeyBoard_Combine_Key_Start_Remember = data.strip()
            self.Setting_KeyBoard_Remember_Start.set(self.KeyBoard_Combine_Key_Start_Remember)
            data = file.readline()
            self.KeyBoard_Combine_Key_Stop_Remember = data.strip()
            self.Setting_KeyBoard_Remember_Stop.set(self.KeyBoard_Combine_Key_Stop_Remember)
            data = file.readline()
            self.KeyBoard_Combine_Key_Start_Control = data.strip()
            self.Setting_KeyBoard_Start_Control.set(self.KeyBoard_Combine_Key_Start_Control)
            data = file.readline()
            self.KeyBoard_Combine_Key_Stop_Control = data.strip()
            self.Setting_KeyBoard_Stop_Control.set(self.KeyBoard_Combine_Key_Stop_Control)
            file.close()
        except:
            print("读取默认文件内容")
            self.Setting_KeyBoard_Remember_Start.set(self.KeyBoard_Combine_Key_Start_Remember)
            self.Setting_KeyBoard_Remember_Stop.set(self.KeyBoard_Combine_Key_Stop_Remember)
            self.Setting_KeyBoard_Start_Control.set(self.KeyBoard_Combine_Key_Start_Control)
            self.Setting_KeyBoard_Stop_Control.set(self.KeyBoard_Combine_Key_Stop_Control)
            # 写入文件
            self.Saving_Data_File()

    # 保存到文件
    def Saving_Data_File(self):
        try:
            # 打开文件
            file_path = './data.dat'
            file = open(file_path, 'w')
            # 写入文件
            data = self.KeyBoard_Combine_Key_Start_Remember + '\n'
            file.writelines(data)
            data = self.KeyBoard_Combine_Key_Stop_Remember + '\n'
            file.writelines(data)
            data = self.KeyBoard_Combine_Key_Start_Control + '\n'
            file.writelines(data)
            data = self.KeyBoard_Combine_Key_Stop_Control + '\n'
            file.writelines(data)
            # 关闭文件
            file.close()
            print("文件写入成功！")
        except:
            print("文件写入失败！请检查程序权限！")


if __name__ == "__main__":
    root = Tk()
    UI(root)
    root.mainloop()
