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
    def __init__(self, ble, rx_callback=None, name="mpy-uart", rxbuf=100):
        self.__ble = ble
        self.__rx_cb = rx_callback
        self.initial_minutes = 0
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
                     initial_minutes = int(received_data)

    def send(self, data):
        data_bytes = struct.pack('I', data)
        self.__write(self.__tx_handle, data_bytes)

        if self.__conn_handle is not None:
            self.__notify(self.__conn_handle, self.__tx_handle, data_bytes)

    def timmme(self):
        # 主循环
        while self.initial_minutes > 0:
            # 清除屏幕内容
            oled.fill(0)

            # 显示剩余时间
            
            oled.text("minutes{} ".format(self.initial_minutes), 0, 20)
            oled.show()

            # 等待 60 秒（1 分钟）
            time.sleep(60)
            self.initial_minutes -= 1
    def rx_callback(data):
        global uart_instance  # 使用 global 关键字声明全局变量
        uart_instance.initial_minutes = data  # 将接收到的数字赋值给实例变量

