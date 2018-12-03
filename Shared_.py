from math import *
import os
import datetime
import socket
import numpy as np
import sys
from ftplib import FTP
import pylab
import matplotlib.dates


def calc(x,abc,num):
    i = len(abc)
    ans = 0
    while i>0:
        ans += float(abc[-i])*x**(i-1)
        i -= 1
##   ans = float(abc[0])*x**2 + float(abc[1])*x + float(abc[2])
    return(round(ans,num))

def find_closest_pair(x,mas,mas_o3,mas_34):
    """R12,mas_r12,mas_o3,mas_r34"""
    ind = []
    for i in mas:
        ind.append(abs(float(x)-float(i)))
        
    bo = ind.index(min(ind))
    ind.pop(bo)
    bot_r = mas.pop(bo)
    bot_o3 = mas_o3.pop(bo)
##    bot_r_34 = mas_34.pop(bo)
    bot_r_34 = 1
    to = ind.index(min(ind))
    ind.pop()
    top_r = mas.pop(to)
    top_o3 = mas_o3.pop(to)
##    top_r_34 = mas_34.pop(to)
    top_r_34 = max(mas_34)
    
    return(bot_r,top_r,bot_o3,top_o3,bot_r_34,top_r_34)

def eva_r34b(ini,mu):
    abc = ini.split('/')
    mu = float(mu)
    return(eval(abc[0])*mu**2 +
           eval(abc[1])*mu +
           eval(abc[2])
           )

def o2nomo(mu,R12,R34,nomo_s,ini_s):
    #not use
    cn_all = []
    digs = 2
    
    for i in nomo_s:
        cn = {}
        c = 4
        cn[i[0]] = int(i[1])    #ozone
        cn[i[2]] = i[3]         #date
        cn[i[c]] = i[c+1:c+digs+2]       #>5 [5:8]
        c += digs+2 #c = 8
##        print(c)
        cn[i[c]] = i[c+1:c+digs+2]      #5>3 [9:12]
        c += digs+2 #c = 12
##        print(c)
        cn[i[c]] = i[c+1:c+digs+2]    #3> [13:16]
        c += digs+2 #c = 16
##        print(c)
        cn[i[c]] = i[c+1:c+digs+2]    #>5 34 [17:20]
        c += digs+2 #c = 20
##        print(c)
        cn[i[c]] = i[c+1:c+digs+2]    #5>3 34 [21:24]
        c += digs+2 #c = 24
##        print(c)
        cn[i[c]] = i[c+1:c+digs+2]    #3> 34 [25:28]
        cn_all.append(cn)
##        print(cn)
    mas_r12 = []
    mas_r34 = []
    mas_o3 = []
    R34b = eva_r34b(ini_s['kdX'],mu)
    for cn in cn_all:
        if mu>=5:
            r12 = calc(mu,cn['mu>5'],6)
            r34 = calc(mu,cn['mu34>5'],6)
        elif 5>mu>3:
            r12 = calc(mu,cn['5>mu>3'],6)
            r34 = calc(mu,cn['5>mu34>3'],6)
        elif 3>=mu:
            r12 = calc(mu,cn['3>mu'],6)
            r34 = calc(mu,cn['3>mu34'],6)
        mas_r12.append(r12)
        mas_r34.append(r34)
        mas_o3.append(cn['ozone'])
    r12_1,r12_2,o1,o2,r34_1,r34_2 = find_closest_pair(R12,mas_r12,mas_o3,mas_r34)
    #bot_r,top_r,bot_o3,top_o3,bot_r_34,top_r_34
##    print([r1,o1,r2,o2])
    
##    Robl = (R34 - max(r1_34,r2_34))
##    print(log10(R34),R34b)
##    Robl = ((log10(R34) - R34b) * (1 + 0.003 * mu))
##    R12 += (R34 - (r34_1+r34_2)/2)# / (1 + mu * 0.003)
##    add_R34 = R34_new - R34
##    print(R34)
##    1.08675x - 0.08480
##    R12 = R12*(2.03667*x**2 - 3.28798*x + 2.25751)
##    x = 300
    
    x = r34_2/R34
    R12 = R12*(1.08675*x - 0.12480)
    x = ((r12_2*o1 - r12_1*o2) + (o2 - o1)*R12)/(r12_2 - r12_1)
    
##    if R12>=r12_2:
##        o_max = o1
##    else:
##        o_max = o2
##    x = o_max + (o2 - o1) * (R12 - r12_1) / (r12_2 - r12_1)
    x = x/1000 #- Robl
    o3 = round(round(x,3) * 1000)
##    print('{}\t{}\t{}\t{}\t{}'.format(mu,o3,R12,R34,r34_2))
    return(o3)

def read_nomo(path):
    with open(os.path.join(path,'Calibration','nomogramma.txt'),'r') as f:
        data = f.readlines()
    nomo = []
    for i in data:
        for j in ['[',']',' ']:
            i = i.replace(j,'')
        i = i.replace(',','\t').strip().split('\t')
        nomo.append(i)
##    print(nomo)
    return(nomo)

def make_kz_coeff(x,y,deg):
    """
    x - массив данных оси x
    y - массив данных оси y
    deg - степень полинома
    Количество возвращаемых коэффициентов = deg + 1
    """
    x_arr = np.array(x)
    y_arr = np.array(y)
    a = np.polyfit(x_arr,y_arr,deg)
    return(a.tolist())
    
