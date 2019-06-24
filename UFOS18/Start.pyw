import os
from time import sleep
from tkinter import *
from tkinter import ttk
from Shared_ import *

"""============== <Main> =============="""
##;0 Экспозиция
##expo=350
##;1 Порядок и тип каналов
##channel=Z
##;2 Суммирование
##accummulate=3
##;3 Усиление
##gain=0
##;4 Запуск
##set_run=S
##;5 Номер устройства
##dev_id=1
##;6 Время
##time=00:00-23:59-5
##;7 Повтор
##repeat=1
##;8 Максимальное значение линейки
##pmax=3100
##;9 Широта
##latitude=59.57
##;10 Долгота
##longitude=-30.42
##;11 Коэффициенты полинома пиксель-длина_волны
##pix2nm=-2*10**-8/0.0403/278.2
##;12 Kz - 0.1717/0.5429/1/1/1/1
##kz=0.1717/0.5429/1/1/1/1
##;13 Kz обл - dx(f(m)-lg(330/350)) = a/b/c/a1/b1/c1 = 0/311.21/6.097/0/-0.0216/0.088
##kz_obl=0/311.21/0/0/-0.0216/0.088
##;14 Коэффициенты полинома пиксель-чувствительность линейки 5*10**-7/-0.0004/0.0663
##omega=0/0/1
##;15 Высота солнца в градусах. Измерения будут проводиться при высоте солнца больше hs
##hs=7
##;16 Дополнительные линии на графике
##points=734,814,968,1187,1286,1286,1783,2863,2946
##;17 Промежуток от каждой точки, в котором берётся среднее значение
##pix+-=5
##;18 Часовой пояс
##hour_pelt=+4
##auto_exp=1
##zenith_add=1.55
##ozone_add=0
def change_params(params,inis):
##    print(inis)
##    i = 0
    for par in params:
        params[par].delete(0,100)
        params[par].insert(0,inis[par])
##        i += 1

def save_param():
    pars = {}
##    params = {'expo':expo_ent,
##            'channel':channel_ent,
##            'accummulate':accumulate_ent,
##            'gain':gain_ent,
##            'set_run':set_run_ent,
##            'dev_id':dev_id_ent,
##            'time':time_ent,
##            'repeat':repeat_ent,
##            'max':pmax_ent,
##            'latitude':latitude_ent,
##            'longitude':longitude_ent,
##            'pix2nm':pix2nm_ent,
##            'kz':k1_ent,
##            'kz_obl':kz_obl_ent,
##            'omega':omega_ent,
##            'hs':hs_ent,
##            'points':points_ent,
##            'pix+-':pix_ent,
##            'hour_pelt':hour_pelt_ent,
##            'auto_exp':auto_exp_ent,
##            'zenith_add':zenith_add_ent,
##            'ozone_add':ozone_add_ent,
##            'stn_id':stn_id_ent,
##            'R21_0':k2_ent,
##            'R34_0':k3_ent,
##            'kdX':r34b_ent,
##            'uva_koef':uva_koef_ent,
##            'uvb_koef':uvb_koef_ent,
##            'uve_koef':uve_koef_ent}
    for par in params:
        pars[par] = params[par].get()
##        print(par,params[par].get())
    inis = read_ini(os.getcwd(),'w',pars)
    for i in inis:
        print('{0} = {1}'.format(i,inis[i]))
    change_params(params,inis)

def modify_label(typ,label,entry):
    try:
        data = entry.get()
        d = data.split('/')
        if typ=='k':
            string = 'X=({0}*mu3+{1}*mu2+{2}*mu+{3})*(R12-(R34-R34b)*(1+{4}*mu))+{5}*mu3+{6}*mu2+{7}*mu+{8}-dX'.format(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8])
##            for i in data[1:]:
##                string += ' + ' + i
        elif typ=='pix2nm':
            string = 'nm = {0}*pix2+{1}*pix+{2}'.format(d[0],d[1],d[2])
##            for i in d[1:]:
##                string += ' / ' + i
        elif typ=='r34b':
            string = 'R34b = {0}*mu2-{1}*mu+{2}'.format(d[0],d[1],d[2])
    except Exception as err:
        print(err)
        string = 'ERR'
    label.configure(text=string)

