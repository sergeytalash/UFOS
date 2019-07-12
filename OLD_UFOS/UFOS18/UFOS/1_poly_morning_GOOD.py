import os
import numpy as np
from math import *

def open_config():
    data = read_file('_config.txt')
    values = {}
    for i in data:
        ii = i.split('=')
        values[ii[0].replace(' ','')] = float(ii[1].replace(' ','').replace('\n',''))
    return(values)

def calc(hg):
    """Not used"""
    hp = hg / 180 * pi
    z = sin(pi / 2 - hp)**2
    mu = 6391.229 / sqrt(6391.229**2 - 6371.223**2 * z)
    z1 = 1 / cos(pi / 2 - hp)
    amas = 0
    if hg <= 0:
        pass
    elif 0 < hg <20:
        amas = 45.022 * hg**(-0.9137)
    else:
        amas = z1 - (z1 - 1) * (0.0018167 - 0.002875 * (z1 - 1) - 0.0008083 * (z1 -1)**2)
    return(mu, amas)

def read_file(path):
    """Чтение данных из файла"""
    f = open(path,'r')
    data = f.readlines()
    f.close()
    return(data)

def range_(begin,end,step):
    """Not Used
    Создание массива 'begin' - 'end' с шагом 'step'"""
    i = begin
    t = []
    while i<end:
        t.append(round(i,1))
        i += step
    return(t)

def make_kz_coeff(x,y,deg):
    """
    x - массив данных оси x
    y - массив данных оси y
    deg - степень полинома
    Количество возвращаемых коэффициентов = deg + 1
    """
    x_arr = np.array(x)
    y_arr = np.array(y)
    return(np.polyfit(x_arr,y_arr,deg))

def make_amas_list(path):
    """Выбираются файлы Z-D"""
    files = os.listdir(path)
    amas_list = []
    mu_list = []
    files_list = []
    data_list = []
    for i in files:
        if i.find('Z-D')!=-1:
            data = read_file(os.path.join(path,i))
            amas = ''
            mu = ''
            done_flag = 0
            for j in data:
                if j.find('amas')!=-1:
                    amas = j.split(' ')[0]
##                    print('amas',j)
                    amas_list.append(amas)
                    done_flag += 1
                elif j.find('mu')!=-1 and j.find('Accummulate')==-1:
                    mu = j.split(' ')[0]
##                    print('mu',mu)
                    mu_list.append(mu)
                    done_flag += 1
                if done_flag>=2:
                    files_list.append(i)
                    data_list.append(data)
                    break
    return(files_list,mu_list,amas_list,data_list)

def take_values(data):
    """Выбираются только строки, состоящие из чисел"""
    new_data = []
    ind = data.index('[Value]\n')
    data = data[ind+1:]
    for i in data:
        try:
            new_data.append(int(i))
        except:
            pass
    return(new_data)

def make_pix_nm():
    """Создает массивы пикселов и длин волн"""
    pixs = ['#','pix']
    nms = ['#','nm']
    i = 1
    while i<=3691:
        pixs.append(i)
##        nms.append(str(pix2nm(i)).replace('.',','))
        nms.append(pix2nm(i))
        i += 1
    return(pixs,nms)

def write_file(path,new_all_data):
    """Запись в файл с транспонированием данных"""
    f = open(path,'w')
    row = 0 #Строка в файле
    while row<len(new_all_data[0]):
        row_mas = []
        for col in new_all_data:
    ##        print(col[row])
            try:
                row_mas.append(col[row])
            except:
                pass
##                print('row',row)
        for k in row_mas:
            print(str(k).replace('.',','),file=f,end=' ')
        print('',file=f)
        row += 1
    f.close()
    print(path,'Done')
    
def min_mas(mas,num):
    min_num = []
    for i in mas:
        min_num.append(abs(chk(i) - num))
    return(min_num)

def div_mas(m1,m2,num):
    """Деление массива m1 на массив m2 с заданной точностью num"""
    m3 = []
    if len(m1)==len(m2):
        i = 0
        while i<len(m1):
            m1_ok = m1[i]
            m2_ok = m2[i]
            try:
##                m3.append(str(round(m1_ok/m2_ok,num)).replace('.',','))
                m3.append(round(m1_ok/m2_ok,num))
            except ZeroDivisionError:
                m3.append("""#ДЕЛ/0!""")
            except Exception as err:
                print(m1_ok,m2_ok)
            i += 1
    else:
##        print(m2)
        print('Массивы имеют разную длину!')
    return(m3)

def chk(text):
    if text!='#ДЕЛ/0!':
        if str(text).find(',')!=-1:
            text = round(float(text.replace(',','.')),4)
        else:
            text = round(float(text),4)
    else:
        text = round(float(1),4)
    if text<=0:
        text = round(float(1),4)
    return(text)

def srednee(mas):
    summ = 0
    for i in mas:
        summ += float(i)
    return(summ/len(mas))

