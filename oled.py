from machine import I2C,Pin
from ssd1306 import SSD1306_I2C
i2c = I2C(scl = Pin(48),sda = Pin(47),freq = 10000) #软件I2C
oled = SSD1306_I2C(128, 32, i2c) #创建oled对象
visiblesat = ''
speed = ''
status = ''
oled.text("sts: {}".format(visiblesat), 0, 0)
oled.text("spd: {}".format(speed), 0, 10)
oled.text("stu: {}".format(status), 0, 20)
oled.show()
oled.show()
print("可见卫星数:", visiblesat)
print("当前时速", speed ,'km/s')
print("定位状态:", status)     
