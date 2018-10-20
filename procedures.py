from math import *
import serial
import time
import datetime
import winreg
import os
import winsound
import sys
import json
import numpy as np
import socket
import base64

# Selivanova


def get_new_corrects(o3s, o3s_tmp, pars):
    sigma = round(np.std(o3s_tmp), 3)
    mean = int(np.mean(o3s_tmp))
    corrects = []
    for i in o3s:
        if mean - pars['calibration']['sigma_count'] * sigma < i < mean + pars['calibration']['sigma_count'] * sigma:
            corrects.append('1')
        else:
            corrects.append('0')
    return corrects, sigma, mean


def calculate_final_files(pars, file, mode):
    "Функция для вычисления значения полинома"
    try:
        if file:
            with open(file) as f:
                all_data = f.readlines()
                data = all_data[1:]
            if mode == 'ZD':
                lines_arr_raw_to_file = [] # Массив старых строк с лишними \t с делением на \t
                o3s_1 = [] # Весь озон
                o3s_tmp1 = [] # 600> Озон >150 (Первая корректировка при измерении)
                o3s_2 = []  # Весь озон
                o3s_tmp2 = []  # 600> Озон >150 (Первая корректировка при измерении)
                k1 = []
                k2 = []
                for line in data:
                    line_arr_raw = line.split(';')
                    lines_arr_raw_to_file.append(line_arr_raw)
                    line_arr = [i for i in line_arr_raw if i]
                    o3_1 = int(line_arr[3])
                    correct1 = int(line_arr[4])
                    o3_2 = int(line_arr[5])
                    correct2 = int(line_arr[6])
                    o3s_1.append(o3_1)
                    o3s_2.append(o3_1)
                    if correct1 == 1:
                        o3s_tmp1.append(o3_1)
                        k1.append(1)
                    else:
                        k1.append(0)
                    if correct2 == 1:
                        o3s_tmp2.append(o3_2)
                        k2.append(1)
                    else:
                        k2.append(0)
                text_mean = ''
                corrects1_actual = k1[:]
                corrects2_actual = k2[:]
                if o3s_tmp1:
                    corrects1, sigma1, mean1 = get_new_corrects(o3s_1, o3s_tmp1, pars)
                    corrects1_actual = []
                    for i in k1:
                        if i == 1:
                            corrects1_actual.append(corrects1.pop(0))
                        else:
                            corrects1_actual.append('0')
                    text_mean += 'Среднее значение ОСО (P1): {}\nСтандартное отклонение: {}\n'.format(mean1, sigma1)
                if o3s_tmp2:
                    corrects2, sigma2, mean2 = get_new_corrects(o3s_2, o3s_tmp2, pars)
                    corrects2_actual = []
                    for i in k2:
                        if i == 1:
                            corrects2_actual.append(corrects2.pop(0))
                        else:
                            corrects2_actual.append('0')
                    text_mean += 'Среднее значение ОСО (P2): {}\nСтандартное отклонение: {}'.format(mean2, sigma2)
                with open(os.path.join(os.path.dirname(file), 'mean_' + os.path.basename(file)), 'w') as f:
                    print(';'.join(all_data[:1]), file=f, end='')
                    for line, correct1, correct2 in zip(lines_arr_raw_to_file, corrects1_actual, corrects2_actual):
                        part1 = line[:-3]
                        part2 = line[-2:-1]
                        print(';'.join(part1 + [correct1] + part2 + [correct2]), file=f)
                    print(text_mean, file=f)
                    print('Mean File Saved: {}'.format(os.path.join(os.path.dirname(file), 'mean_' + os.path.basename(file))))
            elif mode == 'SD':
                pass
    except Exception as err:
        print(err, sys.exc_info()[-1].tb_lineno)


def get_polynomial_result(coefficients, x):
    if type(coefficients[0]) == float:
        return coefficients[2] * float(x)**2 + coefficients[1] * float(x) + coefficients[0]
    else:
        return eval(coefficients[2]) * float(x)**2 + eval(coefficients[1]) * float(x) + eval(coefficients[0])


def sumarize(a):
    sum = 0
    for i in a:
        if i != '':
            sum += float(i)
    try:
        return round(sum, 3)
    except:
        return 0


def read_nomographs(home, mueff_list, r12_list, ozone_list, dev_id):
    if os.path.exists(os.path.join(home, r'nomograph{}.txt'.format(dev_id))):
        file_n = open(os.path.join(home, r'nomograph{}.txt'.format(dev_id)), 'r')
        ozone_number = 0
        mueff_number = 0
        mueff_step = 0.05
        while True:
            line = file_n.readline()
            if line.find('MuEff\t\t\t') != -1:
                continue
            'количество линий озона'
            if line.find('Ozone\tnumber\t\t\t') != -1:
                ozone_number = int(line.split('\t')[0])
                continue
            if line.find('Mueff\tnumber\t\t\t') != -1:
                mueff_number = int(line.split('\t')[0])
                continue
            if line.find('Mueff\tstep\t\t\t') != -1:
                mueff_step = float(line.split('\t')[0])
                continue
            'массив со значениями озона'
            if line.find('\tOzon\tnumber\n') != -1:
                ozone_list_str = line.split('\t')[:ozone_number]
                ozone_list_int = [int(ozone) for ozone in ozone_list_str]
                ozone_list.extend(list(reversed(ozone_list_int)))
                continue
            'Текст закончился - выход'
            if line == '' or line == '\n':
                break
            else:
                r12_list_str = line.split('\t')[:ozone_number]
                r12_list_float = [float(r12) for r12 in r12_list_str]
                r12_list_float_reversed = list(reversed(r12_list_float))
                r12_list.append(list(reversed(r12_list_float)))
                mueff = line.split('\t')[ozone_number:ozone_number+1:1][0]
                mueff_list.append(float(mueff))
        file_n.close()


def find_index_value_greater_x(list, x):
    """Reversed = true, когда последовательность отсортирована не в том порядке - от возрастающего к убывающему"""
    index_value_high = next((list.index(value) for value in list if value > x), len(list)-1)
    "Если ниже минимального значения - берём 2 ближайших значения"
    if index_value_high == 0:
        index_value_high = 1
    return index_value_high