def read_sensitivity(path):
    with open(os.path.join(path,'sensitivity.txt')) as f:
        sens = f.readlines()
    return([float(i.strip()) for i in sens])

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

def make_uv(p1,p2,data,ome,mode,expo,expo_grad,inis):
    prom = 10
    uv = 0
    c = inis['pix2nm'].split('/')
    if ome==None:
        ome=[]
        for i in range(len(data)):
            ome.append(1)
    if mode in ['uva','uvb']:
        for i in range(p1,p2,1):
            try:
                asd = float(data[int(i)]) * float(ome[int(i)])
                uv += asd
            except:
                pass
        uv *= float(c[1]) * expo_grad / int(expo)
        if mode=='uva':
            uv *= float(inis['uva_koef'])
        if mode=='uvb':
            uv *= float(inis['uvb_koef'])
    elif mode == 'uve':
        for i in range(p1,p2,1):
            try:
                asd = float(data[int(i)]) * erithema(int(i),c) * float(ome[int(i)])
                uv += asd
                uv *= float(inis['uve_koef'])
            except Exception as err:
##                print(err,sys.exc_info()[-1].tb_lineno)
                pass
        uv *= float(c[1]) * expo_grad / int(expo)
    return(uv)

class set_last_date():
    """If file not sent, it's name will be written to the 'outbox' file"""
    def write(home,date):
        file = os.path.join(home,'outbox.txt')
        with open(file,'w') as f:
            date = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S.0000000') # date to '1900-12-12 13:14:15.0000000' 
            print(date,file=f,end='')
    def read(home):
        file = os.path.join(home,'outbox.txt')
        with open(file,'r') as f:
            date = f.readline()
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.0000000') # '1900-12-12 13:14:15.0000000' to date
        return(date)
        
def set_flag(flag):
    """Дополнительное измерение если flag == 1"""
    with open('manual_start','w') as f:
        try:
            f.write(str(flag))
        except:
            flag = 0
    return(flag)

def get_flag():
    with open('manual_start','r') as f:
        try:
            flag = int(f.readline())
        except:
            flag = 0
    return(flag)

def curr_time2():
    date_time = datetime.datetime.now()
    tcur = datetime.datetime.strftime(date_time,'%H:%M')
    return(tcur)

def curr_datetime2():
    date_time = datetime.datetime.now()
    date = datetime.datetime.strftime(date_time,'%d.%m.%Y')
    time = datetime.datetime.strftime(date_time,'%H:%M:%S')
    return(date,time)

def create_dirs(ftp,abspath):
    local_dirs = abspath.split('\\')[-4:-1]
    remote_dirs = ftp.nlst()
    for i in local_dirs:
        try:
            ftp.mkd(i)
        except:
            pass
        ftp.cwd(i)
    return(ftp)
        
    
def to_ftp(host,port,remote_dir,user,password,abspath):
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
            create_dirs(ftp,abspath)
            ftp.storlines('STOR ' + file_name, open(abspath,'rb'))
            tex = 'OK'
        except Exception as err2:
            tex = err2
        finally:
            ftp.close()
    except:
        tex = 'Ошибка подключения FTP!'
    return(tex)
        
def sock_connect2(HOST,PORT,text,buffer = 2048):
    data = text.encode(encoding = 'utf-8')
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
    return(t)

def send_files_ufos(home,file2send):
    return(send_files(home,file2send.replace('\n','')))

def get_min_date(path):
    def get_min(path):
        min_dir = []
        dirs = os.listdir(path)
        for i in dirs:
            if os.path.isdir(os.path.join(path,i)) and i.isdigit():
                min_dir.append(i)
        return(min(y))
    
    year = get_min(path)
    month = get_min(os.path.join(path,year))
    day = get_min(os.path.join(path,year,month))
    return(year,month,day)
    
def get_datetime(home,path):
    """Получение даты и времени из файла измерений"""
    with open(path,'r') as f:
##        y,m,d = get_min_date(home)
        data1 = []
        for i in range(2):
            data = f.readline()
            if data.count('time')>0:
                # ;Measurement details: channel = Z-D, date = 02.07.2015, time = 00:02:07
                data = data.split(',')
                for i in data:
                    b = i.split(' ')[-1].replace('\n','')
                    data1.append(b)
    # data1 = ['Z-D','01.01.1900','00:02:07']
    data = datetime.datetime.strptime('{0} {1}'.format(data1[1],data1[2]),'%d.%m.%Y %H:%M:%S')
    return(data) 

    
            