class modify():
    def label_pix2nm(*event):
        modify_label('pix2nm',pix2nm_lab_check,pix2nm_ent)
        
    def label_k1(*event):
        modify_label('k',k1_lab_check,k1_ent)
        
    def label_k2(*event):
        modify_label('k',k2_lab_check,k2_ent)

    def label_k3(*event):
        modify_label('k',k3_lab_check,k3_ent)

    def label_r34b(*event):
        modify_label('r34b',r34b_lab_check,r34b_ent)

def run_mesure():
    but_start_mesure.configure(state = "disable")
    os.startfile('UFOS_3_3.py')

def run_graph():
    os.startfile('Plotter3_3.pyw')
    
main = Tk()
main.title('УФОС Запуск')
##main.geometry('800x600+200+100')
main.resizable(False, False)
t1_width = 15
t2_width = 35
a0 = ttk.Label(main, text = '')
expo_lab = ttk.Label(main, text = 'Начальная экспозиция, [мс]')
expo_ent = ttk.Entry(main,width = t1_width)
channel_lab = ttk.Label(main, text = 'Канал (ZS)')
channel_ent = ttk.Entry(main,width = t1_width)
accumulate_lab = ttk.Label(main, text = 'Суммирование (4)')
accumulate_ent = ttk.Entry(main,width = t1_width)
gain_lab = ttk.Label(main, text = 'Усиление (0)') #Не выводится на GUI
gain_ent = ttk.Entry(main,width = t1_width)
set_run_lab = ttk.Label(main, text = 'Запуск (S)') #Не выводится на GUI
set_run_ent = ttk.Entry(main,width = t1_width)
stn_id_lab = ttk.Label(main, text = 'Номер станции')
stn_id_ent = ttk.Entry(main,width = t1_width)
dev_id_lab = ttk.Label(main, text = 'Номер устройства')
dev_id_ent = ttk.Entry(main,width = t1_width)
time_lab = ttk.Label(main, text = 'Время и интервал (00.00-23.59-10)')
time_ent = ttk.Entry(main,width = t1_width)
repeat_lab = ttk.Label(main, text = 'Повтор измерений (1-Вкл, 0-Выкл)')
repeat_ent = ttk.Entry(main,width = t1_width)
pmax_lab = ttk.Label(main, text = 'Макс. значение без зашкаливания')
pmax_ent = ttk.Entry(main,width = t1_width)
hs_lab = ttk.Label(main, text = 'Начальная высота солнца,[°]')
hs_ent = ttk.Entry(main,width = t1_width)
auto_exp_lab = ttk.Label(main, text = 'Автоматическая экспозиция (1-Вкл, 0-Выкл)')
auto_exp_ent = ttk.Entry(main,width = t1_width)
latitude_lab = ttk.Label(main, text = 'Широта,[°]')
latitude_ent = ttk.Entry(main,width = t2_width)
longitude_lab = ttk.Label(main, text = 'Долгота,[°]')
longitude_ent = ttk.Entry(main,width = t2_width)
pix2nm_lab = ttk.Label(main, text = 'Коэффициенты (пиксель-длина волны)')
pix2nm_ent = ttk.Entry(main,width = t2_width)
pix2nm_lab_check = ttk.Label(main, text = '')
zenith_add_lab = ttk.Label(main, text = 'Сдвиг между каналами, [нм]')
zenith_add_ent = ttk.Entry(main,width = t2_width)
ozone_add_lab = ttk.Label(main, text = 'Прибавка к озону, [Д.е.]')
ozone_add_ent = ttk.Entry(main,width = t2_width)
k1_lab = ttk.Label(main, text = 'K1 Коэффициенты при mu > 4')
k1_ent = ttk.Entry(main,width = t2_width)
k1_lab_check = ttk.Label(main, text = '')
kz_obl_lab = ttk.Label(main, text = 'kz obl')
kz_obl_ent = ttk.Entry(main,width = t2_width)
kz_obl_lab_check = ttk.Label(main, text = '')
omega_lab = ttk.Label(main, text = 'Коэффициенты (пиксель-чувствительность)')
omega_ent = ttk.Entry(main,width = t2_width)
points_lab = ttk.Label(main, text = 'Контрольные точки')
points_ent = ttk.Entry(main,width = t2_width)
pix_lab = ttk.Label(main, text = 'Осреднение в пикселях (5)')
pix_ent = ttk.Entry(main,width = t2_width)
hour_pelt_lab = ttk.Label(main, text = 'Часовой пояс')
hour_pelt_ent = ttk.Entry(main,width = t2_width)
k2_lab = ttk.Label(main, text = 'K2 Коэффициенты при 4 > mu > 2.3')
k2_ent = ttk.Entry(main,width = t2_width)
k2_lab_check = ttk.Label(main, text = '')
k3_lab = ttk.Label(main, text = 'K3 Коэффициенты при 2.3 > mu')
k3_ent = ttk.Entry(main,width = t2_width)
k3_lab_check = ttk.Label(main, text = '')
r34b_lab = ttk.Label(main, text = 'R34b')
r34b_ent = ttk.Entry(main,width = t2_width)
r34b_lab_check = ttk.Label(main, text = '')
uva_koef_lab = ttk.Label(main, text = 'УФ-А коэффициент')
uva_koef_ent = ttk.Entry(main,width = t1_width)
uvb_koef_lab = ttk.Label(main, text = 'УФ-Б коэффициент')
uvb_koef_ent = ttk.Entry(main,width = t1_width)
uve_koef_lab = ttk.Label(main, text = 'УФ-Э коэффициент')
uve_koef_ent = ttk.Entry(main,width = t1_width)
but_save_param = ttk.Button(main,text = 'Сохранить',command = save_param)
but_start_mesure = ttk.Button(main,text = 'Начать измерения',command = run_mesure)
but_start_graph = ttk.Button(main,text = 'Просмотр',command = run_graph)