def get_ozone_by_nomographs(home, r12clear, mueff, dev_id):
    "Чтение номограммы"
    ozone_list = []
    r12_list = []
    mueff_list = []
    read_nomographs(home, mueff_list, r12_list, ozone_list, dev_id)
    "Найти значения mueff, между которыми находится наше значение"
    index_mueff_high = find_index_value_greater_x(mueff_list, mueff)
    index_mueff_low = index_mueff_high - 1
    "вычисление r12 на нижней и на верхней номограмме путём линейной интерполяции"
    r12high_index = find_index_value_greater_x(r12_list[index_mueff_high], r12clear)
    r12low_index = r12high_index - 1
    r12low = r12_list[index_mueff_low][r12low_index]\
             + (r12_list[index_mueff_high][r12low_index] - r12_list[index_mueff_low][r12low_index])\
             * (mueff - mueff_list[index_mueff_low])\
             / (mueff_list[index_mueff_high] - mueff_list[index_mueff_low])
    r12high = r12_list[index_mueff_low][r12high_index]\
              + (r12_list[index_mueff_high][r12high_index] - r12_list[index_mueff_low][r12high_index])\
              * (mueff - mueff_list[index_mueff_low])\
              / (mueff_list[index_mueff_high] - mueff_list[index_mueff_low])
    ozone = ozone_list[r12low_index] \
            + ((ozone_list[r12high_index] - ozone_list[r12low_index]) * (r12clear - r12low)) / (r12high - r12low)
    return ozone
# ==========================================================


def read_connect(home):
    with open(os.path.join(home, 'connect.ini')) as f:
        data = f.readlines()
        new_data = {}
        for i in data:
            if i[0] not in ['\n', ' ', '#']:
                line = i.replace(' ', '').replace('\n', '').split('=')
                new_data[line[0]] = line[1]
        return new_data


def erithema(x,c):
    nm = (x**2) * eval(c[0]) + x * eval(c[1]) + eval(c[2])
    a = 0
    if nm<=298:
        a = 1
    elif 298<nm:#<=325:
        a = 10**(0.094 * (298 - nm))
##    elif nm>325:
##        a = 10**(-0.015 * (410 - nm))
    return(a)

def read_sensitivity(path,ufos_id):
    with open(os.path.join(path,'sensitivity{}.txt'.format(ufos_id))) as f:
        sens = f.readlines()
##        new = []
##        for i in sens:
##            i = i.strip()
##            try:
##                new.append(float(i))
##            except:
##                print([i])
    return([float(i.strip()) for i in sens if i.strip()])

def read_sensitivity_eritem(path,ufos_id):
    with open(os.path.join(path,'senseritem{}.txt'.format(ufos_id))) as f:
        sens = f.readlines()
##        new = []
##        for i in sens:
##            i = i.strip()
##            try:
##                new.append(float(i))
##            except:
##                print([i])
    return([float(i.strip()) for i in sens if i.strip()])

def nm2pix(nm,configure2,add):
    nm = float(nm)
    abc = configure2
    if 270 < nm < 350:
        pix = 0
        ans_nm = pix2nm(abc,pix,1,add)
        while ans_nm < nm:
            pix += 1
            ans_nm = pix2nm(abc,pix,1,add)
    elif 350 <= nm < 430:
        pix = 1500
        ans_nm = pix2nm(abc,pix,1,add)
        while ans_nm < nm:
            pix += 1
            ans_nm = pix2nm(abc,pix,1,add)
    else:
        print(nm,'nm2pix: error')
    return(pix)

def pix2nm(abc,pix,digs,add):
    """
    Обработка одного пикселя
    abc - массив коэффициентов полинома
    pix - номер пиксела
    dig - количество знаков после запятой
    add - сдвиг для зенитных измерений
    """
    try:
        return round(eval(abc[0]) * pix**2 + eval(abc[1]) * pix + eval(abc[2]) + add,digs)
    except:
        return 0
    
def read_path(home,path,mode):
    """Чтение файла last_path"""
    last_path = os.path.join(home,'last_path.txt')
    if mode == 'r' and os.path.exists(last_path):
        file_n = open(last_path, 'r')
        return file_n.readline()
    else:
        file_n = open(last_path, 'w')
        file_n.write(path)
    file_n.close()
    return path


def spectr2zero(p_zero1,p_zero2,p_lamst,spectr):
    mv = 0
    zero_count = 0
    spectrum = [0] * len(spectr)
    for i in range(p_zero1, p_zero2 + 1):
        mv = mv + spectr[i]
        zero_count += 1
    mv = mv / zero_count
    for i in range(p_lamst, len(spectr)-1):
        spectrum[i] = round(spectr[i] - mv)
    return spectrum


def pre_calc_o3(lambda_consts, lambda_consts_pix, spectrum, prom, mu, var_settings, home):
    # print(lambda_consts, lambda_consts_pix)
    p_mas = []
    j = 0
    while j < len(lambda_consts):
        jj = lambda_consts_pix[j]  # in Pixels
        s = sumarize(spectrum[jj - prom:jj + prom + 1])
        if s:
            p_mas.append(s)
        else:
            p_mas.append(1)
        j += 1
    r12m = p_mas[0] / p_mas[1]
    r23m = p_mas[2] / p_mas[3]
    mueff = (1 + mu) / 2
    if mueff < 2:
        r23clean = get_polynomial_result(var_settings['calibration2']['kzLess2'], mueff)
    else:
        r23clean = get_polynomial_result(var_settings['calibration2']['kzLarger2'], mueff)
    kz_obl_f = get_polynomial_result(var_settings['calibration2']['kz_obl'], (r23clean/r23m))
    r12clear = kz_obl_f * r12m
    try:
        o3 = int(get_ozone_by_nomographs(home, r12clear, mueff, var_settings['device']['id']))
    except Exception as err:
        print('Plotter: ', err)
        o3 = -1
    if 150 <= o3 <= 600: correct = 1
    else: correct = 0
    return o3, correct


class Profiler(object):
    def __enter__(self):
        self._startTime = time.time()
        logger.debug('Timer started.')
         
    def __exit__(self, type, value, traceback):
        logger.debug("Timer stopped. Elapsed time: {:.3f} seconds".format(time.time() - self._startTime))


