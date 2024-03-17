import time
import utime
import struct
from machine import UART, I2C, Pin
from ssd1306 import SSD1306_I2C
import ubluetooth as bt
from machine import WDT

wdt = WDT(timeout=10000)#定义一个看门狗

# 定义 UART 和 OLED
uart = UART(1, 9600, rx=11, tx=12)
i2c = I2C(scl=Pin(48), sda=Pin(47), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)

# 定义GPS data，防止轮询因为没有查到数据报错
visiblesat = ''
speed = ''
status = ''

initial_minutes = 0

# BLE UUIDs
__UART_UUID = bt.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
__RX_UUID = bt.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
__TX_UUID = bt.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
__UART_SERVICE = (
    __UART_UUID,
    (
        (__TX_UUID, bt.FLAG_NOTIFY,),
        (__RX_UUID, bt.FLAG_WRITE,),
    ),
)

# BLE UART class
class BLEConst(object):
    class IRQ(object):
        IRQ_CENTRAL_CONNECT = const(1)
        IRQ_CENTRAL_DISCONNECT = const(2)
        IRQ_GATTS_WRITE = const(3)

class BLEAppearance:
    Unknown = 0
    GENERIC_PHONE = 64
    GENERIC_COMPUTER = 128

class BLEADType:
    AD_TYPE_FLAGS = 0x01
    AD_TYPE_16BIT_SERVICE_UUID_COMPLETE = 0x03
    AD_TYPE_32BIT_SERVICE_UUID_COMPLETE = 0x05
    AD_TYPE_128BIT_SERVICE_UUID_COMPLETE = 0x07
    AD_TYPE_COMPLETE_LOCAL_NAME = 0x09
    AD_TYPE_APPEARANCE = 0x19

class BLETools:
    @staticmethod
    def advertising_generic_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
        payload = bytearray()

        def _append(adv_type, value):
            nonlocal payload
            payload += struct.pack('BB', len(value) + 1, adv_type) + value

        _append(BLEADType.AD_TYPE_FLAGS, struct.pack('B', (0x01 if limited_disc else 0x02) + (0x00 if br_edr else 0x04)))

        if name:
            _append(BLEADType.AD_TYPE_COMPLETE_LOCAL_NAME, name)

        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(BLEADType.AD_TYPE_16BIT_SERVICE_UUID_COMPLETE, b)
                elif len(b) == 4:
                    _append(BLEADType.AD_TYPE_32BIT_SERVICE_UUID_COMPLETE, b)
                elif len(b) == 16:
                    _append(BLEADType.AD_TYPE_128BIT_SERVICE_UUID_COMPLETE, b)

        _append(BLEADType.AD_TYPE_APPEARANCE, struct.pack('<h', appearance))

        return payload

    @staticmethod
    def advertising_resp_payload(name=None, services=None):
        payload = bytearray()

        def _append(adv_type, value):
            nonlocal payload
            payload += struct.pack('BB', len(value) + 1, adv_type) + value

        if name:
            _append(BLEADType.AD_TYPE_COMPLETE_LOCAL_NAME, name)

        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(BLEADType.AD_TYPE_16BIT_SERVICE_UUID_COMPLETE, b)
                elif len(b) == 4:
                    _append(BLEADType.AD_TYPE_32BIT_SERVICE_UUID_COMPLETE, b)
                elif len(b) == 16:
                    _append(BLEADType.AD_TYPE_128BIT_SERVICE_UUID_COMPLETE, b)

        return payload

    @staticmethod
    def decode_mac(addr):
        if isinstance(addr, memoryview):
            addr = bytes(addr)

        assert isinstance(addr, bytes) and len(addr) == 6, ValueError("mac address value error")
        return ":".join(['%02X' % byte for byte in addr])