def send_files(home,file2send):
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
##    host,port,data4send = "195.239.117.34", 20000, ''
    tex = ''
    def take_ozone(par):
        if len(par)==2:
            return(par[0])
        else:
            return(0)
    try:
        f = open(file2send,'r')
        text = f.readlines()
        for i in text:
            if i=='\n':
                text.remove(i)
        for i in [' ',"'","\\n",'[',']']:
            text = str(text).replace(i,'')
        ds = text.split(',')
        ini_s = read_ini(home,'r','')
        dev_id = ini_s['dev_id']
        station_id = ini_s['stn_id']
        channel = ds[1].split('=')[1]
        date = str(ds[2].split('=')[1])
        year = date.split('.')[2]
        month = date.split('.')[1]
        day = date.split('.')[0]
        date = '{0}-{1}-{2}'.format(year,month,day)
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
        for i in (' ','[',']',"'"):
            spect = spect.replace(i,'')
        pars = read_ini(home,'r','')
        expo1       = pars['expo']
        channel1    = pars['channel']
        accum1      = pars['accummulate']
        gain1       = pars['gain']
        set_run     = pars['set_run']
        dev_id1     = pars['dev_id']
        time1       = pars['time']
        repeat1     = pars['repeat']
        max1        = pars['max']
        latitude1   = pars['latitude']
        longitude1  = pars['longitude']
        pix2nm1     = pars['pix2nm']
        kz1         = pars['kz']
        kz_obl1     = pars['kz_obl']
        omega1      = pars['omega']
        hs1         = pars['hs']
        points1     = pars['points']
        pixels1     = pars['pix+-']
        hour_pelt1  = pars['hour_pelt']
        auto_exp1   = pars['auto_exp']
        zenith_add1 = pars['zenith_add']
        ozone_add1  = pars['ozone_add']
        stn_id1     = pars['stn_id']
        R21_01      = pars['R21_0']
        R34_01      = pars['R34_0']
        kdX1        = pars['kdX']
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
        #-----------socket-------------
        s_type = ''
        tex = ''
        if host!='0':
            tex = sock_connect2(host,port,data4send)
            if str(tex)=='OK':
                date_time = datetime.datetime.strptime(date_time,'%Y-%m-%d %H:%M:%S')
                set_last_date.write(home,date_time)
                s_type = '(socket)'
        #------------ftp---------------
        s_type2 = ''
        tex_ftp = ''
        if ftp_host!='0':
            tex_ftp = to_ftp(ftp_host,ftp_port,ftp_path,ftp_user,ftp_pass,file2send)
            if str(tex_ftp)=='OK':
                date_time = datetime.datetime.strptime(date_time,'%Y-%m-%d %H:%M:%S')
                set_last_date.write(home,date_time)
                s_type2 = '(ftp)'
        #------------------------------
        print('{0} Отправлен {1}{2} (dev: {3})'.format(file2send.replace('\n',''),s_type,s_type2,dev_id))
        if tex in ['OK',''] and tex_ftp in ['OK','']:
            return('OK')
        else:
            return(tex+'\n'+tex_ftp)
    except Exception as err:
        print('Shared.send_files(): {} - line {}'.format(err,sys.exc_info()[2].tb_lineno))
        return(False)
        
# def plot_uv(v,t,curr_time,canvas,plotx,ploty,kx,ky,mx,my,o3_mode):
#     r = 3
#     if v == 0:
#         for i in range(0,len(t['data'])):
#             try:
#                 color = t['color'][i]
#                 if color=='blue':
#                     point1x = round((int(t['time'][i][:2])+int(t['time'][i][3:5])/60)/24*plotx)
#                     point1y = round(t['data'][i] * ky )
#                     canvas.create_oval(point1x + mx - r, ploty - point1y + my - r, point1x + mx + r, ploty - point1y + my + r,outline=color,fill=color)
#             except:
#                 pass
#     elif v == 1 or v==2:
#         ppp = curr_time[-1] - curr_time[0] + 1
#         for i in range(0,len(t['data'])):
#             try:
#                 color = t['color'][i]
#                 if color=='blue':
#                     point1x = round(((int(t['time'][i][:2])+int(t['time'][i][3:5])/60)-curr_time[0])/ppp*plotx)
#                     point1y = round(t['data'][i] * ky )
#                     canvas.create_oval(point1x + mx - r, ploty - point1y + my - r, point1x + mx + r, ploty - point1y + my + r,outline=color,fill=color)
#             except:
#                 pass
#     """Расчет среднего значения УФ"""
#     uv = 0
#     return(uv)

# def plot_uv2(o3_mode,ImageTk,ttk,some_root,plt,rc,canvas,home,plotx,ploty,xmax,ymax,x,y,o33):
#     global img
#     try:
#         new_x = []
#         for i in x:
#             if i.count(':')>0:
#                 new_x.append(datetime.datetime.strptime(i,'%H:%M:%S'))
#         x = matplotlib.dates.date2num(new_x)
#         fig2 = plt.figure()
#         fig2.set_size_inches(plotx/80,ploty/80)
#         fig2.set_dpi(75)
#         ax = pylab.subplot(1, 1, 1)
#
#         if o3_mode in ['uva','uvb','uve']: #uva,uvb,uve
#             zero = 0
#             max_y = max(y)
#             shag_y = 10**(round(log10(max_y))-1)
#             max_y += shag_y
#         elif o3_mode == 'ozone': #ozone
#             zero = 200
#             max_y = 501
#             shag_y = 100
#         ma_y = []
#         for i in range(zero,max_y+100,shag_y):
#             ma_y.append(i)
#         ax.set_yticks(ma_y)
#         ax.set_ylim(zero,max_y+100)
#
#         ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
#
# ##        ma_x = []
# ##        for i in range(0,max(x),shag_x):
# ##            ma_x.append(i)
# ##        ax.set_xticks(ma_x) #Интервал между значениями по оси х
# ##        ax.set_xlim(min(x),max(x)+shag_x)
#
#         ax.grid(True)# координатную сетку рисовать
#         rc('xtick', labelsize=12,color='#000000',direction='in') # x tick labels
#         rc('ytick', labelsize=12,color='#000000',direction='in') # x tick labels
#         rc('lines', lw=0.6, color='#000000') # thicker black lines
#         rc('grid', color='#000000', lw=0.5) # solid gray grid lines
#         rc('text', color='#000000')
#         rc('axes', labelcolor='#000000') # axes сolor
#         if o33:
#             xs = np.array([x[0],x[-1]])
#             ys = np.array([o33,o33])
#             pylab.plot(xs,ys,'-b')
#         x = np.array(x)
#         y = np.array(y)*1.0
#         pylab.plot_date(x, y, fmt="bo")
#
#     except Exception as err:
#         print(err,sys.exc_info()[-1].tb_lineno)
# ##    ax.plot(x,y,'bo')
#     """//\ /\ /\ /\ /\\"""
#
#     """Построение дополнительных линий, подписей к ним и значения пересечения с графиком"""
#
#     ax.set_ylabel('mWt/m2*nm')
#     image_fig_path = os.path.join(home,'fig.png')
#     try:
#         label.destroy()
#     except:
#         pass
#     try:
#         plt.savefig(image_fig_path,bbox_inches='tight', pad_inches=0,dpi=100)
# ##        plt.close()
#         img = ImageTk.PhotoImage(file = image_fig_path)
# ##        label = ttk.Label(some_root,image=photoimage)
# ##        label.image = photoimage
#         canvas.create_image(xmax//2, ymax, anchor='s',image=img)
#     except Exception as err:
#         print(err)
#     return(0)

