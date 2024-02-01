from machine import I2C,Pin
from ssd1306 import SSD1306_I2C
i2c = I2C(scl = Pin(48),sda = Pin(47),freq = 10000) #软件I2C
oled = SSD1306_I2C(128, 32, i2c) #创建oled对象

oled.text("Hello",0,0)
oled.text("World!",0,20)
oled.show()

# import ssd1306py as lcd
# 
# 
# lcd.init_i2c(48, 47, 128, 64)
# lcd.text('font32x32', 0, 0, 32)
# lcd.show()