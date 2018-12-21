# from math import *
import os
import datetime
import socket
import numpy as np
import sys
from ftplib import FTP
# import pylab
# import matplotlib.dates


def calc(x, abc, num):
    i = len(abc)
    ans = 0
    while i > 0:
        ans += float(abc[-i]) * x ** (i - 1)
        i -= 1
    #   ans = float(abc[0])*x**2 + float(abc[1])*x + float(abc[2])
    return (round(ans, num))


def find_closest_pair(x, mas, mas_o3, mas_34):
    """R12,mas_r12,mas_o3,mas_r34"""
    ind = []
    for i in mas:
        ind.append(abs(float(x) - float(i)))

    bo = ind.index(min(ind))
    ind.pop(bo)
    bot_r = mas.pop(bo)
    bot_o3 = mas_o3.pop(bo)
    #    bot_r_34 = mas_34.pop(bo)
    bot_r_34 = 1
    to = ind.index(min(ind))
    ind.pop()
    top_r = mas.pop(to)
    top_o3 = mas_o3.pop(to)
    #    top_r_34 = mas_34.pop(to)
    top_r_34 = max(mas_34)

    return (bot_r, top_r, bot_o3, top_o3, bot_r_34, top_r_34)


def eva_r34b(ini, mu):
    abc = ini.split('/')
    mu = float(mu)
    return (eval(abc[0]) * mu ** 2 +
            eval(abc[1]) * mu +
            eval(abc[2])
            )


def o2nomo(mu, R12, R34, nomo_s, ini_s):
    # not use
    cn_all = []
    digs = 2

    for i in nomo_s:
        cn = {}
        c = 4
        cn[i[0]] = int(i[1])  # ozone
        cn[i[2]] = i[3]  # date
        cn[i[c]] = i[c + 1:c + digs + 2]  # >5 [5:8]
        c += digs + 2  # c = 8
        ##        print(c)
        cn[i[c]] = i[c + 1:c + digs + 2]  # 5>3 [9:12]
        c += digs + 2  # c = 12
        ##        print(c)
        cn[i[c]] = i[c + 1:c + digs + 2]  # 3> [13:16]
        c += digs + 2  # c = 16
        ##        print(c)
        cn[i[c]] = i[c + 1:c + digs + 2]  # >5 34 [17:20]
        c += digs + 2  # c = 20
        ##        print(c)
        cn[i[c]] = i[c + 1:c + digs + 2]  # 5>3 34 [21:24]
        c += digs + 2  # c = 24
        ##        print(c)
        cn[i[c]] = i[c + 1:c + digs + 2]  # 3> 34 [25:28]
        cn_all.append(cn)
    ##        print(cn)
    mas_r12 = []
    mas_r34 = []
    mas_o3 = []
    R34b = eva_r34b(ini_s['kdX'], mu)
    for cn in cn_all:
        if mu >= 5:
            r12 = calc(mu, cn['mu>5'], 6)
            r34 = calc(mu, cn['mu34>5'], 6)
        elif 5 > mu > 3:
            r12 = calc(mu, cn['5>mu>3'], 6)
            r34 = calc(mu, cn['5>mu34>3'], 6)
        elif 3 >= mu:
            r12 = calc(mu, cn['3>mu'], 6)
            r34 = calc(mu, cn['3>mu34'], 6)
        mas_r12.append(r12)
        mas_r34.append(r34)
        mas_o3.append(cn['ozone'])
    r12_1, r12_2, o1, o2, r34_1, r34_2 = find_closest_pair(R12, mas_r12, mas_o3, mas_r34)

    x = r34_2 / R34
    R12 = R12 * (1.08675 * x - 0.12480)
    x = ((r12_2 * o1 - r12_1 * o2) + (o2 - o1) * R12) / (r12_2 - r12_1)

    x = x / 1000  # - Robl
    o3 = round(round(x, 3) * 1000)
    ##    print('{}\t{}\t{}\t{}\t{}'.format(mu,o3,R12,R34,r34_2))
    return (o3)