def time_code(start):
    """
    'start' - начать отсчет
    'stop' - остановить отсчет и вывести результат
    """
    if start=='start':
        time_code.ct_start = float(str(datetime.datetime.now())[17:23])
    elif start=='stop':
        time_code.ct_next = float(str(datetime.datetime.now())[17:23])
        time_code.ct = time_code.ct_next - time_code.ct_start
        time_code.ct_start = time_code.ct_next
        print(time_code.ct)

# def read_connect(home):
#     with open(os.path.join(home,'connect.ini')) as f:
#         data = f.readlines()
#         new_data = {}
#         for i in data:
#             if i[0] not in ['\n',' ','#']:
#                 line = i.replace(' ','').replace('\n','').split('=')
#                 new_data[line[0]] = line[1]
#         return(new_data)
            
    
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
    
##def kz_f(abc,dig):
##    """
##    abc - массив коэффициентов полинома
##    dig - номер коэффициента 11/21/31/12/22/32
##    """
##    kz = ''
####    print(abc)
##    return eval(abc[dig])

def kz_obl_f(mu,b,pmas2):
    def eva(abc,x):
        return(eval(abc[0]) * float(x)**2 + eval(abc[1]) * float(x) + eval(abc[2]))
    """
    b - массив коэффициентов полинома
    amas - солнечная масса
    pmas2 - значения в точках 332 и 352
    """
    if b==0 or pmas2==0 or pmas2[0]<=0 or pmas2[1]<=0:
        return(1)
    abc = [b[0],b[1],b[2]]
    kz_obl_1 = eva(abc,mu)
    try:
        if kz_obl_f.value==1:
            return(kz_obl)
        elif kz_obl_f.value==0:
            return(0)
    except:
        return(kz_obl)

def omega(abc,pix,digs):
    """pixel to omega"""
    """
    abc - массив коэффициентов полинома
    pix - номер пиксела
    dig - количество знаков после запятой
    """
    
    if len(pix)>1:
        mas = []
        for i in pix:
            mas.append(round(eval(abc[0]) * int(i)**2 + eval(abc[1]) * int(i) + eval(abc[2]),digs))
##        print('mas',abc)
        return mas
    else:
        return round(eval(abc[0]) * int(pix)**2 + eval(abc[1]) * int(pix) + eval(abc[2]),digs)

def sredne(I,o3_mode,digs):
    """Среднее арифметическое"""
    k = 0
    i = 0
    try:
        leng = len(I)
        if o3_mode!='ozone':
            while i<leng:
                k += int(I[i])
                i += 1
        else:
            while i<leng:
                if I[i]!='':
                    k += int(I[i])
                    i+=1
        k = k / leng
    except Exception as err:
        print('shared.sredne: ',err)
        try:
            k = int(I)
        except:
            k = 1
    return(round(k,digs))

def srznach(a,o3_mode):
    """
    Среднее арифметическое
    a - массив значений, который нужно осреднить
    o3_mode=='ozone' - для расчёта дневного озона
    o3_mode==0 - для обычного расчёта среднего арифметического
    """
    b = 0
    leng = len(a)
    for i in a:
        if o3_mode=='ozone':
            if i!='' and 500>i>250:
                b += int(i)
            else:
                leng -= 1
        else:
            if i!='':
                b += int(i)
    try:
        return(round(b/leng))
    except Exception as err:
        print('shared.srznach: ',err)
        return(0)

def read_ini(path,mode,par):
    if mode=='w':
        p = par
    else:
        #Резервные данные
        p = ['300','ZS','3','0','S',
             '1','00:00-23:59-10','1','3200','59.57',
             '-30.42','9.6*10**-8/0.039196277/270.314812842','0.00005/-0.00152/0.01764/-0.1024/0.29792','-1.90657/2.89708','0/0/1',
             '5','317,340,340,359.5,393.37,396.78','5','+3','1',
             '-1.2','0','042','0/-0.00441/0.09348/0.46213/1.08544','0/-0.00027/0.00731/-0.07772/1.14555',
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
        if tmp and mode=='r':
            file_n = open(os.path.join(path,name), 'r')
        else:
            file_n = open(os.path.join(path,name), 'w')
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
                   p['longitude'],p['pix2nm'],
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
                   p['uve_koef']),file = file_n)
            file_n.close()
            file_n=open(os.path.join(path,name), 'r')
        while True:
            tmp = file_n.readline()
            if tmp!='':
                if tmp[0]==';' or tmp[0]==' ' or tmp=='\n':
                    pass
                else:
                    allinfo.append([tmp.split('=')[0],tmp.split('=')[1].split('\n')[0]])
            else:
                break
        file_n.close()
        for name,value in allinfo:
            settings[name] = value
