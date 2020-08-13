from lib.core import *

if WINDOWS_OS:
    import winreg
import serial
from time import sleep


class UfosConnection:
    def __init__(self, to=1):
        self.opened_serial = None
        self.br = 115200  # Baudrate
        self.bs = 8  # Byte size
        self.par = 'N'  # Parity
        self.sb = 1  # Stop bits
        self.to = to  # Time out (s)

    def get_com(self):
        if WINDOWS_OS:
            try:
                registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                              "HARDWARE\\DEVICEMAP\\SERIALCOMM")
                for i in range(255):
                    name, value, typ = winreg.EnumValue(registry_key, i)
                    if 'Silab' in name:
                        self.opened_serial = serial.Serial(port='//./' + value,
                                                           baudrate=self.br,
                                                           bytesize=self.bs,
                                                           parity=self.par,
                                                           stopbits=self.sb,
                                                           timeout=self.to)
                        self.opened_serial.close()
                        return self.opened_serial
            except WindowsError:
                text = "Кабель не подключен к ПК!                   "
                print(text, end='\r')
                LOGGER.error(text)
        else:
            raise ValueError("Linux/Mac COM port support hasn't configured yet.")


class UfosDataToCom:
    def __init__(self, expo, accumulate, channel, start_flag='S'):
        """
        Bytes string preparation and sending to COM
        Args:
            expo (int): Mesurement exposition [ms]
            accumulate (int): Amount of measurements in a row to get more accurate spectre
            channel (str): 'Z' - zenith channel, 'S' - summary channel, 'D' - dark channel
            start_flag (str): Default = 'S' - run measurement,
                any other symbol - change channel only
        """
        self.com_obj = UfosConnection().get_com()
        self.expo = expo
        self.data_send = b''
        self.accumulate = accumulate
        self.data_send = (b'#\x00\x01' +
                          bytes((int(expo) % 256, int(expo) // 256)) +
                          b'0' +
                          bytes((int(accumulate),)) +
                          b'0' +
                          channel.encode('utf-8') +  # Z, S, D
                          start_flag.encode('utf-8')  # S
                          )

    def device_ask(self, tries_allowed=3):
        tries_done = 0
        while tries_done < tries_allowed:
            to = int(self.expo * self.accumulate / 1000) + 1
            self.com_obj = UfosConnection(to).get_com()
            self.com_obj.open()
            self.com_obj.write(self.data_send)
            byte = b''
            while not byte:
                sleep(1)
                byte = self.com_obj.read(13)
            data = byte
            while byte:
                data += byte
                byte = self.com_obj.read(2)
            self.com_obj.close()
            # Если получили данные с УФОС за timeout
            if data:
                temper = data[6:10]
                t1 = (temper[0] * 255 + temper[1]) / 10  # Линейка
                t2 = (temper[2] * 255 + temper[3]) / 10  # Полихроматор
                if len(data) > 13:
                    index = len(data) - 1
                    spectr = []
                    while index > 13:
                        index -= 1
                        spectr.append(data[index + 1] * 255 + data[index])
                        index -= 1
                else:
                    spectr = [0] * 3691
                text = 'Амп = {}'.format(max(spectr[PIX_WORK_INTERVAL]))
                return spectr[:3691], t1, t2, text, 0
            # Если не получили данные с УФОС за timeout
            else:
                if tries_done > 0:
                    text = 'Внимание! Данные не получены (Проверьте подключение кабеля к УФОС).\nПробуем ещё раз...'
                    print(text)
                    LOGGER.warning(text)
                tries_done += 1
        text = 'Сбой! Данные не получены (Проверьте подключение кабеля к УФОС)'
        print(text)
        LOGGER.error(text)
        return [0], 0, 0, '', tries_done