class BLEUART:
    def __init__(self, ble, rx_callback=None, name="Riding", rxbuf=100):
        self.__ble = ble
        self.__rx_cb = rx_callback
        self.__conn_handle = None
        self.__write = self.__ble.gatts_write
        self.__read = self.__ble.gatts_read
        self.__notify = self.__ble.gatts_notify
        self.__ble.active(False)
        print("activating ble...")
        self.__ble.active(True)
        print("ble activated")
        self.__ble.config(rxbuf=rxbuf)
        self.__ble.irq(self.__irq)
        self.__register_services()
        self.__adv_payload = BLETools.advertising_generic_payload(
            services=(__UART_UUID,),
            appearance=BLEAppearance.GENERIC_COMPUTER,
        )
        self.__resp_payload = BLETools.advertising_resp_payload(
            name=name
        )
        self.__advertise()

    def __register_services(self):
        (
            (
                self.__tx_handle,
                self.__rx_handle,
            ),
        ) = self.__ble.gatts_register_services((__UART_SERVICE,))

    def __advertise(self, interval_us=500000):
        self.__ble.gap_advertise(None)
        self.__ble.gap_advertise(interval_us, adv_data=self.__adv_payload, resp_data=self.__resp_payload)
        print("advertising...")

    def __irq(self, event, data):
        global initial_minutes
        if event == BLEConst.IRQ.IRQ_CENTRAL_CONNECT:
            self.__conn_handle, addr_type, addr, = data
            print("[{}] connected, handle: {}".format(BLETools.decode_mac(addr), self.__conn_handle))
            self.__ble.gap_advertise(None)
        elif event == BLEConst.IRQ.IRQ_CENTRAL_DISCONNECT:
            self.__conn_handle, _, addr, = data
            print("[{}] disconnected, handle: {}".format(BLETools.decode_mac(addr), self.__conn_handle))
            self.__conn_handle = None
            self.__advertise()
        elif event == BLEConst.IRQ.IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle == self.__conn_handle and value_handle == self.__rx_handle:
                if self.__rx_cb:
                     received_data = self.__read(self.__rx_handle).decode('utf-8')  # 解码为utf-8格式
                     self.__rx_cb(received_data)
                     print("Received data:", received_data)
                     initial_minutes = int(received_data)*60*1000 + utime.ticks_ms()

    def send(self, data):
        data_bytes = struct.pack('I', data)
        self.__write(self.__tx_handle, data_bytes)

        if self.__conn_handle is not None:
            self.__notify(self.__conn_handle, self.__tx_handle, data_bytes)

    def timmme(self):
        global initial_minutes
        # 主循环
        while initial_minutes > 0:
            # 清除屏幕内容
            oled.fill(0)
            oled.text("Satellites: {}".format(visiblesat), 0, 0)
            oled.text("Speed: {} km/s".format(speed), 0, 10)
            oled.text("Status: {}".format(status), 0, 20)
            oled.text("{}mins ".format(round((initial_minutes - utime.ticks_ms())/1000/60),2), 0, 30)
            oled.show()
            if uart.any():
               received_data = uart.readline().decode('utf-8').strip()
               print(received_data)
               parse_gps_data(received_data)
            time.sleep(1)  # 调整休眠时间，根据需要进行修改

def rx_callback(data):
    global uart_instance  # 使用 global 关键字声明全局变量
    global initial_minutes
    uart_instance.initial_minutes = data  # 将接收到的数字赋值给实例变量

# BLE 实例初始化
ble = bt.BLE()
uart_instance = BLEUART(ble, rx_callback)

# OLED 显示
def update_oled():
    global initial_minutes
    oled.fill(0)
    oled.text("Sats: {}".format(visiblesat), 0, 0)
    oled.text("Speed: {} km/s".format(speed), 0, 10)
    oled.text("Status: {}".format(status), 0, 20)
    oled.text("{}mins ".format(round((initial_minutes - utime.ticks_ms())/1000/60),2), 0, 30)
    oled.show()
 

# GPS 数据处理
def parse_gps_data(received_data):
    global visiblesat, speed, status
    if "GPGSV" in received_data:
        visiblesat = received_data.split(',')[3]
    elif "GPVTG" in received_data:
        speed = received_data.split(',')[7]
    elif "GPRMC" in received_data:
        data = received_data.split(',')
        status = data[2]
        utctime = data[1]
        print("UTC Time:", utctime)
    update_oled()

# 主循环
while True:
    try:
        if uart.any():
            received_data = uart.readline().decode('utf-8').strip()
            print(received_data)
            parse_gps_data(received_data)
        
        wdt.feed() # 喂狗
        uart_instance.timmme()
        utime.sleep_ms(500)  # 等待500毫秒
    except UnicodeError:
        print("UnicodeError")#忽略Unicode错误

       
   