##            print(name,value)
##        t[0] expo = 100
##        t[1] chan = 'ZS'
##        t[2] accum = 1
##        t[3] gain = 0
##        t[4] run = 'S'
##        t[5] dev_id = 1
##        t[6] time =
##        t[7] repeat = 1
##        t[8] pmax = 2400
##        t[9] latitude = 50.50
##        t[10] longitude = -50.50
##        t[11] pix2nm = -2*10**-8/0.0403/278.2
##        t[12] kz = 1/1/1/1/1/1
##        t[13] kz_obl = 1/1/1/1/1/1
##        t[14] omega = 0/0/1
##        t[15] hs = 7
##        t[16] points = 735,814,968,1187,1275,1286,1783
##        t[17] pix+- = 5
##        t[18] hour_pelt = +4
##        t[19] auto_exp = 1
##        t[20] zenith_add = 1
##        t[21] ozone_add=0
##        t[22] stn_id=042
##        t[23] R21_0=0/-0.00441/0.09348/0.46213/1.08544
##        t[24] R34_0=0/-0.00027/0.00731/-0.07772/1.14555
##        t[25] kdX=0.04227/-0.01490/-0.66512/0.23933/1.08258/0.60007
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


# def sunheight(f, l, time, pelt, date):
#     f,l,time,pelt,date = float(f),float(l),str(time),int(pelt),str(date)
#     """
#     f - широта в градусах и минутах (+-ГГ.ММ) +северная -южная
#     l - долгота в градусах и минутах (+-ГГ.ММ) +западная -восточная
#     time - время ('ЧЧ:ММ:СС')
#     pelt - часовой пояс (+-П)
#     date - дата ('ДД.ММ.ГГГГ')
#     """
#     f = (f - 0.4 * copysign(1, f) * round(abs(f) // 1)) * pi / 108
#     l = (l - 0.4 * copysign(1, l) * round(abs(l) // 1)) / 0.6
#     curtime = time
#     hour = int(curtime[:2])
#     mins = int(curtime[3:5])
#     secs = int(curtime[6:])
#     timer = hour * 3600 + mins * 60 + secs  #Текущее время в секундах
#     tim = timer - 3600 * pelt               #Гринвическое время
#     day = int(date[:2]) + 58
#     month = int(date[3:5])
#     year = int(date[6:])
#     if month < 3:
#         year -= 1
#     d_m = [3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 1]   #Месяцы кроме февраля
#     d_d = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31]  #Количество дней в месяце
#     i = 0
#     while i<11:
#         if month == d_m[i]:
#             break
#         else:
#             day += d_d[i]
#         i += 1
#     dd = day + 365 * year + round(year // 4) - round(year // 100) + round(year // 400) + 13 / 38
#     day = (dd + tim / 3600 / 24) * pi / 182.6213
#     s = 0.00686 - 0.39915 * cos(day) + 0.07432 * sin(day)
#     s += -0.00693 * cos(2 * day) + 0.00114 * sin(2 * day)
#     s += -0.00226 * cos(3 * day) + 0.0012 * sin(3 * day)
#     ty = -0.017 - 0.43 * cos(day) + 7.35 * sin(day) + 3.35 * cos(2 * day) + 9.366 * sin(2 * day)
#     r = pi * (tim / 3600 - ty / 60 - l / 15 - 12) / 12
#     q = sin(f) * sin(s) + cos(f) * cos(s) * cos(r)
#     hp = atan(q / sqrt(1 - q**2))
#     hg = hp * 180 / pi
#     z = sin(pi / 2 - hp)**2
#     mu = 6391.229 / sqrt(6391.229**2 - 6371.223**2 * z)
#     z1 = 1 / cos(pi / 2 - hp)
#     amas = 0
#     if hg <= 0:
#         pass
# ##        hg = 0
#     elif 0 < hg <20:
#         amas = 45.022 * hg**(-0.9137)
#     else:
#         amas = z1 - (z1 - 1) * (0.0018167 - 0.002875 * (z1 - 1) - 0.0008083 * (z1 -1)**2)
#     return (mu, amas, round(hg,3))

# def ozon(i1o3,i2o3,w1,w2,iatm1,iatm2,alpha1,alpha2,beta1,beta2,amas,mu,k,k_obl,digs,ini_s,nomo_s):
#     #not use
# ##    global ini_s
# ##    print('i1o3,i2o3,w1,w2,iatm1,iatm2,alpha1,alpha2,beta1,beta2,amas,mu,k,k_obl')
# ##    print(i1o3,i2o3,w1,w2,iatm1,iatm2,alpha1,alpha2,beta1,beta2,amas,mu,k,k_obl)
#     """i1o3, i2o3 - измеренные значения
#     w1, w2 - чувствительность линейки
#     iatm1, iatm2 - внеатмосферные значения
#     alpha1, alpha2 - коэффикиент поглощения озона
#     beta1, beta2 - коэффициент рассеивания в атмосфере
#     amas - солнечная масса
#     mu - озонная масса
#     k - коэффициенты зенитного полинома
#     k_obl - коэффициенты облачного полинома + R34
#     digs - точность вычисления озона"""
#     R34 = float(k_obl[1][0])/float(k_obl[1][1])
#
# ##    R21 = float(i2o3) / float(i1o3)
#     R12 = float(i1o3) / float(i2o3)  # R12, а не R21
# ##    print(i1o3,i2o3)
# ##    o3 = koefficients(mu,R12,R34,ini_s)
#     o3 = o2nomo(mu,R12,R34,nomo_s,ini_s)
# ##    print([mu,R12,R34])
#     o3 += int(ini_s['ozone_add'])
#     return(round(o3))