def read_nomo(path):
    with open(os.path.join(path, 'Calibration', 'nomogramma.txt'), 'r') as f:
        data = f.readlines()
    nomo = []
    for i in data:
        for j in ['[', ']', ' ']:
            i = i.replace(j, '')
        i = i.replace(',', '\t').strip().split('\t')
        nomo.append(i)
    ##    print(nomo)
    return (nomo)


def make_kz_coeff(x, y, deg):
    """
    x - массив данных оси x
    y - массив данных оси y
    deg - степень полинома
    Количество возвращаемых коэффициентов = deg + 1
    """
    x_arr = np.array(x)
    y_arr = np.array(y)
    a = np.polyfit(x_arr, y_arr, deg)
    return (a.tolist())


class set_last_date():
    """If file not sent, it's name will be written to the 'outbox' file"""

    def write(home, date):
        file = os.path.join(home, 'outbox.txt')
        with open(file, 'w') as f:
            date = datetime.datetime.strftime(date,
                                              '%Y-%m-%d %H:%M:%S.0000000')  # date to '1900-12-12 13:14:15.0000000'
            print(date, file=f, end='')

    def read(home):
        file = os.path.join(home, 'outbox.txt')
        with open(file, 'r') as f:
            date = f.readline()
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.0000000')  # '1900-12-12 13:14:15.0000000' to date
        return (date)


def set_flag(flag):
    """Дополнительное измерение если flag == 1"""
    with open('manual_start', 'w') as f:
        try:
            f.write(str(flag))
        except:
            flag = 0
    return (flag)


def get_flag():
    with open('manual_start', 'r') as f:
        try:
            flag = int(f.readline())
        except:
            flag = 0
    return (flag)


def curr_time2():
    date_time = datetime.datetime.now()
    tcur = datetime.datetime.strftime(date_time, '%H:%M')
    return (tcur)


def curr_datetime2():
    date_time = datetime.datetime.now()
    date = datetime.datetime.strftime(date_time, '%d.%m.%Y')
    time = datetime.datetime.strftime(date_time, '%H:%M:%S')
    return (date, time)


def create_dirs(ftp, abspath):
    local_dirs = abspath.split('\\')[-4:-1]
    remote_dirs = ftp.nlst()
    for i in local_dirs:
        try:
            ftp.mkd(i)
        except:
            pass
        ftp.cwd(i)
    return (ftp)


def to_ftp(host, port, remote_dir, user, password, abspath):
    file_name = os.path.basename(abspath)
    path = abspath.split(file_name)[0][:-1]
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
            create_dirs(ftp, abspath)
            ftp.storlines('STOR ' + file_name, open(abspath, 'rb'))
            tex = 'OK'
        except Exception as err2:
            tex = err2
        finally:
            ftp.close()
    except:
        tex = 'Ошибка подключения FTP!'
    return (tex)


def sock_connect2(HOST, PORT, text, buffer=2048):
    data = text.encode(encoding='utf-8')
    t = 'NO'
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.send(data)
        sock.close()
        ##        print(data)
        t = 'OK'
    except Exception as err:
        t += '\nsock_connect2(): {0}'.format(err)
    return (t)


def send_files_ufos(home, file2send):
    return (send_files(home, file2send.replace('\n', '')))


def get_min_date(path):
    def get_min(path):
        min_dir = []
        dirs = os.listdir(path)
        for i in dirs:
            if os.path.isdir(os.path.join(path, i)) and i.isdigit():
                min_dir.append(i)
        return (min(y))

    year = get_min(path)
    month = get_min(os.path.join(path, year))
    day = get_min(os.path.join(path, year, month))
    return (year, month, day)


def get_datetime(home, path):
    """Получение даты и времени из файла измерений"""
    with open(path, 'r') as f:
        ##        y,m,d = get_min_date(home)
        data1 = []
        for i in range(2):
            data = f.readline()
            if data.count('time') > 0:
                # ;Measurement details: channel = Z-D, date = 02.07.2015, time = 00:02:07
                data = data.split(',')
                for i in data:
                    b = i.split(' ')[-1].replace('\n', '')
                    data1.append(b)
    # data1 = ['Z-D','01.01.1900','00:02:07']
    data = datetime.datetime.strptime('{0} {1}'.format(data1[1], data1[2]), '%d.%m.%Y %H:%M:%S')
    return (data)