def start_one(oso,path):
    name,mu,amas,all_data = make_amas_list(path)
    pixs,nms = make_pix_nm()
    tmp = path.split('\\')
    """Строим массив с исходными измерениями"""
    new_name = ''
    new_all_data = [pixs,nms] #Добавляем в первые два столбца пикселы и длину волны
    mu_last = 12
##    index_mu_last = mu.index(mu_last)
##    for i in range(index_mu_last,len(name)-1,1):
    for i in range(0,len(name)-1,1):
        data = take_values(all_data[i])
    ##    print(amas)
        mu_current = float(mu[i])
##        if float(mu_last)-mu_current<=0:
        if mu_current<=mu_last or True:
            mu_last = mu_current
            new_name = 'm{0}'.format(float(amas[i]))
            data = [new_name] + data #Добавляем первой строкой имя столбца
            new_name = 'mu{0}'.format(mu_current)
            data = [new_name] + data #Добавляем первой строкой имя столбца
            new_all_data.append(data)
    ##    print(new_name,round(float(amas[i]),2))
    filename = 'mesured_'+tmp[-1]+tmp[-2]+tmp[-3]+'.csv'
    write_file(filename,new_all_data)

    """Строим массив отношений по заданным длинам волн"""
    i1,i2 = config['nm3'],config['nm4']
    mu_last = config['mu_max']
##    index_mu_last = mu.index(mu_last)
    i1_mas,i2_mas = [],[]
    mas1 = min_mas(nms[2:],i1)
    min_i1_nms = mas1.index(min(mas1)) + 1 #Номер пикселя для i1
    mas2 = min_mas(nms[2:],i2)
    min_i2_nms = mas2.index(min(mas2)) + 1 #Номер пикселя для i2
    #####################Столбец 1##
                     #mu        m       i1                  i2                  calc0     calc1     calc2
    new_all_data3 = [['#'] + [pixs[1]]+[pixs[min_i1_nms]]+[pixs[min_i2_nms]] + ['I3/I4'] + ['#'] + ['#'], 
    #####################Столбец 2##
                     # mu       m       i1                                  i2                                  calc0                           calc1       calc2
                     ['#'] + [nms[1]]+['I3_{0}'.format(nms[min_i1_nms])]+['I4_{0}'.format(nms[min_i2_nms])] + ['I3_{0}/I4_{1}'.format(i1,i2)] + ['#'] + ['Kz_obl']]
    kz_line_obl = []
    kz_line_mu_obl = []
    for i in new_all_data:
       if i[0][:2]=='mu':
            try:
                mu_current = chk(i[0].split('mu')[1])
                if mu_current<=mu_last or True:
                    mu_last = mu_current
                    I1nm = chk(sum(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right])/len(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right]))
                    I2nm = chk(sum(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right])/len(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right]))
                    calc0 = I1nm/I2nm
                    calc1 = 0 #right(chk(i[0].split('mu')[1]),chk(i[1].split('m')[1]),oso) #Правая часть уравнения
                    calc2 = 0 #calc1 - calc0 #Kz - Разница левой и правой части уравнения
                    kz_line_obl.append(calc0)
                    kz_line_mu_obl.append(mu_current)
        #####################Столбец 3+##
                    #       mu          m           i1      i2      calc0     calc1     calc2
                    data = [i[0]] + [i[1][1:]] + [I1nm] + [I2nm] + [calc0] + [calc1] + [calc2]
            except Exception as err:
                print(err)
##                print('err352',end=' ')
##                print(i[0],i[1])
                raise
            new_all_data3.append(data)
    filename = 'o_{0}-{1}_'.format(i1,i2)+tmp[-1]+tmp[-2]+tmp[-3]+'.csv'
    write_file(filename,new_all_data3)
    
    kz_koeff_obl = make_kz_coeff(kz_line_mu_obl,kz_line_obl,6).tolist() #Коэффициенты Kz_obl
    kz_date = path.split('\\')
    kz_f = open('kz_koeff_obl_{0}.txt'.format(kz_date[-1]+kz_date[-2]+kz_date[-3]),'w')
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    a = 0
    print('o3 {0}'.format(oso),file=kz_f)
    for i in kz_koeff_obl:
        string = alphabet[a] + ' ' + str(-i).replace('.',',')
        print(string,file=kz_f)
        a += 1
    kz_f.close()
    print('kz_koeff_obl.txt Done.')


    """Строим массив отношений по заданным длинам волн"""
    i1,i2 = config['nm1'],config['nm2']
    #
    #При изменении длин волн, так же необходимо их изменить в файлах data.uvo и settings.ini
    #
    mu_last = config['mu_max']
    i1_mas,i2_mas = [],[]
    mas1 = min_mas(nms[2:],i1)
    min_i1_nms = mas1.index(min(mas1)) + 1 #Номер пикселя для i1
    mas2 = min_mas(nms[2:],i2)
    min_i2_nms = mas2.index(min(mas2)) + 1 #Номер пикселя для i2
    #####################Столбец 1##
                     #mu        m       i1                  i2                  calc0           calc1     calc2     calc3
    new_all_data3 = [['#'] + [pixs[1]]+[pixs[min_i1_nms]]+[pixs[min_i2_nms]] + ['#'] + ['#'] + ['#'] + ['#'], 
    #####################Столбец 2##
                     # mu       m       i1                                  i2                                  calc0                           calc1                                    calc2      calc3
                     ['#'] + [nms[1]]+['I1_{0}'.format(nms[min_i1_nms])]+['I2_{0}'.format(nms[min_i2_nms])] + ['I1_{0}/I2_{1}'.format(i1,i2)] + ['Kz'] + ['#'] + ['#']]
    kz_line = []
    kz_line_mu = []
    for i in new_all_data:
       if i[0][:2]=='mu':
            try:
                mu_current = chk(i[0].split('mu')[1])
                if mu_current<=mu_last or True:
                    mu_last = mu_current
                    I1nm = chk(sum(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right])/len(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right]))