inis = read_ini(os.getcwd(),'r','') 
params = {'expo':expo_ent,
            'channel':channel_ent,
            'accummulate':accumulate_ent,
            'gain':gain_ent,
            'set_run':set_run_ent,
            'dev_id':dev_id_ent,
            'time':time_ent,
            'repeat':repeat_ent,
            'max':pmax_ent,
            'latitude':latitude_ent,
            'longitude':longitude_ent,
            'pix2nm':pix2nm_ent,
            'kz':k1_ent,
            'kz_obl':kz_obl_ent,
            'omega':omega_ent,
            'hs':hs_ent,
            'points':points_ent,
            'pix+-':pix_ent,
            'hour_pelt':hour_pelt_ent,
            'auto_exp':auto_exp_ent,
            'zenith_add':zenith_add_ent,
            'ozone_add':ozone_add_ent,
            'stn_id':stn_id_ent,
            'R21_0':k2_ent,
            'R34_0':k3_ent,
            'kdX':r34b_ent,
            'uva_koef':uva_koef_ent,
            'uvb_koef':uvb_koef_ent,
            'uve_koef':uve_koef_ent}
change_params(params,inis)

modify.label_pix2nm()
modify.label_k1()
modify.label_k2()
modify.label_k3()
modify.label_r34b()
"""============== GUI Structure =============="""
r = 0
a0.grid(row=r,column=0,sticky='we',columnspan=4)
r += 1
stn_id_lab.grid(        row=r,column=0,sticky='w')
stn_id_ent.grid(        row=r,column=1,sticky='w')
r += 1
dev_id_lab.grid(        row=r,column=0,sticky='w')
dev_id_ent.grid(        row=r,column=1,sticky='w')
##r += 1
##repeat_lab.grid(        row=r,column=0,sticky='w')
##repeat_ent.grid(        row=r,column=1,sticky='w')
r += 1
expo_lab.grid(          row=r,column=0,sticky='w')
expo_ent.grid(          row=r,column=1,sticky='w')
r += 1
channel_lab.grid(       row=r,column=0,sticky='w')
channel_ent.grid(       row=r,column=1,sticky='w')
r += 1 #4
accumulate_lab.grid(    row=r,column=0,sticky='w')
accumulate_ent.grid(    row=r,column=1,sticky='w')
r+= 1 #5
pmax_lab.grid(          row=r,column=0,sticky='w')
pmax_ent.grid(          row=r,column=1,sticky='w')
##gain_lab.grid(          row=4,column=0,sticky='w')
##gain_ent.grid(          row=4,column=1,sticky='w')
##set_run_lab.grid(       row=5,column=0,sticky='w')
##set_run_ent.grid(       row=5,column=1,sticky='w')
r += 1 #6
hs_lab.grid(            row=r,column=0,sticky='w')
hs_ent.grid(            row=r,column=1,sticky='w')
r += 1 #7
time_lab.grid(          row=r,column=0,sticky='w')
time_ent.grid(          row=r,column=1,sticky='w')
##r += 1
##auto_exp_lab.grid(      row=r,column=0,sticky='w')
##auto_exp_ent.grid(      row=r,column=1,sticky='w')
r += 1
uva_koef_lab.grid(          row=r,column=0,sticky='w')
uva_koef_ent.grid(          row=r,column=1,sticky='w')
r += 1
uvb_koef_lab.grid(          row=r,column=0,sticky='w')
uvb_koef_ent.grid(          row=r,column=1,sticky='w')
r += 1
uve_koef_lab.grid(          row=r,column=0,sticky='w')
uve_koef_ent.grid(          row=r,column=1,sticky='w')
"""====="""
r = 1
latitude_lab.grid(      row=r,column=2,sticky='w')
latitude_ent.grid(      row=r,column=3,sticky='w')
r += 1
longitude_lab.grid(     row=r,column=2,sticky='w')
longitude_ent.grid(     row=r,column=3,sticky='w')
r += 1
hour_pelt_lab.grid(     row=r,column=2,sticky='w')
hour_pelt_ent.grid(     row=r,column=3,sticky='w')
r += 1
pix2nm_lab.grid(        row=r,column=2,sticky='w')
pix2nm_ent.grid(        row=r,column=3,sticky='w')
r += 1
pix2nm_lab_check.grid(  row=r,column=2,sticky='w',columnspan=2)
r += 1
zenith_add_lab.grid(    row=r,column=2,sticky='w')
zenith_add_ent.grid(    row=r,column=3,sticky='w')
r += 1
##ozone_add_lab.grid(     row=r,column=2,sticky='w')
##ozone_add_ent.grid(     row=r,column=3,sticky='w')
points_lab.grid(        row=r,column=2,sticky='w')
points_ent.grid(        row=r,column=3,sticky='w')
r += 1
k1_lab.grid(            row=r,column=2,sticky='w')
k1_ent.grid(            row=r,column=3,sticky='w')
r += 1
k1_lab_check.grid(  row=r,column=2,sticky='w',columnspan=2)
##r += 1
##kz_obl_lab.grid(        row=r,column=2,sticky='w')
##kz_obl_ent.grid(        row=r,column=3,sticky='w')
##r += 1
##kz_obl_lab_check.grid(  row=r,column=3,sticky='w')
##r += 1 #7
##omega_lab.grid(         row=6,column=2,sticky='w')
##omega_ent.grid(         row=6,column=3,sticky='w')
##r += 1
##pix_lab.grid(           row=r,column=2,sticky='w')
##pix_ent.grid(           row=r,column=3,sticky='w')
r += 1
k2_lab.grid(         row=r,column=2,sticky='w')
k2_ent.grid(         row=r,column=3,sticky='w')
r += 1
k2_lab_check.grid(   row=r,column=2,sticky='w',columnspan=2)
r += 1
k3_lab.grid(         row=r,column=2,sticky='w')
k3_ent.grid(         row=r,column=3,sticky='w')
r += 1
k3_lab_check.grid(   row=r,column=2,sticky='w',columnspan=2)
r += 1
r34b_lab.grid(           row=r,column=2,sticky='w')
r34b_ent.grid(           row=r,column=3,sticky='w')
r += 1
r34b_lab_check.grid(   row=r,column=2,sticky='w',columnspan=2)
r += 1
but_save_param.grid(    row=r,column=0,sticky='e')
but_start_mesure.grid(  row=r,column=1,sticky='w')
but_start_graph.grid(   row=r,column=2,sticky='w')
"""============== GUI Actions =============="""
pix2nm_ent.bind('<KeyRelease>',modify.label_pix2nm)
k1_ent.bind('<KeyRelease>',modify.label_k1)
k2_ent.bind('<KeyRelease>',modify.label_k2)
k3_ent.bind('<KeyRelease>',modify.label_k3)
r34b_ent.bind('<KeyRelease>',modify.label_r34b)
##but_start.bind('<Button-1>', run)
##file_list.bind('<space>', plot_file)
##file_list.bind('<Return>', plot_file)
main.mainloop()

