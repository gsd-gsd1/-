#include <Arduino.h>
#include <Preferences.h>

#define Master 1    //主从机模式选择 1主机 0从机
#define ADC_Pin 35

#define RO_MODE true
#define RW_MODE false

char ReadBuff[1024];
int isconnect = 0;
int isadjust = 0;
int isinitial = 0;
int start_adjust = 0;

int Write_Buff[30];
float Read_ADC_Data[50];
int device_num = 0;
int last_data = 0;

// ADC相关
float potValue = 0;
float v = 3300;   // 单位为毫伏
//文件存储相关
Preferences MyPrefs;

int error_num = 0;
int running_turns = 0;


void setup() {
  Serial.begin(115200);
  delay(1000);  //等待电路准备完毕
  MyPrefs.begin("myPrefs", RW_MODE); 

  //读取存储内容
  if(get_memory_data())
  {
    Serial.println("数据读取成功！");
    //检查数据长度
    int i = 0;
    for(i=0;i<30;i++)
    {
      if(Read_ADC_Data[i] == 0)break;
    }
    if(i == 0)    //说明没有数据
    {
      isinitial = 1;
      Serial.println("未找到数据，需要进行初始化！");
    }
    device_num = i - 1;   //减去原设备
  }
  else
  {
    isinitial = 1;
    Serial.println("未找到数据，需要进行初始化！");
  }
  //创建数据发送线程
  xTaskCreate(
    th_recall,   /* Task function. */
    "getconnnect", /* String with name of task. */
    10000,     /* Stack size in bytes. */
    NULL,      /* Parameter passed as input of the task */
    1,         /* Priority of the task. */
    NULL);     /* Task handle. */
}

void loop()
{
  //主设备发送设备请求
  if(isconnect == 0 && isadjust == 0 && isinitial == 0 && 0)
  {
    send_simulation_data_up();
    send_simulation_data_down();
  }
  if(isinitial == 1 && start_adjust == 0)
  {
    Serial.println("*");
    delay(50);
    isinitial = 0;
    running_turns = 0;
    error_num = 0;
  }
  // 设备数据采集并发送
  if(isconnect == 0 && isadjust == 0 && isinitial == 0)
  {
    //采集设备数据
    float device_data = get_adc_and_tran();
    //将数据从设备数据表中进行比较
    for(int i=0;i<30;i++)
    {
      if(isconnect == 1 || isadjust == 1 || isinitial == 1)
      {
        break;
      }
      if(abs(Read_ADC_Data[i] - device_data)<10 && Read_ADC_Data[i] != 0)
      {
        //当前i即为对应的等级，并且与上次的不相等，不处理后续的内容
        if(last_data != i)
        {
          Serial.println(i);
          delay(20);
          last_data = i;
        }
        break;
      }
      if(i > device_num)    //说明数据存在问题，请重新进行校验
      {
        error_num = error_num + 1;
        break;
      }
    }
    //读数误差处理
    if(error_num != 0)
    {
      running_turns = running_turns + 1;
    }
    if(running_turns > 100 && error_num < 10)
    {
      error_num = 0;
      running_turns = 0;
    }
    if(error_num > 10)
    {
      isinitial = 1;
    }
  }
  delay(10);
}