# def find_mu_amas_hs(file):
#     tmp = 0
#     vivod = []
#     while tmp<100:
#         text = file.readline()
#         if text[-3:]=='mu\n':
#             mu = text.split(' ')[0]
#             vivod.append(float(mu))
#             text = file.readline()
#             amas = text.split(' ')[0]
#             vivod.append(float(amas))
#             text = file.readline()
#             hs = text.split(' ')[0]
#             vivod.append(float(hs))
#         text = file.readline()
#         if text[-6:]=='ozone\n':
#             ozone = text.split(' ')[0]
#             vivod.append(int(ozone))
#             text = file.readline()
#             uva = text.split(' ')[0]
#             vivod.append(int(uva))
#             text = file.readline()
#             uvb = text.split(' ')[0]
#             vivod.append(int(uvb))
#             text = file.readline()
#             uve = text.split(' ')[0]
#             vivod.append(int(uve))
#         tmp += 1
#     if vivod==[]:
#         return 0
#     else:
#         return(vivod)
    
# def kz_func(x,mu,k):
#     """
#     x - значение озона
#     mu - озонная масса
#     k - коэффициенты полинома из файла конфигурации [0,1,2,3,4,5]
#     """
#     #Correct calculation of Zenith coefficient
#     #26.01787778 -625.9156872 4948.538906 -10366.89445 9881.921419
#     mas = []
#     a = 1
#     dx = 1
# ##    -0.1939146/0.0435974/5.00663/-1.1714645/-38.0708681/8.7189027/59.9827414/-11.1669097/-34.4971532/2.5025566
#     kz = ((a*float(k[0])*x*dx + a*float(k[1]))*mu**4 +
#           (a*float(k[2])*x*dx + a*float(k[3]))*mu**3 +
#           (a*float(k[4])*x*dx + a*float(k[5]))*mu**2 +
#           (a*float(k[6])*x*dx + a*float(k[7]))*mu +
#           (a*float(k[8])*x*dx + a*float(k[9])))
#     mas.append(kz)
#     kz = 5.241977824805645e-05*a*mu**4 -0.0015241138825670168*a*mu**3 + 0.017641302174997472*a*mu**2 -0.10240157661957514*a*mu + 0.2979216735493541*a #kz 15.03.2015 dev 7
#     mas.append(kz)
#     """kz2 = Kz302 - Delta_Kz"""
#     return(mas)

# def nm2pix(nm,configure2,add):
#     nm = float(nm)
#     abc = configure2
#     if 270 < nm < 350:
#         pix = 0
#         ans_nm = pix2nm(abc,pix,1,add)
#         while ans_nm < nm:
#             pix += 1
#             ans_nm = pix2nm(abc,pix,1,add)
#     elif 350 <= nm < 430:
#         pix = 1500
#         ans_nm = pix2nm(abc,pix,1,add)
#         while ans_nm < nm:
#             pix += 1
#             ans_nm = pix2nm(abc,pix,1,add)
#     else:
#         print(nm,'nm2pix: error')
#     return(pix)