def send_files(home, file2send):
    """home - where config.ini file located
    file2send - file for sending"""
    conf = read_connect(home)
    host = conf['socket_ip']
    port = int(conf['socket_port'])
    data4send = ''
    ftp_host = conf['ftp_ip']
    ftp_port = int(conf['ftp_port'])
    ftp_path = conf['ftp_path']
    ftp_user = conf['ftp_user']
    ftp_pass = conf['ftp_pass']
    tex = ''

    def take_ozone(par):
        if len(par) == 2:
            return (par[0])
        else:
            return (0)

    try:
        f = open(file2send, 'r')
        text = f.readlines()
        for i in text:
            if i == '\n':
                text.remove(i)
        for i in [' ', "'", "\\n", '[', ']']:
            text = str(text).replace(i, '')
        ds = text.split(',')
        ini_s = read_ini(home, 'r', '')
        dev_id = ini_s['dev_id']
        station_id = ini_s['stn_id']
        channel = ds[1].split('=')[1]
        date = str(ds[2].split('=')[1])
        year = date.split('.')[2]
        month = date.split('.')[1]
        day = date.split('.')[0]
        date = '{0}-{1}-{2}'.format(year, month, day)
        time = str(ds[3].split('=')[1])
        date_time = date + ' ' + time
        exp = ds[4].split('=')[1]
        gain = ds[5].split('=')[1]
        temp = ds[6].split('=')[1]
        accum = ds[7].split('=')[1]
        ozone = take_ozone(ds[11].split('ozone'))
        uva = take_ozone(ds[12].split('uva'))
        uvb = take_ozone(ds[13].split('uvb'))
        uve = take_ozone(ds[14].split('uve'))
        spect = str(ds[16:])
        for i in (' ', '[', ']', "'"):
            spect = spect.replace(i, '')
        pars = read_ini(home, 'r', '')
        expo1 = pars['expo']
        channel1 = pars['channel']
        accum1 = pars['accummulate']
        gain1 = pars['gain']
        set_run = pars['set_run']
        dev_id1 = pars['dev_id']
        time1 = pars['time']
        repeat1 = pars['repeat']
        max1 = pars['max']
        latitude1 = pars['latitude']
        longitude1 = pars['longitude']
        pix2nm1 = pars['pix2nm']
        kz1 = pars['kz']
        kz_obl1 = pars['kz_obl']
        omega1 = pars['omega']
        hs1 = pars['hs']
        points1 = pars['points']
        pixels1 = pars['pix+-']
        hour_pelt1 = pars['hour_pelt']
        auto_exp1 = pars['auto_exp']
        zenith_add1 = pars['zenith_add']
        ozone_add1 = pars['ozone_add']
        stn_id1 = pars['stn_id']
        R21_01 = pars['R21_0']
        R34_01 = pars['R34_0']
        kdX1 = pars['kdX']
        ##        expo1,channel1,accum1,gain1,set_run,dev_id1,time1,repeat1,max1,latitude1,longitude1,pix2nm1,kz1,kz_obl1,omega1,hs1,points1,pixels1,hour_pelt1,auto_exp1 = pars['expo'],pars['channel'],pars['accummulate'],pars['gain'],pars['set_run'],pars['dev_id'],pars['time'],pars['repeat'],pars['max'],pars['latitude'],pars['longitude'],pars['pix2nm'],pars['kz'],pars['kz_obl'],pars['omega'],pars['hs'],pars['points'],pars['pix+-'],pars['hour_pelt'],pars['auto_exp']
        data4send = """#{0};{1};{2};{3};{4};{5};\
{6};{7};{8};{9};{10};\
{11}@{12};{13};{14};{15};\
{16};{17};{18};{19};{20};\
{21};{22};{23};{24};{25};\
{26};{27};{28};{29};{30};{31}#""".format(dev_id,
                                         station_id,
                                         channel,
                                         date_time,
                                         exp,
                                         gain,
                                         temp,
                                         ozone,
                                         uva,
                                         uvb,
                                         uve,
                                         spect,
                                         expo1,
                                         channel1,
                                         accum1,
                                         gain1,
                                         set_run,
                                         dev_id1,
                                         time1,
                                         repeat1,
                                         max1,
                                         latitude1,
                                         longitude1,
                                         pix2nm1,
                                         kz1,
                                         kz_obl1,
                                         omega1,
                                         hs1,
                                         points1,
                                         pixels1,
                                         hour_pelt1,
                                         auto_exp1)
        # -----------socket-------------
        s_type = ''
        tex = ''
        if host != '0':
            tex = sock_connect2(host, port, data4send)
            if str(tex) == 'OK':
                date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
                set_last_date.write(home, date_time)
                s_type = '(socket)'
        # ------------ftp---------------
        s_type2 = ''
        tex_ftp = ''
        if ftp_host != '0':
            tex_ftp = to_ftp(ftp_host, ftp_port, ftp_path, ftp_user, ftp_pass, file2send)
            if str(tex_ftp) == 'OK':
                date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
                set_last_date.write(home, date_time)
                s_type2 = '(ftp)'
        # ------------------------------
        print('{0} Отправлен {1}{2} (dev: {3})'.format(file2send.replace('\n', ''), s_type, s_type2, dev_id))
        if tex in ['OK', ''] and tex_ftp in ['OK', '']:
            return ('OK')
        else:
            return (tex + '\n' + tex_ftp)
    except Exception as err:
        print('Shared.send_files(): {} - line {}'.format(err, sys.exc_info()[2].tb_lineno))
        return (False)


