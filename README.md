
#### 介绍
基于ESP32S3的可穿戴骑行辅助设备代码仓库

#### 硬件准备
1.一块esp32s3（N16R8）

2.0.91寸oled（128x64）

3.ublox gps模块

#### 软件准备
1.thonny
2.esp32使用的固件下载器（最好使用商家给的配套固件，如果没有的话就去microPython官网下载一个）

#### 接线方式
SCL＝48

SDA＝47

tx ＝11

rx＝12

请注意，这里定义的TX RX是microPython设备的TX RX，可以自行修改，oled屏幕的SCL SDA同理<br>
对应的GPS模块应该反着插，既定位模块的RX对应板载定义的TX，模块的TX对应板载RX
#### 使用教程
1.给你的ESP32S3 MicroPython设备刷入microPython固件（需要有蓝牙）

2.将仓库中的除gitignore文件和证书以外的文件下载至你的ESP32S3 MicroPython设备<br>所需的库已经打包在lib文件夹中了