class UfosConnection:
    """UFOS mesure class"""
    def __init__(self, to=1):
        self.opened_serial = None
        self.br = 115200                       #Baudrate
        self.bs = 8                            #Byte size
        self.par = 'N'                         #Parity
        self.sb = 1                            #Stop bits
        self.to = to                           #Time out (s)
        
    def get_com(self):
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM")
            for i in range(255):
                name, value, typ = winreg.EnumValue(registry_key, i)
                if name.count('Silab') > 0:
                    self.opened_serial = serial.Serial(port='//./' + value,
                                                       baudrate=self.br,
                                                       bytesize=self.bs,
                                                       parity=self.par,
                                                       stopbits=self.sb,
                                                       timeout=self.to)
                    self.opened_serial.close()
                    return {'com_number': value, 'com_obj': self.opened_serial}
        except WindowsError:
            text = "Кабель не подключен к ПК!                   "
            print(text, end='\r')
            logger.error(text)


class CalculateOnly:
    # Calculate for mesurement
    def __init__(self, var_sets, home):
        self.home = home
        self.var_sets = var_sets
        self.confZ = self.var_sets['calibration']['nm(pix)']['Z']
        self.confS = self.var_sets['calibration']['nm(pix)']['S']
        self.lambda_consts1 = self.var_sets['calibration']['points']['o3_pair_1'] + \
                              self.var_sets['calibration']['points']['cloud_pair_1']
        self.lambda_consts2 = self.var_sets['calibration']['points']['o3_pair_2'] + \
                              self.var_sets['calibration']['points']['cloud_pair_2']
        self.p_uva1, self.p_uva2 = nm2pix(315, self.confS, 0), nm2pix(400, self.confS, 0)
        self.p_uvb1, self.p_uvb2 = nm2pix(280, self.confS, 0), nm2pix(315, self.confS, 0)
        self.p_uve1, self.p_uve2 = 0, 3691 #nm2pix(290),nm2pix(420)
        self.p_zero1 = nm2pix(290, self.confZ, 0)
        self.p_zero2 = nm2pix(295, self.confZ, 0)
        self.p_lamst = nm2pix(290, self.confZ, 0)
        self.lambda_consts_pix1 = [] #Массив констант лямбда в пикселях
        for i in self.lambda_consts1:
            self.lambda_consts_pix1.append(nm2pix(i, self.confZ, 0))
        self.lambda_consts_pix2 = []  # Массив констант лямбда в пикселях
        for i in self.lambda_consts2:
            self.lambda_consts_pix2.append(nm2pix(i, self.confZ, 0))

                # Calc ozone
        self.o3 = 0
        self.prom = int(self.var_sets['calibration2']['pix+-'] / eval(self.confZ[1]))
        self.f = self.var_sets['station']['latitude']
        self.l = self.var_sets['station']['longitude']
        self.pelt = int(self.var_sets['station']['timezone'])
        # Calc UV
        self.uv = 0
        self.curr_o3_dict = {'uva': [2, self.p_uva1, self.p_uva2],
                             'uvb': [3, self.p_uvb1, self.p_uvb2],
                             'uve': [4, self.p_uve1, self.p_uve2]}
    
    def calc_ozon(self, spectr, mu):
        """
        data['spectr'] => spectrum
        data['mu']
        """
        spectrum = spectr2zero(self.p_zero1, self.p_zero2, self.p_lamst, spectr)
        """Расчет озона"""
        o3_1, correct1 = pre_calc_o3(self.lambda_consts1, self.lambda_consts_pix1, spectrum, self.prom, mu, self.var_sets,
                                     self.home)
        o3_2, correct2 = pre_calc_o3(self.lambda_consts2, self.lambda_consts_pix2, spectrum, self.prom, mu, self.var_sets,
                                     self.home)
        return {'o3_1': int(round(o3_1)), 'o3_2': int(round(o3_2)), 'correct1': correct1, 'correct2': correct2}

    def calc_uv(self, uv_mode, spectr, expo, sensitivity, sens_eritem):
        p1 = self.curr_o3_dict[uv_mode][1]
        p2 = self.curr_o3_dict[uv_mode][2]
       # print(uv_mode)
        spectrum = spectr2zero(self.p_zero1, self.p_zero2, self.p_lamst, spectr)
        try:
            if uv_mode in ['uva','uvb']:
                uv = sum(np.array(spectrum[p1:p2]) * np.array(sensitivity[p1:p2]))
            elif uv_mode == 'uve':
                uv = sum([float(spectrum[i]) * sens_eritem[i] * sensitivity[i] for i in range(p1,p2,1)])
           #     print(uv)
           # print(eval(self.confS[1]))
           # print(self.var_sets['device']['graduation_expo'])
           # print(data['mesurement']['exposition'])
            uv *= float(eval(self.confS[1])) * self.var_sets['device']['graduation_expo'] / expo
           # uv *= float(self.var_sets['calibration']['{}_koef'.format(uv_mode)])
        except Exception as err:
            print('procedures.calc_uv: ',err)
            uv = 0
        return(int(round(uv,1)))
       # if self.o3_mode!='spectr':
       #     self.x.append(self.data['datetime'])
       #     self.y.append(uv)
            