##                    print(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right],len(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right]),end=' - ')
                    I2nm = chk(sum(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right])/len(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right]))
##                    print(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right],len(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right]))
##                    if mu_current==3.56 or True:
##                        print('======================')
##                        print(chk(sum(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right])/len(i[min_i1_nms-pixels-pix_to_left:min_i1_nms+pixels+pix_to_right])),
##                              chk(sum(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right])/len(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right])))
##                        len(i[min_i2_nms-pixels-pix_to_left:min_i2_nms+pixels+pix_to_right])
                    calc0 = I1nm/I2nm
                    calc1 = oso/calc0 #Kz
##                    print('oso =',oso)
                    calc2 = 0
                    calc3 = 0
                    kz_line.append(calc1)
                    kz_line_mu.append(mu_current)
##                    print(calc2,mu_current)
        #####################Столбец 3+##
                            #mu       m             i1      i2      calc0     calc1     calc2     calc3
                    data = [i[0]] + [i[1][1:]] + [I1nm] + [I2nm] + [calc0] + [calc1] + [calc2] + [calc3] 
            except Exception as err:
                print(err)
##                print('err',end=' ')
##                print(i[0],i[1])
                raise
            new_all_data3.append(data)
    filename = 'o_{0}-{1}_'.format(i1,i2)+tmp[-1]+tmp[-2]+tmp[-3]+'.csv'
    write_file(filename,new_all_data3)

    kz_date = path.split('\\')
    kz_f = open('kz_koeff_{0}.txt'.format(kz_date[-1]+kz_date[-2]+kz_date[-3]),'w')
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    print('o3 {0}'.format(oso),file=kz_f)
    for step in range(2,7,1):
        a = 0
        kz_koeff = make_kz_coeff(kz_line_mu,kz_line,step).tolist() #Коэффициенты Kz
        for i in kz_koeff:
            string = alphabet[a] + ' ' + str(-i).replace('.',',')
            print(string,file=kz_f)
            a += 1
        print('\n',file=kz_f)
    kz_f.close()
    print('kz_koeff.txt Done.')

def add_zero(num):
    num = str(num)
    if len(num)==1:
        num = '0' + num
    return(num)

def nm2pix(nm):
    for i in range(1,3691,1):
        if nm==round(pix2nm(i)):
            return(i)
        
"""================================================="""


def pix2nm(p):
    """Pixel to nanometer"""
##    9.6*10**-8/0.039196277/270.314812842
    #Смещение 1.3 обязательно, если расчет калиброки по длинам волн произведен для полусферного канала.
##    nm = 9.6*10**-8 * p**2 + 0.039196277 * p + 270.314812842 # dev7
##    nm = 9.4*10**-8 * p**2 + 0.039379817 * p + 272.353939329 # dev4
##    nm = 1.12*10**-7 * p**2 + 0.039119466 * p + 262.598914138 # dev10
##    nm = 2.25*10**-7 * p**2 + 0.038489241 * p + 273.71185689 # dev6
##    nm = 1*10**-8 * p**2 + 0.040066014 * p + 269.041909841 # dev11
    a = '9.5*10**-8/0.039478253/277.025477156' # Формулу подставить сюда
    b = a.split('/')
    nm = eval(b[0])*p**2+eval(b[1])*p+eval(b[2])
    sm = 1.2
    return(round(nm+sm,2))

config = open_config()
nmm = config['nm_srednee'] #nm

pixels = nm2pix(300+nmm)-nm2pix(300)
##print(pixels)
pix_to_left = -1
pix_to_right = 2
ozon_mas,date_mas = [],[]
path = os.getcwd()
f = open('_ozone.txt','r')
data = f.readlines()
f.close()
for i in data:
    k = i.replace('\n','').split(' ')
    date_mas.append(k[0])
    ozon_mas.append(k[1])
    
    
for i in date_mas:
    oso = round(float(ozon_mas[date_mas.index(i)]),3)
    d = i.split('.')
    day_path = os.path.join(path,d[2],d[1],d[0])
    try:
        start_one(oso,day_path)
    except:
        pass
input('OK')
    
    
    


        
    