def time_code(start):
    """
    'start' - начать отсчет
    'stop' - остановить отсчет и вывести результат
    """
    if start == 'start':
        time_code.ct_start = float(str(datetime.datetime.now())[17:23])
    elif start == 'stop':
        time_code.ct_next = float(str(datetime.datetime.now())[17:23])
        time_code.ct = time_code.ct_next - time_code.ct_start
        time_code.ct_start = time_code.ct_next
        print(time_code.ct)


def pix2nm(abc, pix, digs, add):
    """
    Обработка одного пикселя
    abc - массив коэффициентов полинома
    pix - номер пиксела
    dig - количество знаков после запятой
    add - сдвиг для зенитных измерений
    """
    try:
        return round(eval(abc[0]) * pix ** 2 + eval(abc[1]) * pix + eval(abc[2]) + add, digs)
    except:
        return 0


def kz_obl_f(mu, b, pmas2):
    def eva(abc, x):
        return (eval(abc[0]) * float(x) ** 2 + eval(abc[1]) * float(x) + eval(abc[2]))

    """
    b - массив коэффициентов полинома
    amas - солнечная масса
    pmas2 - значения в точках 332 и 352
    """
    if b == 0 or pmas2 == 0 or pmas2[0] <= 0 or pmas2[1] <= 0:
        return (1)
    abc = [b[0], b[1], b[2]]
    kz_obl_1 = eva(abc, mu)
    try:
        if kz_obl_f.value == 1:
            return (kz_obl)
        elif kz_obl_f.value == 0:
            return (0)
    except:
        return (kz_obl)


def omega(abc, pix, digs):
    """pixel to omega"""
    """
    abc - массив коэффициентов полинома
    pix - номер пиксела
    dig - количество знаков после запятой
    """

    if len(pix) > 1:
        mas = []
        for i in pix:
            mas.append(round(eval(abc[0]) * int(i) ** 2 + eval(abc[1]) * int(i) + eval(abc[2]), digs))
        ##        print('mas',abc)
        return mas
    else:
        return round(eval(abc[0]) * int(pix) ** 2 + eval(abc[1]) * int(pix) + eval(abc[2]), digs)