class Ufos_data:
    """UFOS mesure class"""
    def __init__(self, expo, accum, mesure_type, start_mesure):
        """Преобразование данных запроса в необходимый тип для отправки в прибор
        dev_id - номер прибора (всегда = 1)
        expo - время измерения в мс
        accum - количество суммирований измерений (время измерения = expo * accum)
        mesure_type - тип измерений (Z=зенит, S=полусфера, D=темновой)
        start_mesure - S=запустить измерение, любой другой символ только переключит канал измерения."""
        self.expo = expo
        self.accum = accum
        self.start_mesure = start_mesure
        parameters = []
        parameters.append(b'#')                                             # header = #
        parameters.append(b'\x00\x01')                                      # device id = 1
        parameters.append(bytes((int(expo) % 256, int(expo) // 256)))
        parameters.append(b'0')                                             # gain = 0
        parameters.append(bytes((int(accum),)))
        parameters.append(b'0')                                             # cooler = 0
        parameters.append(mesure_type.encode(encoding='utf-8'))             # Z, S, D
        parameters.append(start_mesure.encode(encoding='utf-8'))            # S 
        # i = 1
        # crc = ord(parameters[0])
        # while i<len(parameters):
        #     crc = (crc * 2 + (crc // 256 & 1)) & 0xff
        #     crc ^= i + 1
        #     i+=1
        # parameters.append(bytes((crc,)))
        self.data_send = b''
        for byte in parameters:
            self.data_send += byte
            
    def device_ask(self, tries):
        data = b''
        to = int(self.expo * self.accum / 1000) + 1
        self.com_obj = UfosConnection(to).get_com()['com_obj']
        self.com_obj.open()
        with Profiler() as p:
            self.com_obj.write(self.data_send)
        logger.debug('Sleep {} seconds...'.format(to))
        time.sleep(to)
        with Profiler() as p:
            byte = self.com_obj.read(1)
            while byte:
                data += byte
                byte = self.com_obj.read(1)
            self.com_obj.close()
        if data:
            tries = 0
            i = data[6:10]
            t1 = (i[0] * 255 + i[1]) / 10 #Линейка
            t2 = (i[2] * 255 + i[3]) / 10 #Полихроматор
            if len(data)>13:
                i = len(data) - 1
                spectr = []
                while i>13:
                    i -= 1
                    spectr.append(int(data[i+1]) * 255 + int(data[i]))
                    i -= 1
                text = 'Амп = {}'.format(max(spectr[100:3600]))
            else:
                spectr = [0]
                text = ''
            return(spectr[:3691], t1, t2, text, tries)
        else:
##            print(tries)
            if tries>1:
                text ='Сбой! Данные не получены (Проверьте подключение кабеля к УФОС)'
                print(text)
                logger.error(text)
            tries += 1
            return([0],0,0,'',tries)
    
class settings:
    def get(home):
        with open(os.path.join(home,'settings.py'),'r') as f:
            return(json.load(f))
    def set(home,pars):
        with open(os.path.join(home,'settings.py'),'w') as f:
            return(json.dump(pars,f,ensure_ascii=False,indent='    ',sort_keys=True))

def sunheight(altitude,longitude,date_time,timezone):
    f,l,timezone = float(altitude),float(longitude),int(timezone)
    # Расчёт высоты солнца всегда по UTC, поэтому "timezone=0"
    timezone = 0 
    """
    altitude - широта в градусах и минутах (+-ГГ.ММ) +северная -южная
    longitude - долгота в градусах и минутах (+-ГГ.ММ) +западная -восточная
    date_time - дата+время
    timezone - часовой пояс (+-П)
    """
    f = (f - 0.4 * copysign(1, f) * round(abs(f) // 1)) * pi / 108
    l = (l - 0.4 * copysign(1, l) * round(abs(l) // 1)) / 0.6 
    timer = date_time.hour * 3600 + date_time.minute * 60 + date_time.second  #Текущее время в секундах
    tim = timer - 3600 * timezone               #Гринвическое время
    day = date_time.day + 58
    month = date_time.month
    year = date_time.year
    if month < 3:
        year -= 1
    d_m = [3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 1]   #Месяцы кроме февраля
    d_d = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31]  #Количество дней в месяце
    i = 0
    while i<11:
        if month == d_m[i]: break
        else: day += d_d[i]
        i += 1
    dd = day + 365 * year + round(year // 4) - round(year // 100) + round(year // 400) + 13 / 38
    day = (dd + tim / 3600 / 24) * pi / 182.6213
    s = 0.00686 - 0.39915 * cos(day) + 0.07432 * sin(day)
    s += -0.00693 * cos(2 * day) + 0.00114 * sin(2 * day)
    s += -0.00226 * cos(3 * day) + 0.0012 * sin(3 * day)
    ty = -0.017 - 0.43 * cos(day) + 7.35 * sin(day) + 3.35 * cos(2 * day) + 9.366 * sin(2 * day)
    r = pi * (tim / 3600 - ty / 60 - l / 15 - 12) / 12
    q = sin(f) * sin(s) + cos(f) * cos(s) * cos(r)
    hp = atan(q / sqrt(1 - q**2))
    hg = hp * 180 / pi
    z = sin(pi / 2 - hp)**2
    mu = 6391.229 / sqrt(6391.229**2 - 6371.223**2 * z)
    z1 = 1 / cos(pi / 2 - hp)
    amas = 0
    if hg <= 0:
        pass
##        hg = 0
    elif 0 < hg <20:
        amas = 45.022 * hg**(-0.9137)
    else:
        amas = z1 - (z1 - 1) * (0.0018167 - 0.002875 * (z1 - 1) - 0.0008083 * (z1 -1)**2)
    return(round(mu,3),round(amas,3),round(hg,3))

def get_time_next_start(latitude,longitude,timezone,sun_height_min):
    """Расчёт времени следующего измерения"""
    time_now = datetime.datetime.now()
    mu,amas,sh = sunheight(latitude,longitude,time_now,timezone)
    if sh < sun_height_min:
        for t in [3600,60,1]:
            while sh < sun_height_min:
                time_now += datetime.timedelta(0,t)
                mu,amas,sh = sunheight(latitude,longitude,time_now,timezone)
            else:
                time_now -= datetime.timedelta(0,t)
                mu,amas,sh = sunheight(latitude,longitude,time_now,timezone)
    return(str(time_now).split('.')[0])


def make_dirs(dirs, home):
    path = home
    # dirs = ['1','2','2'] > home\1\2\3
    for i in dirs:
        path = os.path.join(path,str(i))
        if not os.path.exists(path):
            os.mkdir(path)
    return path


def write_final_file(pars, home, chan, date_utc, sunheight, calc_result, add_to_name, create_new_file):
    # Ozone/UV calculation and write to final file 
    try:
        date = datetime.datetime.strptime(date_utc, '%Y%m%d %H:%M:%S')
        date_local = datetime.datetime.strftime(date + datetime.timedelta(hours=int(pars["station"]["timezone"])),
                                                '%Y%m%d %H:%M:%S') # Local Datetime
        if chan == 'ZD':
            t = 'Ozone'
            # header = 'DatetimeUTC\t\t\tDatetimeLocal\t\tSunheight[°]\tOzoneP1[D.u.]\tCorrectP1\tOzoneP2[D.u.]\tCorrectP2'
            #             # text_out = '{}\t{}\t{}\t\t\t{}\t\t\t{}'.format(date_utc,
            #             #                                                date_local,
            #             #                                                sunheight,
            #             #                                                calc_result['o3_1'],
            #             #                                                calc_result['correct1'],
            #             #                                                calc_result['o3_2'],
            #             #                                                calc_result['correct2'])
            header = ';'.join(['DatetimeUTC', 'DatetimeLocal', 'Sunheight[°]', 'OzoneP1[D.u.]', 'CorrectP1', 'OzoneP2[D.u.]', 'CorrectP2'])
            text_out = ';'.join([str(i) for i in [date_utc, date_local, sunheight, calc_result['o3_1'], calc_result['correct1'], calc_result['o3_2'], calc_result['correct2']]])
        elif chan == 'SD':
            t = 'UV'
            # header = 'DatetimeUTC\t\t\tDatetimeLocal\t\tSunheight[°]\tUV-A[mWt/m^2]\tUV-B[mWt/m^2]\tUV-E[mWt/m^2]'
            # text_out = '{}\t{}\t{}\t\t\t{}\t\t\t{}\t\t\t{}'.format(date_utc,
            #                                             date_local,
            #                                             sunheight,
            #                                             calc_result['uva'],
            #                                             calc_result['uvb'],
            #                                             calc_result['uve'])
            header = ';'.join(['DatetimeUTC', 'DatetimeLocal', 'Sunheight[°]', 'UV-A[mWt/m^2]', 'UV-B[mWt/m^2]', 'UV-E[mWt/m^2]'])
            text_out = ';'.join([str(i) for i in [date_utc, date_local, sunheight, calc_result['uva'], calc_result['uvb'], calc_result['uve']]])
        if chan == 'ZD' or chan == 'SD':
            dirs = ['Ufos_{}'.format(pars['device']['id']),
                                     t,
                                     datetime.datetime.strftime(date, '%Y'),
                                     datetime.datetime.strftime(date, '%Y-%m')]
            name = '{}m{}_{}_{}.txt'.format(add_to_name,
                                            pars['device']['id'],
                                            t,
                                            datetime.datetime.strftime(date, '%Y%m%d'))
            path = make_dirs(dirs, home)
            if not os.path.exists(os.path.join(path, name)) or create_new_file:
                with open(os.path.join(path, name), 'w') as f:
                    print(header, file=f)
            with open(os.path.join(path, name), 'a') as f:
                print(text_out, file=f)
        return os.path.join(path, name)
    except Exception as err:
        print('write_final_file:', end='')
        print(err, sys.exc_info()[-1].tb_lineno)
        logger.error(str(err))


class Main:
    """UFOS mesure class"""
    def __init__(self,pars):
        self.tries = 0
        self.mesure_count = 0
        self.last_file_o3 = ''
        self.last_file_uv = ''
        self.mesure_data = {'ZD':{},'SD':{}}
        self.calc_result = {'ZD':{},'SD':{}}
        self.file2send = {}
        self.t1 = ''
        self.t2 = ''
        self.pars = pars
        self.home = os.getcwd()
        self.connect_pars = read_connect(self.home)
        self.sensitivity = read_sensitivity(self.home,self.pars['device']['id'])
        self.sensitivity_eritem = read_sensitivity_eritem(self.home,self.pars['device']['id'])
        self.time_now = datetime.datetime.now()
        dirs = ['Ufos_{}'.format(self.pars['device']['id']),
                     'Mesurements',
                     datetime.datetime.strftime(self.time_now,'%Y'),
                     datetime.datetime.strftime(self.time_now,'%Y-%m'),
                     datetime.datetime.strftime(self.time_now,'%Y-%m-%d')]
        self.path = os.path.join(self.home,*dirs)    
    
    def analyze_spectr(self,spectr):
        try:
            self.time_now = datetime.datetime.now() # UTC Datetime
            self.time_now_local = self.time_now + datetime.timedelta(hours=int(self.pars["station"]["timezone"])) # Local Datetime
            """Расчёт высоты солнца"""
            self.mu,self.amas,self.sunheight = sunheight(self.pars["station"]["latitude"],
                                   self.pars["station"]["longitude"],
                                   self.time_now,
                                   self.pars["station"]["timezone"])
            """Запись шапки файла"""                                                    
            self.text = {"id": {
                             "device":self.pars["device"]["id"],
                             "station":self.pars["station"]["id"]
                             },
                         "mesurement":{
                             "datetime": datetime.datetime.strftime(self.time_now,'%Y%m%d %H:%M:%S'),
                             "datetime_local": datetime.datetime.strftime(self.time_now_local,'%Y%m%d %H:%M:%S'),
                             "timezone":self.pars["station"]["timezone"],
                             "latitude": self.pars["station"]["latitude"], 
                             "longitude": self.pars["station"]["longitude"],
                             "exposition": self.expo,
                             "accummulate": self.pars["device"]["accummulate"],
                             "channel": self.chan,
                             "temperature_ccd": self.t1,
                             "temperature_poly": self.t2
                             },
                         "calculated": {
                             "mu": round(self.mu,4),
                             "amas": round(self.amas,4),
                             "sunheight": round(self.sunheight,4),
                             "sko": round(float(np.std(spectr[300:3600])),4),
                             "mean": round(float(np.mean(spectr[300:3600])),4),
                             "dispersia": round(float(np.var(spectr[300:3600])),4)
                             }
                         }
            if self.chan in ['Z','S']:
                """Расчёт СКО для Спектра (-) altD (темновой до 500 пикс)"""
                self.spectrZaD = np.array(spectr) - np.mean(spectr[100:500])
                self.skoZaD = np.std(self.spectrZaD[100:3600])
                self.text["spectr"] = np.array(spectr).tolist()
            elif self.chan[0]=='D':
                # Если 'СКО D измеренное' < 100 И 'СКО Z-aD' > 100"""
                if self.text["calculated"]["sko"]<self.pars["calibration"]["sko_D"] and self.skoZaD>self.pars["calibration"]["sko_ZaD"]:
                    self.altD_flag = 0
                # Если 'СКО D измеренное' > 100 И 'СКО Z-aD' > 100"""
                elif self.text["calculated"]["sko"]>self.pars["calibration"]["sko_D"] and self.skoZaD>self.pars["calibration"]["sko_ZaD"]:
                    self.altD_flag = 1
                else:
                    self.altD_flag = 2
                self.text["spectr"] = np.array(spectr).tolist()
            elif self.chan in ['ZD','SD']:
                if self.altD_flag == 0:
                    # Если всё ок
                    self.text["spectr"] = np.array(spectr).tolist()
                    self.text["mesurement"]["status"] = 0
                elif self.altD_flag == 1:
                    # Если плохой темновой спектр, использовать альтернативный темновой (spectr[100:500])
                    self.text["spectr"] = np.array(self.spectrZaD).tolist()
                    self.text["mesurement"]["status"] = 1
                else:
                    self.text["spectr"] = np.array(spectr).tolist()
                    self.text["mesurement"]["status"] = 2
        except Exception as err:
            print('analyze_spectr:',end='')
            print(err, sys.exc_info()[-1].tb_lineno)
            logger.error(str(err))
                
    def pix2nm(self,pix):
        nm = 0
        deg = len(self.pars["calibration"]["nm(pix)"]["Z"]) - 1
        for i in self.pars["calibration"]["nm(pix)"]["Z"]:
            nm += eval(i) * pix**deg 
            deg -= 1
        return(nm)
    
    def nm2pix(self,nm):
        pix = 0
        while self.pix2nm(pix)<nm:
            pix += 1
        return(pix)
        
    def nms2pixs(self):
        self.pixs = {}
        for pair in self.pars["calibration"]["points"].keys():
            self.pixs[pair+'_pix'] = []
            for nm in self.pars["calibration"]["points"][pair]:
                self.pixs[pair+'_pix'].append(self.nm2pix(nm))

    def calc_final_file(self, pars, home, spectr, mu, expo, sensitivity, sensitivity_eritem):
        calco = CalculateOnly(pars, home)
        if self.chan == 'ZD':
            o3_dict = calco.calc_ozon(spectr, mu)
            o3_1, correct1 = o3_dict['o3_1'], o3_dict['correct1']
            o3_2, correct2 = o3_dict['o3_2'], o3_dict['correct2']
            # out = {'o3': o3,
            #        'correct': correct}
            print('=> OZONE: P1 = {}, P2 = {}'.format(o3_1, o3_2))
        elif self.chan == 'SD':
            uva = calco.calc_uv('uva', spectr, expo, sensitivity, sensitivity_eritem)
            uvb = calco.calc_uv('uvb', spectr, expo, sensitivity, sensitivity_eritem)
            uve = calco.calc_uv('uve', spectr, expo, sensitivity, sensitivity_eritem)
            o3_dict = {'uva': uva, 'uvb': uvb, 'uve': uve}
        self.calc_result[self.chan] = o3_dict
            
    def write_file(self):
        try:
            dirs = ['Ufos_{}'.format(self.pars['device']['id']),
                         'Mesurements',
                         datetime.datetime.strftime(self.time_now_local,'%Y'),
                         datetime.datetime.strftime(self.time_now_local,'%Y-%m'),
                         datetime.datetime.strftime(self.time_now_local,'%Y-%m-%d')]
            dirs_sending = ['Ufos_{}'.format(self.pars['device']['id']),
                            'Sending']
            self.path = make_dirs(dirs,self.home)
            self.path_sending = make_dirs(dirs_sending,self.home)
            
            self.name = 'm{}_{}_{}_{}.txt'.format(self.pars['device']['id'],
                                             str(self.mesure_count).zfill(3),
                                             self.chan,
                                             datetime.datetime.strftime(self.time_now_local,'%Y%m%d%H%M'))
            
            with open(os.path.join(self.path,self.name),'w') as f:
                json.dump(self.text,f,ensure_ascii=False,indent='',sort_keys=True)
                print('>>> {}'.format(self.name))
                logger.info('>>> {}'.format(self.name))
            if self.chan in ['ZD','SD']:
                self.file2send[self.chan] = self.name
                # self.calc_result[self.chan] <<
                self.calc_final_file(self.pars,
                                   self.home,
                                   self.text['spectr'],
                                   self.text['calculated']['mu'],
                                   self.text['mesurement']['exposition'],
                                   self.sensitivity,
                                   self.sensitivity_eritem)
                path_file = write_final_file(self.pars,
                                             self.home,
                                             self.chan,
                                             self.text["mesurement"]["datetime"],
                                             round(self.text["calculated"]["sunheight"],1),
                                             self.calc_result[self.chan],
                                             '',
                                             False)
                
                if self.chan=='ZD':
                    self.last_file_o3 = path_file
                elif self.chan=='SD':
                    self.last_file_uv = path_file
        except Exception as err:
            print('write_file (spectr): ',end='')
            print(err,sys.exc_info()[-1].tb_lineno)
            logger.error(str(err))
    
    def change_channel(self,chan):
        logger.debug('Переключение на канал {}.'.format(self.pars['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8')))
        data,t1,t2,text,self.tries = Ufos_data(50,self.pars['device']['accummulate'],chan, 'N').device_ask(self.tries)
        return self.tries

    def write_file4send(self,chan,data4send):
        with open(os.path.join(self.path_sending,self.file2send[chan]),'w') as f:
            f.write(data4send)
    
    def make_line(self):
        try:
            debug = 0
            encode = 0
            if debug:
                with open('test.txt', 'w') as f:
                    print(self.mesure_data, file=f)   # mesurement
                    print('==========================================', file=f)
                    print(self.pars, file=f)          # settings
                    print('==========================================', file=f)
                    print(self.connect_pars, file=f)  # connect settings
                    print('==========================================', file=f)
                    print(self.calc_result, file=f)   # o3 + uv
            if encode:
                points2send = base64.b64encode(str(self.pars['calibration']['points']).encode('ascii')).decode('ascii')
                pars2send = base64.b64encode(str(self.pars).encode('ascii')).decode('ascii')
            else:
                points2send = str(self.pars['calibration']['points']).replace("'", '"')
                pars2send = str(self.pars).replace("'", '"')
            for chan in self.calc_result.keys():
                uva, uvb, uve = 0, 0, 0
                o3 = 0
                correct = -1
                if chan == 'ZD':
                    correct = self.calc_result[chan]['correct1']
                    o3 = self.calc_result[chan]['o3_1']
                elif chan == 'SD':
                    uva = self.calc_result[chan]['uva']
                    uvb = self.calc_result[chan]['uvb']
                    uve = self.calc_result[chan]['uve']
                    
                data4send = """#{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10};\
{11}@{12};{13};{14};{15};{16};{17};{18};{19};{20};\
{21};{22};{23};{24};{25};{26};{27};{28};{29};{30};{31}#""".format(self.mesure_data[chan]['id']['device'],
                                                                  self.mesure_data[chan]['id']['station'],
                                                                  self.mesure_data[chan]['mesurement']['channel'][0]+'-'+self.mesure_data[chan]['mesurement']['channel'][1],
                                                                  self.mesure_data[chan]['mesurement']['datetime'],
                                                                  self.mesure_data[chan]['mesurement']['exposition'],
                                                                  'NULL',  # gain = 0
                                                                  self.mesure_data[chan]['mesurement']['temperature_ccd'],
                                                                  o3,   #mesure
                                                                  uva,  #mesure
                                                                  uvb,  #mesure
                                                                  uve,  #mesure
                                                                  self.mesure_data[chan]['spectr'],
                                                                  correct,  # gain = 0
                                                                  # ==== Additional parameters ====
                                                                  self.mesure_data[chan]['mesurement']['datetime_local'],
                                                                  self.mesure_data[chan]['mesurement']['timezone'],
                                                                  self.pars['station']['sun_height_min'],
                                                                  self.mesure_data[chan]['mesurement']['accummulate'],
                                                                  'NULL',  # set_run
                                                                  self.mesure_data[chan]['id']['device'],  # dev_id1
                                                                  self.pars['station']['interval'],
                                                                  self.pars['device']['auto_exposition'],  # repeat1
                                                                  self.pars['device']['amplitude_max'],
                                                                  self.mesure_data[chan]['mesurement']['latitude'],
                                                                  self.mesure_data[chan]['mesurement']['longitude'],
                                                                  pars2send,    #pix2nm1
                                                                  'NULL',       #kz1,
                                                                  'NULL',       #kz_obl1,
                                                                  'NULL',       #omega1,
                                                                  'NULL',
                                                                  points2send,
                                                                  'NULL',       #pixels1,
                                                                  'NULL',
                                                                  'NULL')
##                    print(data4send)
                
                # Write file for next sending
                self.write_file4send(chan,data4send)
                    
        except Exception as err:
            print(err,sys.exc_info()[-1].tb_lineno)

    def ftp_send(self,host,port,remote_dir,user,password,file2send):
        file_name = os.path.basename(file2send)
        path = file2send.split(file_name)[0][:-1]
        ftp = FTP()
    ##    print('Подключение к FTP...',end=' ')
        try:
            ftp.connect(host=host, port=port)
            ftp.login(user=user, passwd=password)
    ##        print('OK')
            try:
                dir_list = []
                ftp.cwd(remote_dir)
    ##            ftp.debug(1)
                create_dirs(ftp,file2send)
                ftp.storlines('STOR ' + file_name, open(file2send,'rb'))
                tex = 'OK'
            except Exception as err2:
                tex = err2
            finally:
                ftp.close()
        except:
            tex = 'Ошибка подключения FTP!'
        return(tex)
            
    def sock_send(self,host,port,data2send,buffer = 2048):
        try:
            t = 'ERR'
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.send(data2send.encode(encoding = 'utf-8'))
            sock.close()
            t = 'OK'
        except Exception as err:
            print('procedures.sock_send(): {} - line {}'.format(err,sys.exc_info()[2].tb_lineno))
            t = 'ERR'
        finally:
            return(t)

    def send_file(self,file2send):
        try:
            tex = {}
            for send_type in ['socket','ftp']:
                if self.connect_pars[send_type + '_ip']!='0':
                    tex[send_type] = ''
                    if send_type=='socket':
                        with open(file2send) as f:
                            data2send = ''.join(f.readlines())
                            tex[send_type] = self.sock_send(self.connect_pars['socket_ip'],
                                                int(self.connect_pars['socket_port']),
                                                data2send)
                    elif send_type=='ftp':
                        tex[send_type] = self.ftp_send(self.connect_pars['ftp_ip'],
                                       int(self.connect_pars['ftp_port']),
                                       self.connect_pars['ftp_path'],
                                       self.connect_pars['ftp_user'],
                                       self.connect_pars['ftp_pass'],
                                       file2send)
                    if tex[send_type]=='OK':
                        print('{} Отправлен {} (dev: {})'.format(file2send,send_type,self.text['id']['device']))
                    else:
                        print(tex[send_type])
                    
        except Exception as err:
            print('procedures.send_file(): {} - line {}'.format(err,sys.exc_info()[2].tb_lineno))
        finally:
            return(tex)

    def mesure(self):
        """Определение номера последнего измерения"""
        try:
            files = os.listdir(self.path)
            if files:
                self.mesure_count = max(set([int(i.split('_')[1]) for i in files if i.count('_')==3]))
            else:
                self.mesure_count = 1
        except:
            pass
        try:
            k = {'Z':0,'S':0}
            if self.pars['device']['auto_exposition']==1:
                self.mesure_count += 1
                """ Z or S mesurement """
                for chan in self.pars['device']['channel']:
                    self.expo = self.pars['device']['auto_expo_min']
                    self.ZSspectr = [0]
                    self.tries = 0
                    self.change_channel(chan)
                    if self.tries > 0:
                        raise TypeError
                    else:
                        print()
                    while self.expo<self.pars['device']['auto_expo_max'] and max(self.ZSspectr)<self.pars['device']['amplitude_max']:
                        
                        try:
                            text = 'Канал {}. Эксп = {}'.format(self.pars['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),self.expo)
                            print(text,end='')
                            self.ZSspectr, self.t1, self.t2, text2, self.tries = Ufos_data(self.expo,self.pars['device']['accummulate'],chan,'S').device_ask(self.tries)
                            text += ' ' + text2
                            print('\r{}'.format(text))
                            logger.info(text)
                            if max(self.ZSspectr)>self.pars['device']['amplitude_min']:
                                break
    ##                        print()
                            k[chan] = max(self.ZSspectr) / self.pars['device']['amplitude_max']
                            if k[chan]!=0:
                                self.expo = int(self.expo / k[chan])
                            
                        except Exception as err:
                            print('mesure:',end='')
                            print(err,sys.exc_info()[-1].tb_lineno)
                            logger.error(str(err))
                            break
                                               
                    else:
                        self.expo = self.pars['device']['auto_expo_max']
                        text = 'Канал {}. Эксп = {}'.format(self.pars['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),self.expo)
                        print(text)
                        self.ZSspectr, self.t1, self.t2, text2, self.tries = Ufos_data(self.expo,self.pars['device']['accummulate'],chan,'S').device_ask(self.tries)
                        text += ' ' + text2
                        print('\r{}'.format(text),end=' ')
                        logger.info(text)
                    self.chan = chan
                    self.analyze_spectr(self.ZSspectr)
                    self.write_file()
                    
                    """ D mesurement """
                    self.chan = 'D' + chan.lower()
                    self.change_channel('D')
                    text = 'Канал {}. Эксп = {}'.format(self.pars['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),self.expo)
                    print(text)
                    self.Dspectr, self.t1, self.t2, text2, self.tries = Ufos_data(self.expo,self.pars['device']['accummulate'],'D','S').device_ask(self.tries)
                    text += ' ' + text2
                    print('\r{}'.format(text),end=' ')
                    logger.info(text)
                    self.analyze_spectr(self.Dspectr)
                    self.write_file()
            
                    """ Z-D or S-D calculation """
                    self.chan = chan+'D'
                    text = 'Расчёт спектра {}.'.format(self.chan)
                    print(text,end=' ')
                    logger.info(text)
                    self.ZDspectr = np.array(self.ZSspectr) - np.array(self.Dspectr)
                    self.analyze_spectr(self.ZDspectr)
                    self.write_file()
                    self.mesure_data[self.chan] = self.text

            else:
                for expo in self.pars['device']['manual_expo']:
                    self.expo = expo
                    self.mesure_count += 1
                    for chan in self.pars['device']['channel']:
                        """ Z or S mesurement """
                        self.change_channel(chan)
                        text ='Канал {}. Эксп = {}'.format(self.pars['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),self.expo)
                        print(text)
                        self.ZSspectr, self.t1, self.t2, text2, self.tries = Ufos_data(self.expo,self.pars['device']['accummulate'],
                                                   chan,
                                                   'S').device_ask(self.tries)
                        text += ' ' + text2
                        print('\r{}'.format(text),end=' ')
                        logger.info(text)
                        self.chan = chan
                        self.analyze_spectr(self.ZSspectr)
                        self.write_file()
                        
                        """ D mesurement """
                        self.chan = 'D' + chan.lower()
                        self.change_channel('D')
                        text = 'Канал {}. Эксп = {}'.format(self.pars['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),self.expo)
                        print(text)
                        self.Dspectr, self.t1, self.t2, text2, self.tries = Ufos_data(self.expo,self.pars['device']['accummulate'],'D','S').device_ask(self.tries)
                        text += ' ' + text2
                        print('\r{}'.format(text),end=' ')
                        logger.info(text)
                        self.analyze_spectr(self.Dspectr)
                        self.write_file()

                        """ Z-D or S-D calculation """
                        self.chan = chan+'D'
                        text = 'Расчёт спектра {}.'.format(self.chan)
                        print(text,end=' ')
                        logger.info(text)
                        self.ZDspectr = np.array(self.ZSspectr) - np.array(self.Dspectr)
                        self.analyze_spectr(self.ZDspectr)
                        self.write_file()
                        self.mesure_data[self.chan] = self.text
        except TypeError:
##            print("No data from UFOS")
            pass
        except Exception as err:
            print("procedures.Main.mesure:", end='')
            print(err,sys.exc_info()[-1].tb_lineno)

class check_sun_and_mesure():
    def __init__(self):
        self.home = os.getcwd()
        
    def start(self):
        while 1:
            try:
                
                ufos_com = UfosConnection().get_com()['com_obj']
                self.pars = settings.get(self.home)
                
                self.time_now_1 = datetime.datetime.now()
                self.mu, self.amas, self.sunheight = sunheight(self.pars["station"]["latitude"],
                                                               self.pars["station"]["longitude"],
                                                               self.time_now_1,
                                                               self.pars["station"]["timezone"])
                main = Main(self.pars)
                if self.sunheight >= self.pars["station"]["sun_height_min"]:
                    
                    main.nms2pixs()
                    print('=== Запуск измерения ===                      ', end='\r')
                    main.mesure()
                    
                    if main.tries > 0:
                        print('Кабель подключен к ПК, но не подключен к УФОС!', end='\r')
                        time.sleep(10)
                    else:
                        calculate_final_files(self.pars, main.last_file_o3, 'ZD')
                        main.make_line()
                        print('========================')
                        next_time = self.time_now_1 + datetime.timedelta(minutes=self.pars["station"]["interval"])
                        self.mu, self.amas, self.sunheight = sunheight(self.pars["station"]["latitude"],
                                                                       self.pars["station"]["longitude"],
                                                                       next_time,
                                                                       self.pars["station"]["timezone"])
                    
                        print('Следующее измерение: {}'.format(str(next_time).split('.')[0]))

                        # Send files
                        for file2send in os.listdir(main.path_sending):
                            if datetime.datetime.now() < next_time:
                                sending_file = os.path.join(main.path_sending, file2send)
                                tex = main.send_file(sending_file)
                                logger.debug(str(tex))
                                for prot in tex.keys():
                                    if tex[prot] == 'OK':
                                        os.remove(sending_file)
                        while datetime.datetime.now() < next_time:
                            time.sleep(1)
                else:
                    calculate_final_files(self.pars, main.last_file_o3,'ZD')
                    print('\rСледующее измерение: {}'.format(get_time_next_start(self.pars["station"]["latitude"],
                                                                                 self.pars["station"]["longitude"],
                                                                                 self.pars["station"]["timezone"],
                                                                                 self.pars["station"]["sun_height_min"])),
                          end='')
                    time.sleep(5)
            except serial.serialutil.SerialException as err:
                print(err)
            except TypeError:
                time.sleep(10)
            except Exception as err:
                print(err, sys.exc_info()[-1].tb_lineno)
                time.sleep(10)