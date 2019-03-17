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