# def ozone_uv(home,ome,data,date,time,file_name,expo_grad,channel):
#     #not use
#     """ome - чувствительность прибора"""
# ##    global ini_s
#     tmp1 = 0
#     tmp2 = 0
#     o3lab = ''
#     uvalab = ''
#     uvblab = ''
#     uvelab = ''
#     curr_o3 = [0,0,0,0,0]
#     file_name = os.path.basename(file_name)
# ##    print(file_name)
#     file_name = file_name.split('_')[1]
#     ini_s = read_ini(home,'r','')
# ##    nomo_s = read_nomo(home)
#     conf2 = ini_s['pix2nm'].split('/')
#     if file_name.find('Z'):
#         add = float(ini_s['zenith_add'])
#     else:
#         add = 0
#     point = ini_s['points'].split(',')
#     ##print(point)
#     p_uva1,p_uva2 = nm2pix(315,conf2,add),nm2pix(400,conf2,add)
#     p_uvb1,p_uvb2 = nm2pix(280,conf2,add),nm2pix(315,conf2,add)
#     p_uve1,p_uve2 = 0,3691 #nm2pix(290),nm2pix(420)
#     p_1 = nm2pix(float(point[0]),conf2,add)
#     p_2 = nm2pix(float(point[1]),conf2,add)
#     p_3 = nm2pix(float(point[2]),conf2,add)
#     p_4 = nm2pix(float(point[3]),conf2,add)
#     ps = [p_1,p_2,p_3,p_4]
#     p330_350 = [nm2pix(point[2],conf2,add),nm2pix(point[3],conf2,add)]
#     """    lines=[735,814,968, # I1
#               1187,1275,   # I2
#               1286,1783]   # Облачность"""
#     prom = int(ini_s['pix+-'])      # -prom (.) + prom
#     """Расчет озона"""
#     if data!=0:
#         p_mas = []
#         j = 0
#         while j<4:
#             jj = ps[j] #Points in pixels
#             p_mas.append(sredne(data[jj-prom:jj+prom+1],'ozone',3))
#             j += 1
#         """Для Санкт-Петербурга"""
#         f = float(ini_s['latitude'])
#         l = float(ini_s['longitude'])
#         digs = 3
#         """312,    332,    332,    352"""
#         p1 = 1 # 1
#         p2 = 2 # 2
#         #Не менять
#         w1 = 1      #Чувствительность линейки, уже учтена в формуле!
#         w2 = 1      #Чувствительность линейки, уже учтена в формуле!
#         pelt = int(ini_s['hour_pelt'])
#         mu, amas, hg = sunheight(f,l,time,pelt,date)
#
#         "Расчёт mv для zero1, zero2"
#         mv = 0
#         zero_count = 0
#         spectrum = [None] * len(main_func.data)
#         for i in range(p_zero1, p_zero2 + 1):
#             mv = mv + main_func.data[i]
#             zero_count = zero_count + 1
#         mv = mv / zero_count
#         for i in range(p_lamst, len(main_func.data)-1):
#             spectrum[i] = main_func.data[i] - mv
#         """Расчет озона"""
#         p_mas = []
#         j = 0
#         while j<len(lambda_consts):
#             jj = lambda_consts_pix[j] #in Pixels
#             "Массив средних значений в пределах допуска для реперных длин волн"
#             p_mas.append(sumarize(spectrum[jj-prom:jj+prom+1]))
#             j += 1
#         "Расчёт измеренных r12, r23"
#         r12m = p_mas[0]/p_mas[1]
#         r23m = p_mas[2]/p_mas[3]
#         """Расчёт mueff"""
#         mueff = (1+mu)/2
#         """Расчёт r23 для ясного дня"""
#         r23clean = 1
#         if mueff<2:
#             r23clean = get_polynomial_result(ini_s['kzLess2'].split('/'),mueff)
#         else:
#             r23clean = get_polynomial_result(ini_s['kzLarger2'].split('/'), mueff)
#         """Расчёт облачного коэффициента"""
#         kz_obl_f = get_polynomial_result(ini_s['kz_obl'].split('/'), (r23clean/r23m))
#         "Расчёт r12 скорректированный с учётом облачности"
#         r12clear = kz_obl_f*r12m
#         try:
#             o3 = round(get_ozone_by_nomographs(home, r12clear, mueff), 2)
#         except Exception as err:
#             print('Shared_: ',err)
#             o3 = -1
#
#         if channel=='Z-D':
#             curr_o3[1] = o3
#             if o3==-1 or o3==0 or o3>=600 or o3<150:
#                 o3 = 0
#             curr_o3[2] = 0
#             curr_o3[3] = 0
#             curr_o3[4] = 0
#
#         elif channel=='S-D':
#             curr_o3[2] = round(make_uv(p_uva1,p_uva2,data,ome,'uva',file_name,expo_grad,ini_s))
#             curr_o3[3] = round(make_uv(p_uvb1,p_uvb2,data,ome,'uvb',file_name,expo_grad,ini_s))
#             curr_o3[4] = round(make_uv(p_uve1,p_uve2,data,ome,'uve',file_name,expo_grad,ini_s))
#             o3 = 0
#         else:
#             o3 = 0
#     dt = {'o3':o3,'uva':curr_o3[2],'uvb':curr_o3[3],'uve':curr_o3[4],'ome':ome,'mu':mu,'amas':amas,'hg':hg}
#     return(dt)

