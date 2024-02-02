import os
from machine import UART
from machine import Timer
from machine import I2C,Pin
import ssd1306 as oled
import time
import select
import bluetooth
#——————gps————————

# SGPGSV语句的基本格式如下:
# $GPGSV,(1),(2),(3),(4),(5),(6),(7)..(4),(5),(6),()#hh(CR(LF)
# (1)GSV语句总数。
# (2)本句GSV的编号。
# (3)可见卫星的总数(00-12,前面的0也将被传输)
# (4)卫星编号(01-32，前面的0也将被传输)。
# (5)卫星仰角(00-90度，前面的0也将被传输)
# （6）卫星方位角(000-359度，前面的0也将被传输)

# SGPRMC,(1),.(2),(3).(4),(5),(6),(7),8),(9),(10),(11),(12)#hb(CR)(LF)
# (1）UTC时间，hhmmss (时分秒)
# （2）定位状态，A=有效定位，V=无效定位
# (3)纬度dmm.mmmmm (度分)
# （4)纬度半球N(北半球)或S(南半球)
# (5) 经度dldmm.mmmmm(度分)
# (6)经度半球E(东经)或W(西经)
# (7)地面速率(000.0-999.9节)
# (8)地面航向(0000-359.9度，以真北方为参考基准)
# (9)UTC日期，ddmmyy(日月年）
# (10)磁偏角(000.0-180.0度，前导位数不足则补0)
# (11)磁偏角方向，E(东)或W(西)
# (12)模式指示(A=自主定位，D=差分，E=估算，N=数据无效)

# $GPVTG (地面速度信息，Track Made Good and Ground Speed)
# SGPVTG语句的基本格式如下:
# $GPVTG,(1D),T2),M,(3),N,(4).K,(5)"hh(CR)(LF)
# (1)以真北为参考基准的地面航向(000-359度，前面的0也将被传输)
# (2)以磁北为参考基准的地面航向(000-359度，前面的0也将被传输)
# (3)地面速率(000.0-999.9节，前面的0也将被传输)
# (4)地面速率0000.0-1851.8公里/小时，前面的0也将被传输#
# (5)模式指示(A=自主定位，D=差分，E=估算，N=数据无效)


uart = UART(1,9600,rx=11, tx=12)
#格式：UART(1, baudrate=115201, bits=8, parity=None, stop=1, tx=10, rx=9, rts=-1, cts=-1, txbuf=256, rxbuf=256, timeout=0, timeout_char=0)
#定义GPS模块收发IO口
normal_data_GPGSV = ''
normal_data_GPVTG = ''
normal_data_GPRMC = ''
received_data = ''
#统一定义变量，防止因为没有轮询到相应回复导致变量未定义
while True:
    if uart.any():
       received_data = uart.readline().decode('utf-8').strip()#阅读一行，除去换行符，转为普通字符串
       print(received_data)
       if "GPGSV" in received_data:
          normal_data_GPGSV = received_data
          print("可见卫星信息:", normal_data_GPGSV)
       elif "GPVTG" in received_data:
          normal_data_GPVTG = received_data
          print("地面速度信息:", normal_data_GPVTG)
       elif "GPRMC" in received_data:
          normal_data_GPRMC = received_data
          print("推荐定位信息:", normal_data_GPRMC)
       time.sleep(0.5)   
       # 开始分割
       split_data_GPGSV = normal_data_GPGSV.split(',')
       split_data_GPVTG = normal_data_GPVTG.split(',')
       split_data_GPRMC = normal_data_GPRMC.split(',')
       print(split_data_GPGSV,
             split_data_GPVTG,
             split_data_GPRMC)
       if len(split_data_GPGSV) >= 2:
          visiblesat = split_data_GPGSV[3]
          print("可见卫星数:", visiblesat)
       if len(split_data_GPVTG) >= 2:
          speed = split_data_GPVTG[7]
          print("当前时速", speed ,'km/s')
       if len(split_data_GPRMC) >= 2:
          utctime = split_data_GPRMC[1]
          status = split_data_GPRMC[2]
          print("当前UTC时间:", utctime)
          print("定位状态:", status)     
       time.sleep(1)
    else : print('unknown:',received_data)
    
#——————oled——————
# from machine import I2C,Pin
# import ssd1306 as oled    
i2c = I2C(scl = Pin(48),sda = Pin(47),freq = 10000) #软件I2C
oled = oled.SSD1306_I2C(128, 32, i2c) #创建oled对象
oled.text("hello!",0,0)
oled.show()


#定义oled的io口
#OLED_WR_Byte(0xA1,OLED_CMD);//--Set SEG/Column Mapping     0xa0左右反置 0xa1正常
#OLED_WR_Byte(0xC8,OLED_CMD);//Set COM/Row Scan Direction   0xc0上下反置 0xc8正常
#可能用于上下翻转显示
# 
# 
# display.poweroff（）#关闭显示器电源，像素保留在内存中
# display.poweon（）#打开显示器电源，重新绘制像素
# display.contation（0）#dim
# display.contation（255）#明亮
# display.inverse（1）#显示反转
# display.inverse（0）#显示正常
# display.rotate（True）#旋转180度
# display.rate（False）#旋转0度
# display.show（）#将FrameBuffer的内容写入显示内存
# 子类化 帧缓冲区提供对图形基元的支持：
# # 
# display.fill（0）#用颜色填充整个屏幕=0
# display.pixel（0,10）#在x=0，y=10处获取像素
# display.pixel（0，10，1）#将x=0，y=10处的像素设置为color=1
# display.hline（0，8，4，1）#绘制水平线x=0，y=8，宽度=4，颜色=1
# display.vline（0，8，4，1）#绘制垂直线x=0，y=8，高度=4，颜色=1
# display.line（0，0，127，63，1）#画一条从0,0到127,63的线
# display.rect（10，10，107，43，1）#绘制矩形轮廓10，10到107，43
# display.fill_rect（10，10，107，43，1）#绘制一个实心矩形10,10到107,43，color=1
# display.text（“Hello World”，0，0，1）#在x=0，y=0，colour=1处绘制一些文本
# display.scroll（20，0）#向右滚动20个像素#
# #在给定坐标的当前帧缓冲区的顶部绘制另一个帧缓冲区
# # import framebuf
# fbuf = framebuf.FrameBuffer(bytearray(8 * 8 * 1), 8, 8, framebuf.MONO_VLSB)
# fbuf.line(0, 0, 7, 7, 1)
# display.blit(fbuf, 10, 10, 0)           # draw on top at x=10, y=10, key=0
# display.show()

#——bluetooth——
bt = bluetooth.BLE()
bt.active(True)
bt.gap_advertise(100, adv_data='ESP32_BLE_01',connectable=True)
#BLE.gap_advertise(interval_us, adv_data=None, *, resp_data=None, connectable=True)
bt.gap_advertise(None,)
#停止广播
HR_UUID = bluetooth.UUID(0x180D)
HR_CHAR = (bluetooth.UUID(0x2A37), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
HR_SERVICE = (HR_UUID, (HR_CHAR,),)
UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
UART_TX = (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
UART_RX = (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_WRITE,)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX,),)
SERVICES = (HR_SERVICE, UART_SERVICE,)
( (hr,), (tx, rx,), ) = bt.gatts_register_services(SERVICES)
#注册服务