def sredne(I, o3_mode, digs):
    """Среднее арифметическое"""
    k = 0
    i = 0
    try:
        leng = len(I)
        if o3_mode != 'ozone':
            while i < leng:
                k += int(I[i])
                i += 1
        else:
            while i < leng:
                if I[i] != '':
                    k += int(I[i])
                    i += 1
        k = k / leng
    except Exception as err:
        print('shared.sredne: ', err)
        try:
            k = int(I)
        except:
            k = 1
    return (round(k, digs))


def srznach(a, o3_mode):
    """
    Среднее арифметическое
    a - массив значений, который нужно осреднить
    o3_mode=='ozone' - для расчёта дневного озона
    o3_mode==0 - для обычного расчёта среднего арифметического
    """
    b = 0
    leng = len(a)
    for i in a:
        if o3_mode == 'ozone':
            if i != '' and 500 > i > 250:
                b += int(i)
            else:
                leng -= 1
        else:
            if i != '':
                b += int(i)
    try:
        return (round(b / leng))
    except Exception as err:
        print('shared.srznach: ', err)
        return (0)


def read_ini(path, mode, par):
    if mode == 'w':
        p = par
    else:
        # Резервные данные
        p = ['300', 'ZS', '3', '0', 'S',
             '1', '00:00-23:59-10', '1', '3200', '59.57',
             '-30.42', '9.6*10**-8/0.039196277/270.314812842', '0.00005/-0.00152/0.01764/-0.1024/0.29792',
             '-1.90657/2.89708', '0/0/1',
             '5', '317,340,340,359.5,393.37,396.78', '5', '+3', '1',
             '-1.2', '0', '042', '0/-0.00441/0.09348/0.46213/1.08544', '0/-0.00027/0.00731/-0.07772/1.14555',
             '0.04227/-0.01490/-0.66512/0.23933/1.08258/0.60007']
    """Чтение файла параметров"""
    allinfo = []
    settings = {}
    tmp = 0
    try:
        name = r'settings.ini'
        for i in os.listdir(path):
            if i == name:
                tmp = 1
                break
        if tmp and mode == 'r':
            file_n = open(os.path.join(path, name), 'r')
        else:
            file_n = open(os.path.join(path, name), 'w')
            print(""";0 Экспозиция
expo={0}
;1 Порядок и тип каналов
channel={1}
;2 Суммирование
accummulate={2}
;3 Усиление
gain={3}
;4 Запуск
set_run={4}
;5 Номер устройства
dev_id={5}
;6 Время
time={6}
;7 Повтор
repeat={7}
;8 Максимальное значение линейки
max={8}
;9 Широта
latitude={9}
;10 Долгота
longitude={10}
;11 Коэффициенты полинома пиксель-длина_волны
pix2nm={11}
;12 Kz - 0.1717/0.5429/1/1/1/1
kz={12}
;13 Kz обл - dx(f(month)-lg(330/350)) = a/b/c/a1/b1/c1 = 0/311.21/6.097/0/-0.0216/0.088
kz_obl={13}
;14 Коэффициенты полинома пиксель-чувствительность линейки 5*10**-7/-0.0004/0.0663
omega={14}
;15 Высота солнца в градусах. Измерения будут проводиться при высоте солнца больше hs
hs={15}
;16 Дополнительные линии на графике
points={16}
;17 Промежуток от каждой точки, в котором берётся среднее значение
pix+-={17}
;18 Часовой пояс
hour_pelt={18}
;19 Автоматический поиск экспозиции
auto_exp={19}
;20 Сдвиг коэффициентов пиксель-длина_волны между каналами
zenith_add={20}
;21 Прибавка к озону в ед. добсона
ozone_add={21}
;22 Номер станции в формате ВМО (3 символа)
stn_id={22}
;23 Отношение I2 к I1 ясного дня (-0.00441*mu**3 + 0.09348*mu**2 + 0.46213*mu + 1.08544)
R21_0={23}
;24 Отношение I3 к I4 ясного дня (-0.00027*mu**3 + 0.00731*mu**2 - 0.07772*mu + 1.14555)
R34_0={24}
;25 Прибавка к озону от его величины (kdX = (0.04227 * x - 0.01490)*mu**2 + (-0.66512 * x + 0.23933)*mu + (1.08258 * x + 0.60007))
kdX={25}
;26 uva_koef
uva_koef={26}
;27 uvb_koef
uvb_koef={27}
;28 uve_koef
uve_koef={28}""".format(p['expo'],
                        p['channel'],
                        p['accummulate'],
                        p['gain'],
                        p['set_run'],
                        p['dev_id'],
                        p['time'],
                        p['repeat'],
                        p['max'],
                        p['latitude'],
                        p['longitude'], p['pix2nm'],
                        p['kz'],
                        p['kz_obl'],
                        p['omega'],
                        p['hs'],
                        p['points'],
                        p['pix+-'],
                        p['hour_pelt'],
                        p['auto_exp'],
                        p['zenith_add'],
                        p['ozone_add'],
                        p['stn_id'],
                        p['R21_0'],
                        p['R34_0'],
                        p['kdX'],
                        p['uva_koef'],
                        p['uvb_koef'],
                        p['uve_koef']), file=file_n)
            file_n.close()
            file_n = open(os.path.join(path, name), 'r')
        while True:
            tmp = file_n.readline()
            if tmp != '':
                if tmp[0] == ';' or tmp[0] == ' ' or tmp == '\n':
                    pass
                else:
                    allinfo.append([tmp.split('=')[0], tmp.split('=')[1].split('\n')[0]])
            else:
                break
        file_n.close()
        for name, value in allinfo:
            settings[name] = value
        #            print(name,value)
        #        t[0] expo = 100
        #        t[1] chan = 'ZS'
        #        t[2] accum = 1
        #        t[3] gain = 0
        #        t[4] run = 'S'
        #        t[5] dev_id = 1
        #        t[6] time =
        #        t[7] repeat = 1
        #        t[8] pmax = 2400
        #        t[9] latitude = 50.50
        #        t[10] longitude = -50.50
        #        t[11] pix2nm = -2*10**-8/0.0403/278.2
        #        t[12] kz = 1/1/1/1/1/1
        #        t[13] kz_obl = 1/1/1/1/1/1
        #        t[14] omega = 0/0/1
        #        t[15] hs = 7
        #        t[16] points = 735,814,968,1187,1275,1286,1783
        #        t[17] pix+- = 5
        #        t[18] hour_pelt = +4
        #        t[19] auto_exp = 1
        #        t[20] zenith_add = 1
        #        t[21] ozone_add=0
        #        t[22] stn_id=042
        #        t[23] R21_0=0/-0.00441/0.09348/0.46213/1.08544
        #        t[24] R34_0=0/-0.00027/0.00731/-0.07772/1.14555
        #        t[25] kdX=0.04227/-0.01490/-0.66512/0.23933/1.08258/0.60007
        return settings
    except:
        return None