##def ozone_uv(home,ome,data,date,time,file_name,expo_grad,channel):
##    #not use
##    """ome - чувствительность прибора"""
####    global ini_s
##    tmp1 = 0
##    tmp2 = 0
##    o3lab = ''
##    uvalab = ''
##    uvblab = ''
##    uvelab = ''
##    curr_o3 = [0,0,0,0,0]
##    file_name = os.path.basename(file_name)
####    print(file_name)
##    file_name = file_name.split('_')[1]
##    ini_s = read_ini(home,'r','')
####    nomo_s = read_nomo(home)
##    conf2 = ini_s['pix2nm'].split('/')
##    if file_name.find('Z'):
##        add = float(ini_s['zenith_add'])
##    else:
##        add = 0
##    point = ini_s['points'].split(',')
##    ##print(point)
##    p_uva1,p_uva2 = nm2pix(315,conf2,add),nm2pix(400,conf2,add)
##    p_uvb1,p_uvb2 = nm2pix(280,conf2,add),nm2pix(315,conf2,add)
##    p_uve1,p_uve2 = 0,3691 #nm2pix(290),nm2pix(420)
##    p_1 = nm2pix(float(point[0]),conf2,add)
##    p_2 = nm2pix(float(point[1]),conf2,add)
##    p_3 = nm2pix(float(point[2]),conf2,add)
##    p_4 = nm2pix(float(point[3]),conf2,add)
##    ps = [p_1,p_2,p_3,p_4]
##    p330_350 = [nm2pix(point[2],conf2,add),nm2pix(point[3],conf2,add)]
##    """    lines=[735,814,968, # I1
##              1187,1275,   # I2
##              1286,1783]   # Облачность"""
##    prom = int(ini_s['pix+-'])      # -prom (.) + prom
##    """Расчет озона"""
##    if data!=0:
##        p_mas = []
##        j = 0
##        while j<4:
##            jj = ps[j] #Points in pixels
##            p_mas.append(sredne(data[jj-prom:jj+prom+1],'ozone',3))
##            j += 1
##        """Для Санкт-Петербурга"""
##        f = float(ini_s['latitude'])
##        l = float(ini_s['longitude'])
##        digs = 3
##        """312,    332,    332,    352"""
##        p1 = 1 # 1
##        p2 = 2 # 2
##        #Не менять
##        w1 = 1      #Чувствительность линейки, уже учтена в формуле!
##        w2 = 1      #Чувствительность линейки, уже учтена в формуле!
##        pelt = int(ini_s['hour_pelt'])
##        mu, amas, hg = sunheight(f,l,time,pelt,date)
##        
##        """i1o3, i2o3 - измеренные значения
##        w1, w2 - чувствительность линейки
##        iatm1, iatm2 - внеатмосферные значения
##        alpha1, alpha2 - коэффикиент поглощения озона
##        beta1, beta2 - коэф"""i1o3, i2o3 - измеренные значения
##        w1, w2 - чувствительность линейки
##        iatm1, iatm2 - внеатмосферные значения
##        alpha1, alpha2 - коэффикиент поглощения озона
##        beta1, beta2 - коэффициент рассеивания в атмосфере
##        amas - солнечная масса
##        mu - озонная масса
##        kz - зенитный коэффициент (солнце => зенит)
##        kz_obl - облачный коэффициент
##        digs - точность вычисления озона
##        con[i] = [pix,lambda,alpha,beta,iatm]"""
##        
##        """Расчёт облачного коэффииента"""
##        p_mas2 = []
##        for i in p330_350:
##            p_mas2.append(srznach(data[i-prom:i+prom+1],'spectr'))
##        k_obl = [ini_s['kz_obl'].split('/'),p_mas2]
##        if channel=='Z-D':
##            try:
##                o3 = ozon(p_mas[0],p_mas[1],
##                          w1,w2,
##                          0,0,
##                          0,0,
##                          0,0,
##                          amas,
##                          mu,
##                          ini_s['kz'].split('/'),
##                          k_obl,
##                          3,
##                          ini_s,
##                          nomo_s)
##
##            except ZeroDivisionError:
##                print('Ошибка в файле измерений!')
##                o3 = -1
##            except Exception as err:
##                print('_Shared.ozone_uv: ',err)
##                o3 = -1фициент рассеивания в атмосфере
##        amas - солнечная масса
##        mu - озонная масса
##        kz - зенитный коэффициент (солнце => зенит)
##        kz_obl - облачный коэффициент
##        digs - точность вычисления озона
##        con[i] = [pix,lambda,alpha,beta,iatm]"""
##        
##        """Расчёт облачного коэффииента"""
##        p_mas2 = []
##        for i in p330_350:
##            p_mas2.append(srznach(data[i-prom:i+prom+1],'spectr'))
##        k_obl = [ini_s['kz_obl'].split('/'),p_mas2]
##        if channel=='Z-D':
##            try:
##                o3 = ozon(p_mas[0],p_mas[1],
##                          w1,w2,
##                          0,0,
##                          0,0,
##                          0,0,
##                          amas,
##                          mu,
##                          ini_s['kz'].split('/'),
##                          k_obl,
##                          3,
##                          ini_s,
##                          nomo_s)
##
##            except ZeroDivisionError:
##                print('Ошибка в файле измерений!')
##                o3 = -1
##            except Exception as err:
##                print('_Shared.ozone_uv: ',err)
##                o3 = -1
##            curr_o3[1] = o3
##            if o3==-1 or o3==0 or o3>=600 or o3<150:
##                o3 = 0
##            curr_o3[2] = 0
##            curr_o3[3] = 0
##            curr_o3[4] = 0
##            
##        elif channel=='S-D':
##            curr_o3[2] = round(make_uv(p_uva1,p_uva2,data,ome,'uva',file_name,expo_grad,ini_s))
##            curr_o3[3] = round(make_uv(p_uvb1,p_uvb2,data,ome,'uvb',file_name,expo_grad,ini_s))
##            curr_o3[4] = round(make_uv(p_uve1,p_uve2,data,ome,'uve',file_name,expo_grad,ini_s))
##            o3 = 0
##        else:
##            o3 = 0
##    dt = {'o3':o3,'uva':curr_o3[2],'uvb':curr_o3[3],'uve':curr_o3[4],'ome':ome,'mu':mu,'amas':amas,'hg':hg}
##    return(dt)

if __name__=='__main__':
##    home = os.getcwd()
##    file2send = 'D:\\UFOS\\Мурманск\\2015\\07\\09\\m0003.Z-D_1100_09072015.txt'
##    send_files(home,file2send)
##    conf = read_connect(home)
##    tex = to_ftp(conf['ftp_ip'],int(conf['ftp_port']),conf['ftp_path'],conf['ftp_user'],conf['ftp_pass'],'D:\\UFOS\\Мурманск\\2015\\07\\09\\m0003.Z-D_1100_09072015.txt')
##    input(tex)
    pass
##    while 1:
##        time = input('Time: ')
##        if len(time)==4:
##            time = '0' + time
##        time += '.00'
##        date = input('Date: ')
##        if date == '':
##            date = '14.08.2012'
##        f = 59.57
##        l = -30.42
##        pelt = '+4'
##        try:
##            mu,ama,h = sunheight(f,l,time,pelt,date)
##            print(round(mu,3),round(ama,3),round(h,3))
##        except:
##            break
