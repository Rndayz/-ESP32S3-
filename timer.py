from machine import I2C,Pin
from ssd1306 import SSD1306_I2C
import machine
import time
i2c = I2C(scl = Pin(48),sda = Pin(47),freq = 10000) #软件I2C
oled = SSD1306_I2C(128, 32, i2c) #创建oled对象
data = 100

# Function to convert seconds to minutes and seconds
def convert_seconds_to_minutes(seconds):
    minutes, seconds = divmod(seconds, 60)
    return minutes, seconds

# Get initial time in minutes from the user
initial_minutes = int(data)
remaining_seconds = initial_minutes * 60

# Main loop
while remaining_seconds > 0:
    # Convert remaining seconds to minutes and seconds
    remaining_minutes, remaining_seconds = convert_seconds_to_minutes(remaining_seconds)
    oled.text("time: {}".format(remaining_minutes, remaining_seconds), 0, 20)
    oled.show()

    # Display the remaining time
    print("Time remaining: {} minutes {} seconds".format(remaining_minutes, remaining_seconds))

    # Wait for 60 seconds (1 minute)
    time.sleep(60)


