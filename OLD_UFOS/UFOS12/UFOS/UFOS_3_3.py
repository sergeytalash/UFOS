import serial,time,datetime,winreg,os,winsound,sys
##import threading
from winreg import *
from Shared_ import *

expo_grad = 1100 #Экспозиция градуировки


def send_all_files_UFOS(home,date):
##    global main.next_start
    """Отправка всех неотправленных файлов"""
    # date = '1900-12-12 13:14:15.0000000' to date
    y = datetime.datetime.strftime(date,'%Y')
    m = datetime.datetime.strftime(date,'%m')
    d = datetime.datetime.strftime(date,'%d')
    count = 0
    flag = True
    path = os.path.join(home,'ZEN',y,m,d)
    next_st = datetime.datetime.strptime(main.next_start,'%Y-%m-%d %H:%M')
    while flag and next_st>datetime.datetime.now():
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.count('-D')>0:
                    file2send = os.path.join(path,file)
##                    print(file2send)
                    file_time = get_datetime(home,file2send)
##                    print(file_time,date)
                    if file_time>date:
                        tex = send_files(home,file2send) # отправка файла
                        if tex!='OK':
                            print(tex)
                            return(count)
                        count += 1
        new_date = datetime.datetime.strptime('{0}-{1}-{2}'.format(y,m,d),'%Y-%m-%d') + datetime.timedelta(days=1)
        if new_date<datetime.datetime.now():
            y = datetime.datetime.strftime(new_date,'%Y')
            m = datetime.datetime.strftime(new_date,'%m')
            d = datetime.datetime.strftime(new_date,'%d')
        else:
            break
        path = os.path.join(home,'ZEN',y,m,d)
    return(count)

    
def com_check_all():
    """Проверка COM портов последовательным перебором"""
    ports_COM = []
    ser = None
    i = 0                   
    ports_COM = []
    """Настройки COM портов"""
    br = 115200                       #Baudrate
    bs = 8                            #Byte size
    par = 'N'                         #Parity
    sb = 1                            #Stop bits
    to = 5                            #Time out (s)
    try:
        Key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM")
    except WindowsError:
        print("Драйвер УФОС не установлен!")
        
    while i<256:
        try:
            name, value, typ = winreg.EnumValue(Key, i)
            if name.count('Silab')>0:
                ser = serial.Serial(port = '//./' + value, baudrate = br, bytesize = bs, parity = par, stopbits = sb, timeout = to)
                lib = {}
                lib['com'] = value
                lib['ser'] = ser
                ports_COM.append(lib)
        except:
            pass
        if ser:
           ser.close()
        i += 1
    if ports_COM==[]:
        ports_COM = None
    return(ports_COM)

def get_com(count):
    """Получение номера COM порта"""
    if count == -1:
        j = 0
        for i in main.ports_COM:
            j = max(int(i['com'][-1:]), j)
        return(j)
    else:
        return(main.ports_COM[count]['com'][-1:])
    
def get_ser(count):
    """Получение самого COM порта"""
    if count == -1:
        return main.ports_COM[len(main.ports_COM)-1]['ser']
    else:
        return main.ports_COM[count]['ser']

