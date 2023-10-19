# 外部设备控制鼠标键盘小程序
## 应用简介
### 原理
   通过检测物体的横截面变化，将截面变化通过微动开关转化为电信号的方式来实现检测，并通过串口进行数据交换，利用python实现将外部截面变化转换为电脑鼠标变化，实现鼠标的点击和移动。
### 设备构成
1. ESP32开发板（个人感觉性价比较高），进行模拟信号的采集和模数转换
2. 微动开关（就鼠标中键的那种开关），可以检测较小的力，并将其转换为开关信号
3. 电阻与导线若干
4. 数据线（也可以不用，因为ESP32上搭载着蓝牙和WiFi模块）
5. 相关固定结构（这个本人不是很擅长，就还没咋设计）
### 注意事项
警告：由于本软件在运行时会强行控制鼠标，尽管我已经尽可能的进行了测试与调整，但仍不排除出现BUG的可能，在使用该程序前请尽可能关闭其他有着重要工作的软件，以免造成损失，并且如果出现bug的情况，电脑强制关机或者断电不免是一个更好的选择。
### 使用说明
   本软件使用时必须搭配相关的硬件，并且串口得选对，不然无法正常工作
   软件界面如下图所示：
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/b1f57cc4-3f27-40aa-8592-da48cf41108e)
   
#### 各按键功能说明
   ##### 1. "串口相关"说明：
   串口：指设备连接到电脑端之后，系统会在注册表中创建一个设备文件，我们与设备的通信全是基于这个文件来进行的，一般使用默认的设置就行，无需修改数值
      
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/0e3c13d8-d92c-428a-ad8d-b1e601224c06) 
   ##### 2. "键盘相关"说明：
      
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/5f01cbbb-3d1a-4418-9979-c4bf9594a68e)
      
   只有当勾选开启键盘监听时，才会被允许进行相关的热键操作，否则将无法控制鼠标和键盘
      
   ##### 3. "鼠标相关"说明：
      
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/bc0d1d8f-a3d8-4674-bd23-fced9037715c)
   
   只有当允许控制鼠标选择框被勾选时，才被允许进行鼠标的控制，否则将无法进行鼠标的控制
      
   ##### 4. "选择鼠标控制键"下拉框说明：

   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/60da18b4-f188-411a-b13f-4a7deb4b4e6c)

   该选框选择的是鼠标的控制按钮，比如选择左键，那么整个软件控制的对象就是鼠标左键，右键就是鼠标右键，中键就是鼠标中键

   ##### 5. "选择鼠标点击模式"下拉框说明：

   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/bac4af9f-efef-4164-8ef0-721728257808)

   该选择框控制的是鼠标在被控制移动时是保持鼠标长按还是鼠标在移动时不断点击

   ##### 6. "全自动控制模式"与半自动控制模式说明：

   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/d9479bab-cb2a-4049-b636-0d1098bee6ae)

   该选项控制了两种模式：分别是全自动控制模式与半自动控制模式
   
   ###### 6.1 全自动控制模式：

   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/7a9e3541-c30f-4b73-9e47-097e32c0e125)
   
   全自动控制模式有以下模式：
   
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/489e5ac5-cc2a-43a5-90e6-951e9b5165e5)

   辅助获取坐标按钮：是将坐标点的选择可视化（在想要移动的起始位置处单击左键，就会记录那个位置的坐标并作为开始移动的开始位置，在想要终止的位置处单击左键，就能记录移动结束的终止坐标）（注：可以切换进程进行位置选择呦）
   
   直线模式：即控制鼠标在选定的两个坐标之间，根据外部设备的信号进行循环

   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/c53c202b-bc42-4e95-827f-8eab52d7b5af)
   
   矩形模式：即鼠标移动的轨迹是一个矩形，并根据外部设备的信号进行循环
   
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/1e1ddbc6-2908-488b-abbf-88631a54ffca)

   圆形模式：即鼠标移动的轨迹是一个圆形，并根据外部设备的信号进行循环
   
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/00b82818-6a0a-406e-9e46-d2d96cf4edac)

   记忆模式：可以根据自己之前设置的快捷键进行鼠标移动轨迹的记录，当按下相关快捷键时开始控制时，根据外部设备的信号进行循环（控制终端会有相关提示，按提示操作即可）
   
   ![image](https://github.com/gsd-gsd1/Peripheral-Analog-Mouse-and-Keyboard/assets/140622400/ec06b998-75ae-4b2e-a392-c34339e5385e)

   ###### 6.2 半自动控制模式

   


## 硬件连接与接线
## 未来的更新计划
找到了一种更好的传感器材料，可以把拉伸转换为电阻变化并且该材料本身具有弹性，非常适合用来该项目，但相关代码还未编写，相关材料还未进行具体的测试实验，但未来的方向就是那样，用一块可粘贴的切具有弹性的柔性传感器薄膜进行检测，可以说是相当方便
#