def read_path(home, path, mode):
    """Чтение файла last_path"""
    last_path = os.path.join(home, 'last_path.txt')
    if mode == 'r' and os.path.exists(last_path):
        with open(last_path, 'r') as file_n:
            return file_n.readline()
    else:
        with open(last_path, 'w') as file_n:
            file_n.write(path)
    return path


if __name__ == '__main__':
    #    home = os.getcwd()
    #    file2send = 'D:\\UFOS\\Мурманск\\2015\\07\\09\\m0003.Z-D_1100_09072015.txt'
    #    send_files(home,file2send)
    #    conf = read_connect(home)
    #    tex = to_ftp(conf['ftp_ip'],int(conf['ftp_port']),conf['ftp_path'],conf['ftp_user'],conf['ftp_pass'],'D:\\UFOS\\Мурманск\\2015\\07\\09\\m0003.Z-D_1100_09072015.txt')
    #    input(tex)
    pass
#    while 1:
#        time = input('Time: ')
#        if len(time)==4:
#            time = '0' + time
#        time += '.00'
#        date = input('Date: ')
#        if date == '':
#            date = '14.08.2012'
#        f = 59.57
#        l = -30.42
#        pelt = '+4'
#        try:
#            mu,ama,h = sunheight(f,l,time,pelt,date)
#            print(round(mu,3),round(ama,3),round(h,3))
#        except:
#            break