def settings2send(header, dev_id, expo, gain, accum, cooler, mesure_type, start_mesure):
    """Преобразование данных запроса в необходимый тип для отправки в прибор"""
    parameters = []
    parameters.append(header)
    parameters.append(bytes((int(dev_id) // 256, int(dev_id) % 256)))
    parameters.append(bytes((int(expo) % 256, int(expo) // 256)))
    parameters.append(bytes((int(gain),)))
    parameters.append(bytes((int(accum),)))
    parameters.append(cooler)
    parameters.append(mesure_type)
    parameters.append(start_mesure)
    i = 1
    crc = ord(parameters[0])
    while i<len(parameters):
        crc = (crc * 2 + (crc // 256 & 1)) & 0xff
        crc ^= i + 1
        i+=1
    parameters.append(bytes((crc,)))
    data_send = b''
    for byte in parameters:
        data_send += byte
    return(data_send)

def device_ask(ser, data_send, k):
    """Отправление данных в прибор"""
    if ser:
        try:
            if data_send:
                ser.open()
                cha = chr(data_send[8])
                if cha=='Z':
                    cha_name = 'Зенитный'
                elif cha=='S':
                    cha_name = 'Суммарный'
                elif cha=='D':
                    cha_name = 'Темновой'
                if chr(data_send[9])=='S':
                    # Режим измерений
                    if cha == 'D':
                        print(function.count,'{0} канал.'.format(cha_name))
                    else:
                        print(function.count,'{0} канал.'.format(cha_name),end=' ')
                    ser.write(data_send)
                    timee = int(run.accum) * int(run.expo) / 1000 * float(k)
                    time.sleep(round(timee))
                    t = device_answer(ser,7395)      # Чтение 7395 байт данных с COM порта
                else:
                    # Режим переключения каналов без измерений
                    ser.write(data_send)
                    time.sleep(2)
                    t = device_answer(ser,13)        # Чтение 13 байт данных с COM порта
                if t:
                    return(t)
                else:
                    return(False)
        except:
            print('***** Кабель не подключен к ПК *****')
            
def device_answer(ser,num):
    """Получение данных с прибора"""
    data_out = b''
    data_tmp = b''
    try:
        i = 0
        if num != 13:
            time.sleep(2)
            while i<16:
                byte = ser.read(493)
                data_tmp += byte
                i += 1
        else:
            data_tmp = ser.read(13)
            i = data_tmp[6:10]
##            print('t1(Линейка) = ',(i[0] * 255 + i[1]) / 10)
##            print('t2(Полихроматор) = ',(i[2] * 255 + i[3]) / 10)
            run.temper1 = (i[0] * 255 + i[1]) / 10 #Линейка
            run.temper2 = (i[2] * 255 + i[3]) / 10 #Полихроматор
        ser.close()
        if len(data_tmp)>14:
            data_out = data_tmp
        else:
            data_out = 'N'
        return data_out
    except:
        print('***** Кабель не подключен к УФОС *****')
        ser.close()
        return(False)

def answer_decode(data_out, exposure, chan, accum, k, ini_s):
    """Расшифровка данных, полученных с прибора и запись в файл"""
    def try_join_path(path1,path2):
        try:
            new_path = os.path.join(path1,path2)
            os.mkdir(new_path)
        except:
            pass
        return(new_path)
    
    home = main.home
    data = []
    d = data_out
    if d:
        if k == 1 or chan == 'D':
            try:
                curr_date, curr_time = curr_datetime2()
                mu, amas, hs = sunheight(ini_s['latitude'],ini_s['longitude'],curr_time,ini_s['hour_pelt'],curr_date)
                date_mas = curr_date.split('.')
                date_filename = date_mas[0] + date_mas[1] + date_mas[2]
                tmp_path = os.getcwd()
                sens_tmp_path = try_join_path(tmp_path,'SDI')
                zen_tmp_path = try_join_path(tmp_path,'ZEN')
                #zen_tmp_path
                zen_tmp_path = try_join_path(zen_tmp_path,date_mas[2])
                zen_tmp_path = try_join_path(zen_tmp_path,date_mas[1])
                zen_tmp_path = try_join_path(zen_tmp_path,date_mas[0])
                #sens_tmp_path
                sens_tmp_path = try_join_path(sens_tmp_path,date_mas[2])
                sens_tmp_path = try_join_path(sens_tmp_path,date_mas[1])
                sens_tmp_path = try_join_path(sens_tmp_path,date_mas[0])
                dir1 = os.listdir(zen_tmp_path)
                if dir1!=[]:
                    i = 1
                    ii = ''
                    for j in dir1:
                        tmp = j.split('.')[0][1:]
                        while True:
                            try:
                                if int(tmp)==i:
                                    i += 1
                                else:
                                    break
                            except:
                                break
                        if len(str(i))<4:
                            ii = '0'*(4-len(str(i))) + str(i)
                        else:
                            ii = str(i)
                else:
                    ii='0001'
                name = r'm{0}.{1}_{2}_{3}.txt'.format(ii,chan,exposure,date_filename)
                file_o = open(os.path.join(zen_tmp_path,name),'w')
                file_data = """;UFOS3
;Measurement details: channel = {0}, date = {1}, time = {2}
Exposure={3}
Gain={4}
Temperature={5}
Accummulate={6}
{7} mu
{8} amas
{9} hs
""".format(chan,
           curr_date,
           curr_time,
           exposure,
           function.gain,
           run.temper1,
           accum,
           round(float(mu),3),
           round(float(amas),3),
           round(float(hs),3)
           )
                i = len(d) - 1
                spectr1 = []
                while i>12:
                    i -= 1
                    spectr1.append(int(d[i+1]) * 255 + int(d[i]))
                    i -= 1
                mu_amas_hs = 0
                try:
                    ome = read_sensitivity(home)
                    dt = ozone_uv(main.home,ome,spectr1,curr_date,curr_time,name,expo_grad,chan)
##                    print((dt['o3'],dt['uva'],dt['uvb'],dt['uve']))
                    if dt['ome']:
                        file_data += """{0} ozone
{1} uva
{2} uvb
{3} uve
""".format(dt['o3'],round(int(dt['uva'])),round(int(dt['uvb'])),round(int(dt['uve'])))
                except Exception as err:
                    print('UFOS.ozone_uv',err)
                    pass
                file_data += '[Value]\n'
                #Создание спектра с учётом чувствительности
                if chan=='S-D': 
                    sens_spectr = []
                    spectr_i = 0
                    while spectr_i<len(spectr1):
                        try:
                            #Измеренный_спектр * чувствительность_УФОС * экспозиция_градуировки / экспозиция_измерения
                            #                           Нужно ли это?  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                            sens_spectr.append(int(spectr1[spectr_i]) * float(ome[spectr_i]) * expo_grad / int(name.split('_')[1]))
                        except:
                            sens_spectr.append(0)
                        spectr_i += 1
                    sens_data = file_data
                    for i in sens_spectr:
                        sens_data += str(i) + '\n'
                    with open(os.path.join(sens_tmp_path,name),'w') as sens_file_o:
                        print(sens_data, file = sens_file_o)
                    
                #Изменение первых 100 пикселей, чтобы обозначить, что был снят дополнительный спектр
                if main.flag==1 and len(chan)>2 and main.waiting==1: 
                    spectr1 = [50]*100+spectr1[100:]
                
                for i in spectr1:
                    file_data += str(i) + '\n'
##                    print(i, file = file_o)
                
                print(file_data, file = file_o)
                file_o.close()
                print('  Сохранено', name)
                
##                path_name = os.path.join(tmp_path,name)
##                if not os.path.exists(os.path.join(main.home,'outbox.txt')):
##                    f = open(os.path.join(main.home,'outbox.txt'),'w')
####                    print(1)
##                    yy,mm,dd = get_min_date(main.home)
####                    print(2)
##                    print('{0}-{1}-{2} 00:00:00.0000000'.format(yy,mm,dd),file=f,end='')
##                    f.close()
##                last_sent_file = set_last_date.read(main.home) # '1900-12-12 13:14:15.0000000' to date
##                print(3)
                if len(chan)>2:
##                    try:
##                        count_sent = send_all_files_UFOS(home,last_sent_file)
##                        print(count_sent, 'файлов отправлено.')
##                    except Exception as send_err:
##                        print('UFOS.send_err',send_err)
##                        pass
                    #======Запись температуры в файл======
##                    some = device_ask(get_ser(0),make_par(ini_s,100,'Z','N'),0.99999)
##                    curr_date, curr_time = curr_datetime2()
##                    write_temperature('{0} {1}'.format(curr_date, curr_time),'{0} {1}'.format(run.temper1,run.temper2))
##                    print('{0} {1}'.format(curr_date, curr_time),'Line {0}; Poly {1}'.format(run.temper1,run.temper2))
                    #=====================================
                    function.count = 1
                    print('-----------{0}-----------'.format(chan))
                os.chdir(main.home)
                return(1)
            except Exception as a:
                print('answer_decode(): ',a)
                return(1)
##                pass
        else:   # if k!=1:
            spectr1 = []
##            spectr2 = []
            i = len(d) - 1
            if chan == 'S':
                pppp = 3500 #Номер пикселя, до которого считается максимальная амплитуда спектра
                while i>13:
                    i -= 1
                    spectr1.append(int(d[i+1]) * 255 + int(d[i]))
##                    spectr2.append(int(d[i]) * 255 + int(d[i+1]))
                    i -= 1
            else:
                pppp = 2500 #Номер пикселя, до которого считается максимальная амплитуда спектра
                while i>12:
                    i -= 1
                    spectr1.append(int(d[i+1]) * 255 + int(d[i]))
##                    spectr2.append(int(d[i]) * 255 + int(d[i+1]))
                    i -= 1
            
##            pppp = 3500
            Smax1 = max(spectr1[481:pppp])
##            print(Smax1)
            pmax = run.pmax #run.pmax
##            print(run.pmax)
##            Smax2 = max(spectr2[481:pppp])
            if Smax1<4000: #4000
                Smax = Smax1
##                if exposure <= 1100:#1100
##                    pmax = expo_plus(exposure)
            else:
                Smax = 2000
            try:
                k = pmax / Smax
                if k < 3:
                    k = k * (-0.1 * k + 1.1) # Эмпирический коэффициент для более плавного подхода к полосе допустимых значений
            except Exception as a:
                print('k = pmax / Smax:',a)
                if Smax == 0:
                    print('На выходе АЦП - нули')
            print('Экспозиция = {0}'.format(exposure))
            if chan in ['Z','S']:
                if abs(pmax - Smax) <= pmax * 0.1: # pmax + - 10%
                    k = 1
            return(k)
    else:
        function.good = False
        return(1)

def write_temperature(date_time,temp):
    with open(os.path.join(main.home,'temperature.txt'),'a') as f:
        print('{0} {1}'.format(date_time,temp),file=f)
    
def function(ser,ini_s):
    try:
        k = 0.99999
        function.good = True
        data_z_s = []
        data_d = []
        chan = str(ini_s['channel'])[0]
        accum = ini_s['accummulate']
        run.accum = accum
        function.gain = ini_s['gain']
        ch = ['Z','D','S']
        tzs = 1
        function.count = 1
        if chan == 'Z':
            expo = run.expoZ
        elif chan == 'S':
            expo = run.expoS
        file_mus = r'C:\WINDOWS\Media\tada.wav'
        winsound.PlaySound(file_mus,winsound.SND_FILENAME)
        while k!=1 and function.good:
            run.expo = expo
            if tzs:
                if chan == 'Z':
                    count = 0
                    expo = run.expoZ
                elif chan == 'S':
                    count = 0
                    expo = run.expoS
##                print(1)
                some = device_ask(ser,make_par(ini_s,expo,chan,'N'),k)
##                print(2)
                if some==False:
                    raise
                tzs = 0
            expo = round(expo*k)
            if str(ini_s['auto_exp'])=='1':
                #Start  Auto exposition
                data_z_s = device_ask(ser,make_par(ini_s,expo,chan,'S'),k)
                if len(data_z_s)==0:
                    print('Данные не получены')
                    break
                k = answer_decode(data_z_s,expo,chan,accum,k,ini_s)
                function.count += 1
                
                # Ограничение по максимальной экспозиции
                if (function.count>15 or expo>1100) and chan!='D':
                    k = 1
                    expo = 1100
                    function.count = 1
                    data_z_s = device_ask(ser,make_par(ini_s,expo,chan,'S'),0.99999)
                elif expo<24 and chan!='D':
                    expo = 50
                    k = 1
                    function.count = 1
                    data_z_s = device_ask(ser,make_par(ini_s,expo,chan,'S'),0.99999)
            else:
                data_z_s = device_ask(ser,make_par(ini_s,expo,chan,'S'),k)
                if len(data_z_s)==0:
                    print('Данные не получены')
                    break
                else:
                    print('Экспозиция = {0}'.format(expo))
                k = 1
                function.count += 1
                
            #End  Auto exposition
            if k==1:
                if chan == 'Z':
                    run.expoZ = int(ini_s['expo']) #expo
                elif chan == 'S':
                    run.expoS = int(ini_s['expo']) #expo
                if function.good:
                    answer_decode(data_z_s,expo,chan,accum,k,ini_s)   # Z(S) запись в файл
                    device_ask(ser,make_par(ini_s,expo,ch[1],'N'),k)
                    data_d = device_ask(ser,make_par(ini_s,expo,ch[1],'S'),k)
                    answer_decode(data_d,expo,ch[1],accum,1,ini_s)    # D запись в файл
                    data_ready = []
                    i=0
                    try:
                        while True:
                            data_ready.append(int(data_z_s[i])-int(data_d[i]))
                            i+=1
                    except:
                        k = answer_decode(data_ready,expo,str(chan)+'-'+str(ch[1]),accum,1,ini_s)
                    if len(str(ini_s['channel'])) == 1:
                        function.good=False
                        break
                    elif chan == str(ini_s['channel'])[1]:
                        function.good=False
                        break
                    chan = str(ini_s['channel'])[1]
                    tzs = 1
                    k = 0.99999
    except Exception as a:
        print('function(ser,ini_s): ',a)
        pass
        
def make_par(param,expo,chan,run):
    """     t[0] expo = 100
        t[1] chan = 'ZS'
        t[2] accum = 1
        t[3] gain = 0
        t[4] run = 'S'
        t[5] dev_id = 1
        t[6] time =
        t[7] repeat = 1
        t[8] pmax = 2400
        t[9] latitude = 50.50
        t[10] longitude = -50.50
        t[11] pix2nm = a/b/c
        t[12] kz = a/b/c
        t[13] kz_obl = a/b/c
        t[14] omega = 0/0/1
        t[15] hs = 7
        t[16] points = 735,814,968,1187,1275,1286,1783
        t[17] pix+- = 5
        t[18] hour_pelt = +4
        t[19] auto_exp = 1"""
    t = param             #Массив параметров
    if not run:
        run = t['set_run']
    p_header = b'#'
    pelt = b'0'   
    return(settings2send(p_header,1,expo,t['gain'],t['accummulate'],pelt,chan.encode(encoding='utf-8'),run.encode(encoding='utf-8')))

def run():
    try:
        ini_s = read_ini(main.home,'r','')
        if ini_s!=None:
            run.expoZ = int(ini_s['expo'])
            run.expoS = int(ini_s['expo'])
            run.pmax = int(ini_s['max'])
            run.expo = 1
            run.accum = 1
            run.temper1 = 0
            run.temper2 = 0
            temper_k = 0
            sleep_flag = False
            if ini_s['time']=='' or ini_s['repeat']!='1':
                n = input('\nКоличество измерений [1]: ')
                if n=='' or n=='\n':
                    n = 1
                else:
                    n = int(n)
                print('\n5 мин = 300\n10 мин = 600')
                t = input('Интервал между измерениями, сек: ')
                if t=='':
                    t = 0
                else:
                    t = int(t)
                for i in range(abs(n)):
                    some = function(get_ser(0),ini_s)
                    if some==False:
                        raise
                    time.sleep(abs(t))
            else:
                if int(ini_s['repeat'])==1:
                    print('Ежедневный повтор включён')
                curr_date, curr_time = curr_datetime2()
                mu, amas, hs = sunheight(ini_s['latitude'],ini_s['longitude'],curr_time,ini_s['hour_pelt'],curr_date)
                
                while int(ini_s['repeat'])==1:
                    
                    curr_date, curr_time = curr_datetime2()
                    mu, amas, hs = sunheight(ini_s['latitude'],ini_s['longitude'],curr_time,ini_s['hour_pelt'],curr_date)
                    
                    arr = ini_s['time'].split('-')
                    t1 = arr[0]         # Время начала измерений
                    t2 = arr[1]         # Время окончания измерений
                    mins = int(arr[2])  # Интервал измерений в минутах
                    
                    tcur = time.ctime()[11:13] + ':' + time.ctime()[14:16]
                    while hs>=float(ini_s['hs']):
                        sleep_flag = False
                        tbegin = time.ctime()[11:13] + ':' + time.ctime()[14:16]
##                            main.next_start = '{0} {1}'.format(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'), tbegin)
                        """Запуск измерений"""
                        print('Запуск Измерений:',tbegin)
                        function(get_ser(0),ini_s)
                        tcur = time.ctime()[11:13] + ':' + time.ctime()[14:16]
                        timerr = addtime(tbegin,mins)
                        main.next_start = '{0} {1}'.format(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'), timerr)
                        print('Следующее измерение в {0}.'.format(timerr))
                        ##---------------begin send----------------
                        try:
                            if not os.path.exists(os.path.join(main.home,'outbox.txt')):
                                f = open(os.path.join(main.home,'outbox.txt'),'w')
            ##                    print(1)
                                yy,mm,dd = get_min_date(main.home)
            ##                    print(2)
                                print('{0}-{1}-{2} 00:00:00.0000000'.format(yy,mm,dd),file=f,end='')
                                f.close()
                            last_sent_file = set_last_date.read(main.home) # '1900-12-12 13:14:15.0000000' to date
                            count_sent = send_all_files_UFOS(main.home,last_sent_file)
                            print(count_sent, 'файлов отправлено.')
                        except Exception as send_err:
                            print('UFOS.send_err',send_err)
                        ##--------------end send--------------------
                        print('Следующее измерение в {0}.'.format(timerr))
                        while timerr>tcur:
                            main.waiting = 1
                            tcur2 = curr_time2()
                            curr_date, curr_time = curr_datetime2()
                            mu, amas, hs = sunheight(ini_s['latitude'],ini_s['longitude'],curr_time,ini_s['hour_pelt'],curr_date)
                            time.sleep(1)
                            main.flag = get_flag()
                            if main.flag == 1:
                                print('*** Дополнительное измерение ***')
                                function(get_ser(0),ini_s)
                                main.flag = set_flag(0)
                            if tcur!=tcur2:
                                tcur = time.ctime()[11:13] + ':' + time.ctime()[14:16]
                        main.waiting = 0
                    else:
                        curr_date, curr_time = curr_datetime2()
                        mu, amas, hs = sunheight(ini_s['latitude'],ini_s['longitude'],curr_time,ini_s['hour_pelt'],curr_date)
##                            print('Текущая высота солнца: ',hs,' Запуск при ',ini_s[15], 'градусах.')
                        if sleep_flag == False:
                            print('Ожидание. Запуск при ',ini_s['hs'], 'градусах.')
                            sleep_flag = True
                        #======Запись температуры в файл======
##                            if temper_k==0:
##                                some = device_ask(get_ser(0),make_par(ini_s,100,'Z','N'),0.99999)
##                                curr_date, curr_time = curr_datetime2()
##                                write_temperature('{0} {1}'.format(curr_date, curr_time),'Line {0}; Poly {1}'.format(run.temper1,run.temper2))
##                            temper_k += 1
##                            if temper_k>=60:
##                                temper_k = 0
                        #=====================================
                        time.sleep(5)
                    ini_s = read_ini(main.home,'r','')
            input('Цикл измерений завершен.\n = Нажмите Enter = ')
        else:
            pass
    except Exception as err:
        print('Измерения прекращены\n = Нажмите Enter! = \n{0}'.format(err))

def addtime(time,add):
    tt = time.split(':')
    hh = int(tt[0])
    mm = int(tt[1])
    hc = add // 60
    mm += add % 60
    if mm < 10:
        mm = '0' + str(mm)
    elif 10 <= mm < 60:
        mm = str(mm)
    elif mm >= 60:
        hc += 1
        mm -= 60
        if mm < 10:
            mm = '0' + str(mm)
        elif 10 <= mm < 60:
            mm = str(mm)
    hh += hc
    if hh < 10:
        hh = '0' + str(hh)
    elif 10 <= hh < 24:
        hh = str(hh)
    elif hh >= 24:
        hh = hh % 24
        if hh < 10:
            hh = '0' + str(hh)
        elif 10 <= hh < 24:
            hh = str(hh)
    return(hh + ':' + mm)
        

def main():
    main.home = os.listdir(os.getcwd())
    read_ini(main.home,'r','')
    main.ports_COM = com_check_all()
    main.home = os.getcwd()
    main.flag = get_flag()
    main.waiting = 0
    main.next_start = 0
    if main.ports_COM:
        run()
    else:
        input('Устройство не обнаружено\n = Нажмите Enter = ')

def main_but(event):
    main()
        
"""===================Main program===================="""

if __name__ == '__main__':
    main()

        