void th_recall(void *Parameter)
{
  while(1)
  {
    if(Serial.available())
    { 
      float write_data[30] = {0};
      char ch = '\0';
      int i = 0;
      while(Serial.available())
      {
        ch = char(Serial.read());
        ReadBuff[i] = ch;
        i++;
      }
      if(strcmp(ReadBuff, "Device_InFo") == 0)
      {
        int num = 0;
        isconnect = 1;
        commute_with_superior(device_num);
        //向设备发送存储数据
        show_device_data();
        isconnect = 0;
      }
      else if (strcmp(ReadBuff, "Device_Adjust") == 0) {
        isadjust = 1;
        start_adjust = 1;
        float data = 0;
        float data_last = 0;
        Serial.println("开始进行校准！");
        //进行相关初始化
        clean_buff_Memory();    //清空数组
        // 开始进行调整
        delay(200);
        Serial.println("+");
        delay(100);
        Serial.println("校准开始！");
        delay(100);
        Serial.println("请将不要按下设备! 共保持5秒!");
        delay(2000);
        Serial.println("开始采集无按压时的数据! 请保持该状态");
        data = get_adc_and_tran();

        write_data[0] = data;
        //将数据写入存储
        delay(3000);
        int j = 0;
        for(int i = 1;i<30;i++)
        {
          char str[200] = {'\0'};

          sprintf(str, "请按下第%d个设备(包括前面的)! 共保持5秒!", i);
          Serial.println(str);
          delay(2000);

          Serial.println("开始采集数据! 请保持该状态");
          delay(1000);
          data = get_adc_and_tran();
          delay(2000);
          for(j = 0;j<i;j++)
          {
            if(abs(data - write_data[j]) < 10)  //说明与之前的情况一样不发生变化，即说明检测停止
            {
              break;
            }
          }
          if(j < i)   //说明找到了
          {
            Serial.println("存在两次采集无变化，退出校准模式！");
            device_num = i - 1;
            delay(50);
            sprintf(str, "采集设备总数为: %d", device_num);
            Serial.println(str);
            delay(50);
            break;
          }
          write_data[i] = data;
        }
        Serial.println('-');
        delay(200);
        // 将数组写入存储
        MyPrefs.putBytes( "ADC_Data", write_data, sizeof(write_data) );
        //更新数组
        get_memory_data();
        isinitial = 0;
        isadjust = 0;
        start_adjust = 0;
      }
      // 清空数组
      clean_buff();
      delay(200);
    }
    delay(10);
  }
  
}
void commute_with_superior(int n)
{
  //与设备交换信息
  delay(100);
  Serial.println("#");
  delay(50);
  Serial.println(n);
  delay(50);
  Serial.println("#");
}
void send_simulation_data_up()
{
  for(int i = 0;i<9;i++)
  {
    if(isconnect == 1 || isadjust == 1)break;
    Serial.println(i);
    delay(10);
  }
}
void send_simulation_data_down()
{
  for(int i = 9;i>0;i--)
  {
    if(isconnect == 1 || isadjust == 1)break;
    Serial.println(i);
    delay(5);
  }
}

void clean_buff()
{
  for(int i = 0;i<1024;i++)
  {
    ReadBuff[i] = '\0';
  }
}
//清空读数据缓存，以及存储数据
void clean_buff_Memory()
{
  for(int i = 0;i<50;i++)
  {
    Read_ADC_Data[i] = 0;
  }
  MyPrefs.clear();
}
//获取平均采集电压
float get_adc_and_tran()
{
  float V_Value = 0;
  float V_Value_temp = 0;
  for(int i = 0;i<10;i++)    //连续5次采样，求平均
  {
    V_Value_temp += analogRead(ADC_Pin) * (v / 4096.0);
  }
  V_Value = V_Value_temp / 10;
  //除去异常点
  return V_Value;
}
//显示设备数据
void show_device_data()
{
  char str[200] = {'\0'};
  delay(200);
  Serial.println("P");
  delay(100);
  for(int i=0;i<30;i++)
  {
    if(Read_ADC_Data[i] == 0)break;
    sprintf(str, "第%d个位置存储的数据为: %f", i, Read_ADC_Data[i]);
    Serial.println(str);
    delay(50);
  }
  Serial.println("P");
  delay(100);
}
// 将存储数据取出
int get_memory_data()
{
  if(MyPrefs.getBytes("ADC_Data", Read_ADC_Data, MyPrefs.getBytesLength("ADC_Data")))
  {
    return 1;
  }
  return 0;
}
