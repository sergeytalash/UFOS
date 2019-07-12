import os, datetime
from PIL import ImageTk
from time import sleep
from tkinter import *
from tkinter import ttk
import tkinter.font as font2
from math import *

import numpy as np

from sys import platform as sys_pf

if sys_pf == 'darwin':
    import matplotlib

    matplotlib.use("TkAgg")
    from OLD_UFOS.UFOS18.UFOS.Shared_ import *
else:
    from Shared_ import *

import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from matplotlib import rc
from shutil import copy

if os.name != 'posix':
    import winreg

    p_sep = '\\'
else:
    p_sep = '/'

expo_grad = 1100  # Экспозиция градуировки. Сейчас не используется


class LastCalculatedOzone:
    def __init__(self):
        pass

    def get(self):
        with open("last_calculated_ozone.txt", "r") as fr:
            lines = fr.readlines()
            return _strptime(str(lines[0]).strip())

    def set(self, date_time):
        with open("last_calculated_ozone.txt", "w") as fw:
            print(_strftime(date_time), file=fw)
        return date_time


def send_all_files_plotter():
    lab_err.configure(text='')
    root.update()
    for i in os.listdir(path):
        if i.find('-D') != -1:
            file2send = os.path.join(path, i)
            tex = send_files(home, file2send)
            if tex != 'OK':
                print(tex)
            lab_err.configure(text=i + tex)
            root.update()


def check_code(*event):
    code = ent_code.get()
    if code == '9':
        obj_grid()
    else:
        change_privileges(common, 0)


def obj_grid():
    admin_panel.grid(row=1, column=0, sticky='nwe')
    rad_4096.grid(row=0, column=1, sticky='w')
    rad_ytop.grid(row=0, column=2, sticky='w')
    chk_kz_obl.grid(row=0, column=3, sticky='w')
    chk_mwt.grid(row=0, column=5, sticky='w')
    but_plot_more.grid(row=0, column=4, sticky='w')
    but_remake.grid(row=0, column=5, sticky='w')
    rad_spectr.grid(row=0, column=7, sticky='w')
    rad_o3file.grid(row=0, column=8, sticky='w')
    rad_uva.grid(row=0, column=9, sticky='w')
    rad_uvb.grid(row=0, column=10, sticky='w')
    rad_uve.grid(row=0, column=11, sticky='w')
    chk_autorefresh.grid(row=0, column=12, sticky='w')


def change_privileges(priv, on_off):
    """Скрыть сервисную панель"""
    admin_panel.grid_forget()


def get_add():
    """Добавление сдвига по длинам волн для зенитного канала"""
    global add
    file_name = file_list.selection_get()
    if file_name.find('Z') != -1 or uv.get() == 0:
        add = float(ini_s['zenith_add'])
    else:
        add = 0
    return (add)


def window_closed():
    global root
    root.quit()
    root.destroy()


def plot_more():
    global plt
    global o3_plotted
    if not o3_plotted:
        try:
            plt.close()
        except:
            pass
        try:
            x = main_func.nm
            y = main_func.data
            i = 0
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(211, axisbg='#FFFFFF')
            ax.plot(x, y, '-k')
            ax.set_ylim(-10, max(y))
            ax.set_title(main_func.date + ' ' + main_func.time)
            ax2 = fig.add_subplot(212, axisbg='#FFFFFF')
            ax2.set_ylim(-10, max(y))
            ax.grid(True)  # координатную сетку рисовать
            ax2.grid(True)  # координатную сетку рисовать
            line2, = ax2.plot(x, y, '-k')

            def onselect(xmin, xmax):
                try:
                    indmin, indmax = np.searchsorted(x, (xmin, xmax))
                    indmax = min(len(x) - 1, indmax)
                    thisx = x[indmin:indmax]
                    thisy = y[indmin:indmax]
                    line2.set_data(thisx, thisy)
                    ax2.set_xlim(thisx[0], thisx[-1])
                    ax2.set_ylim(min(thisy), max(thisy))
                    fig.canvas.draw()
                except:
                    pass

            span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                                rectprops=dict(alpha=0.2, facecolor='red'))
            plt.show()
        except:
            pass


def set_disk_but(event):
    global path
    path = disks[disk_list.current()] + ':\\'
    drive = path
    only_draw_dirs()
    refresh_txtlist(path)


def make_list():
    global disks
    if os.name == 'posix':
        disks = '/'
    else:
        alp = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        disks = []
        for i in alp:
            try:
                os.chdir(i + ':\\')
                disks.append(os.getcwd()[:1])
            except:
                pass
    return tuple(disks)


def graph_in(o3_mode, gr_ok, t, kx, ky, x, y, plotx, ploty, xshag, yshag, some_root):
    """Построение графика из кортежа данных "t"
        o3_mode - режим расчёта ozone, spectr, uva, uvb, uve
        gr_ok - режим построения графика и расчёта озона (0,1,2)
        t - кортеж t=()
        kx - коэффициент увеличения-уменьшения значений по оси х
        ky - коэффициент увеличения-уменьшения значений по оси y
        x - ширина изображения в пикселях
        y - высота изображения в пикселях
        plotx - ширина графического поля в пикселях
        ploty - высота графического поля в пикселях
        xshag - шаг сетки
        yshag - шаг сетки
        some_root - где рисовать"""
    global canvas
    global ima
    global label
    global curr_o3
    global o3min
    global o3_mod
    global o3srednee
    o3_mod = o3_mode

    def shline(xxx, b_y, e_y, smech, ypoint, mwt_smech):
        """
        - - - Пунктирные линии - - -
        xxx - положение по оси абсцисс
        smech - смещение текста вправо(1) или в лево(0)
        b_y - нижняя граница линии
        e_y - верхняя граница линии"""
        if smech == 0:
            fil = '--r'
            mov_y = 1
            if mwt_smech:
                textup = 0.09
                addmwt = 20
            else:
                textup = 0.03
                addmwt = -20
        else:
            fil = '--b'
            mov_y = -1
            if mwt_smech:
                textup = 0.09
                addmwt = 40
            else:
                textup = 0.03
                addmwt = -100
        plt.plot([xxx, xxx], [b_y, e_y], fil)
        plt.plot([xxx + 2, xxx - 2], [ypoint, ypoint], fil[1:])  # Горизонтальная линия на точке пересечения
        plt.plot([xxx - mov_y * 10, xxx], [e_y + addmwt, ypoint], fil[1:])  # Линия от значения до обозначения
        plt.plot([xxx - mov_y * 10, xxx - mov_y * 18], [e_y + addmwt, e_y + addmwt], fil[1:])  # Линия под обозначением
        plt.annotate(round(ypoint), (xxx - mov_y * 14 + 2, e_y + addmwt), ha='right',
                     va='center', bbox=dict(fc='white', ec='none'))  # Обозначение

    """==============================================================="""
    graph_in.tmp1 = 0
    graph_in.tmp2 = 0
    mx = 40
    my = 20
    xmax = plotx + mx * 2
    ymax = ploty + my * 3
    o3lab = ''
    uvalab = ''
    uvblab = ''
    uvelab = ''
    ini_s = read_ini(home, 'r', '')
    if main_func.time:
        curr_time.append(int(main_func.time[:-6]))
        for i in curr_time:
            while curr_time.count(i) > 1:
                curr_time.remove(i)
    if gr_ok != 0:
        if curr_time != []:
            ppp = max(curr_time) - min(curr_time) + 1
        try:
            for im in ima:
                canvas.delete(im)
            canvas.delete(ALL)
            ima = []

        except AttributeError as normal:
            pass
        except Exception as err:
            print('plotter. canvas delete - ', err)
        """Построение линий сетки"""
        xline = mx
        v = var.get()
        minutes = 0
        xshag24 = plotx / 24
        if o3_mode != 'spectr':
            """Построение вертикальных линий и подписей к ним"""
            """Шкала времени"""
            while xline <= plotx + mx:
                ima.append(canvas.create_line((xline, my, xline, ploty + my), fill='grey'))
                if v == 0:
                    ima.append(canvas.create_text(xline, ploty + my + 10, text=str(minutes // 30), fill='black'))
                    xline += xshag24
                else:
                    if minutes % 60 == 0:
                        text_time = str(minutes // 60 + curr_time[0]) + ':00'
                    ima.append(canvas.create_text(xline, ploty + my + 10, text=text_time, fill='black'))
                    xline += plotx // ppp
                minutes += 60

            """Построение горизонтальных линий и подписей к ним"""
            """Шкала озона"""
            yline = ploty + my
            while yline >= my:
                ima.append(
                        canvas.create_line((mx, ploty + 2 * my - yline, plotx + mx, ploty + 2 * my - yline),
                                           fill='grey'))
                ima.append(
                        canvas.create_text(mx - 15, ploty + 2 * my - yline, text=str(round((yline - my) / ky + o3min)),
                                           fill='black'))
                yline -= yshag * 2
            ima.append(canvas.create_text(plotx + mx, ploty + my * 2 + 5, text='время', fill='black'))
    if gr_ok != 1:
        mov2 = 10
        plt.plot([0, 0], [0, 0], '.')
        if o3_mode == 'ozone' or o3_mode == 'spectr':
            """Расчет озона"""
            prom = int(main_func.inis['pix+-'])  # -prom (.) + prom
            if t != 0 and main_func.data != None:
                p_mas = []
                j = 0
                while j < 4:
                    jj = ps[j]  # Points in pixels
                    p_mas.append(sredne(main_func.data[jj - prom:jj + prom + 1], 'ozone', 3))
                    j += 1
                """Для Санкт-Петербурга"""
                f = float(main_func.inis['latitude'])
                l = float(main_func.inis['longitude'])
                digs = 3
                """312,    332,    332,    352"""
                p1 = 1  # 1
                p2 = 2  # 2
                # Не менять
                w1 = 1  # Чувствительность линейки, уже учтена в формуле!
                w2 = 1  # Чувствительность линейки, уже учтена в формуле!
                pelt = int(ini_s['hour_pelt'])
                try:
                    mu = main_func.mu_amas_hs[0]
                    amas = main_func.mu_amas_hs[1]
                    hg = main_func.mu_amas_hs[2]
                except:
                    mu, amas, hg = sunheight(f, l, main_func.time, pelt, main_func.date)
                lab_sun.configure(text='Высота Cолнца: ' + str(hg) + '° (mu={0})'.format(round(mu, 3)))
                """i1o3, i2o3 - измеренные значения
                w1, w2 - чувствительность линейки
                iatm1, iatm2 - внеатмосферные значения
                alpha1, alpha2 - коэффикиент поглощения озона
                beta1, beta2 - коэффициент рассеивания в атмосфере
                amas - солнечная масса
                mu - озонная масса
                kz - зенитный коэффициент (солнце => зенит)
                kz_obl - облачный коэффициент
                digs - точность вычисления озона
                con[i] = [pix,lambda,alpha,beta,iatm]"""
                """Расчёт облачного коэффициента"""
                p_mas2 = []
                v = var.get()
                if v != 2:
                    for i in p330_350:
                        p_mas2.append(srznach(main_func.data[i - prom:i + prom + 1], 'spectr'))
                    kz_obl_f.value = chk_var.get()
                    k_obl = [ini_s['kz_obl'].split('/'), p_mas2]
                else:
                    kz_obl = 0
                # Расчет озона
                o3 = 0
                curr_o3[2] = 0
                curr_o3[3] = 0
                curr_o3[4] = 0
                if main_func.channel == 'Z-D':
                    try:
                        o3 = ozon(p_mas[0], p_mas[1],
                                  w1, w2,
                                  0, 0,
                                  0, 0,
                                  0, 0,
                                  amas,
                                  mu,
                                  ini_s['kz'].split('/'),
                                  k_obl,
                                  3,
                                  ini_s)
                    except ZeroDivisionError:
                        print('Ошибка в файле измерений!')
                        o3 = -1
                    except Exception as err:
                        print('Plotter: ', err)
                        o3 = -1
                    curr_o3[1] = o3
                    main_func.ozone = o3
                    if o3 == -1 or o3 == 0 or o3 == 600 or o3 < o3min or o3 > ozon_scale_max:
                        o3lab = str(o3) + '*'
                    else:
                        o3lab = str(o3)
                elif main_func.channel == 'S-D':
                    if o3_mode == 'spectr':
                        curr_o3[2] = round(
                            make_uv(p_uva1, p_uva2, main_func.data, ome, 'uva', file_name, expo_grad, ini_s))
                        curr_o3[3] = round(
                            make_uv(p_uvb1, p_uvb2, main_func.data, ome, 'uvb', file_name, expo_grad, ini_s))
                        curr_o3[4] = round(
                            make_uv(p_uve1, p_uve2, main_func.data, ome, 'uve', file_name, expo_grad, ini_s))

                curr_o3[1] = o3
                uvalab = str(curr_o3[2])
                uvblab = str(curr_o3[3])
                uvelab = str(curr_o3[4])
                main_func.ozone = o3
                main_func.uva = uvalab
                main_func.uvb = uvblab
                main_func.uve = uvelab

        elif o3_mode == 'uva' and t != 0 and main_func.data != None:
            curr_o3[2] = round(make_uv(p_uva1, p_uva2, main_func.data, ome, o3_mode, file_name, expo_grad, ini_s))
            o3lab = str(main_func.date)
        elif o3_mode == 'uvb' and t != 0 and main_func.data != None:
            curr_o3[3] = round(make_uv(p_uvb1, p_uvb2, main_func.data, ome, o3_mode, file_name, expo_grad, ini_s))
            o3lab = str(main_func.date)
        elif o3_mode == 'uve' and t != 0 and main_func.data != None:
            curr_o3[4] = round(make_uv(p_uve1, p_uve2, main_func.data, ome, o3_mode, file_name, expo_grad, ini_s))
            o3lab = str(main_func.date)
        curr_o3[0] = main_func.time
    """Построение графика"""
    if t != 0 and gr_ok != 0:
        if o3_mode == 'spectr':
            """График спектра"""
            fig2 = plt.figure()
            fig2.set_size_inches(plotx / 80, ploty / 80)
            fig2.set_dpi(75)
            ax = fig2.add_subplot(111)
            ma_y = []
            if v == 0:
                for i in range(0, 4096, 200):
                    ma_y.append(i)
                ax.set_ylim(0, 4096)
            else:
                max_t_data = round(max(t['data']))
                if max_t_data > 200:
                    for i in range(0, round(max(t['data']) + 100), 200):
                        ma_y.append(i)
                    ax.set_ylim(0, round(max(t['data'])) + 100)
                else:
                    for i in range(0, round(max(t['data']) + 50), 10):
                        ma_y.append(i)
                    ax.set_ylim(0, round(max(t['data'])) + 50)
            nnm = main_func.nm
            ax.grid(True)  # координатную сетку рисовать

            ax.set_yticks(ma_y)
            rc('xtick', labelsize=12, color='#000000', direction='in')  # x tick labels
            rc('ytick', labelsize=12, color='#000000', direction='in')  # x tick labels
            rc('lines', lw=0.6, color='#000000')  # thicker black lines
            rc('grid', color='#000000', lw=0.5)  # solid gray grid lines
            rc('text', color='#000000')
            rc('axes', labelcolor='#000000')  # axes сolor

            """Oтображение в длинах волн"""
            ma_x = []
            for i in range(0, len(t['data']), 10):
                ma_x.append(i)
            ax.set_xticks(ma_x)  # Интервал между значениями по оси х
            ax.set_xlim(min(nnm), max(nnm))
            ax.plot(nnm, t['data'], '-k')
            """//\ /\ /\ /\ /\\"""

            """Построение дополнительных линий, подписей к ним и значения пересечения с графиком"""
            if point != ['']:
                ss = 0
                mwt_smech = chk_var_mwt.get()
                for i in point:
                    xxx = nm2pix(i, conf2, add)
                    if v == 0:
                        shline(pix2nm(main_func.inis['pix2nm'].split('/'), xxx, 1, add), 0, 100, ss, t['data'][xxx],
                               mwt_smech)
                    else:
                        shline(pix2nm(main_func.inis['pix2nm'].split('/'), xxx, 1, add), 0, round(max(t['data'])), ss,
                               t['data'][xxx], mwt_smech)
                    if ss == 0:
                        ss = 1
                    else:
                        ss = 0
            ax.set_xlabel('nm')
            if chk_var_mwt.get() == 0:
                ax.set_ylabel('mV')
            else:
                ax.set_ylabel('mWt/m2*nm')
            image_fig_path = os.path.join(home, 'fig.png')
            try:
                label.destroy()
            except:
                pass
            try:
                plt.savefig(image_fig_path, bbox_inches='tight', pad_inches=0, dpi=100)
                plt.close()
                photoimage = ImageTk.PhotoImage(file=image_fig_path)
                label = ttk.Label(some_root, image=photoimage)
                label.image = photoimage
                ima.append(canvas.create_image(xmax // 2, ymax, anchor='s', image=photoimage))
            except:
                pass
            canvas.bind('<Button-1>', dirs_window_destroy)
        elif o3_mode == 'uva':
            uvalab = plot_uv(v, t, curr_time, canvas, plotx, ploty, kx, ky, mx, my, o3_mode)
        elif o3_mode == 'uvb':
            uvblab = plot_uv(v, t, curr_time, canvas, plotx, ploty, kx, ky, mx, my, o3_mode)
        elif o3_mode == 'uve':
            uvelab = plot_uv(v, t, curr_time, canvas, plotx, ploty, kx, ky, mx, my, o3_mode)
        elif o3_mode == 'ozone':
            """График озона"""
            r = 3
            if v == 0:
                for i in range(0, len(t['data'])):
                    try:
                        color = t['color'][i]
                        point1x = round((int(t['time'][i][:2]) + int(t['time'][i][3:5]) / 60) / 24 * plotx)
                        point1y = round(t['data'][i] * ky - o3min * ky)
                        point2x = round((int(t['time'][i + 1][:2]) + int(t['time'][i + 1][3:5]) / 60) / 24 * plotx)
                        point2y = round(t['data'][i + 1] * ky - o3min * ky)
                        ima.append(canvas.create_oval(point1x + mx - r, ploty - point1y + my - r, point1x + mx + r,
                                                      ploty - point1y + my + r, outline=color))
                    except:
                        pass
            elif v == 1 or v == 2:
                ppp = max(curr_time) - min(curr_time) + 1
                for i in range(0, len(t['data'])):
                    try:
                        color = t['color'][i]
                        point1x = round(
                                ((int(t['time'][i][:2]) + int(t['time'][i][3:5]) / 60) - min(curr_time)) / ppp * plotx)
                        point1y = round(t['data'][i] * ky - o3min * ky)
                        point2x = round(((int(t['time'][i + 1][:2]) + int(t['time'][i + 1][3:5]) / 60) - min(
                                curr_time)) / ppp * plotx)
                        point2y = round(t['data'][i + 1] * ky - o3min * ky)
                        if color == 'black':
                            ima.append(canvas.create_oval(point1x + mx - r, ploty - point1y + my - r, point1x + mx + r,
                                                          ploty - point1y + my + r, outline=color, fill=color))
                    except:
                        pass
            """Расчет среднего значения озона"""
            ozone_t = []
            ji = 0
            while ji < len(t['data']):
                if t['color'][ji] == 'black':
                    ozone_t.append(t['data'][ji])
                ji += 1
            o33 = srznach(ozone_t, 'ozone')
            o3lab = str(o33)
            if o3lab != '':
                o3srednee = o3lab
            o3sred = ploty - o33 * ky + o3min * ky + my
            ima.append(canvas.create_line((mx, o3sred, plotx + mx, o3sred), fill='blue'))
            ima.append(canvas.create_text(plotx + mx + 15, o3sred, text=o3lab, fill='blue'))
            if o3_mode == 'ozone':
                lab_ozon.configure(text='Дата: {1}\nЗначение озона: {0}'.format(o3srednee, main_func.date))

    """Вывод даты"""
    if main_func.date and main_func.time:
        ima.append(canvas.create_text(mx * 3, ploty + my * 2 + 2, text=str(main_func.date) + ' ' + str(main_func.time),
                                      fill='black'))
    if gr_ok != 0:
        canvas.configure(width=xmax - 10, height=ymax)
        canvas.grid(column=0, row=0, sticky='nwse', padx=1, pady=1)

    dt = {'o3lab': o3lab, 'uvalab': uvalab, 'uvblab': uvblab, 'uvelab': uvelab}
    return dt


# ==============================================================================================================================

class Ozone:
    def __init__(self, home):
        self.inis = read_ini(home, 'r', '')
        self.home = home
        self.conf2 = self.inis['pix2nm'].split('/')
        self.kz = self.inis['kz'].split('/')
        self.prom = int(self.inis['pix+-'])  # -prom (.) + prom
        self.latitude = float(self.inis['latitude'])
        self.longitude = float(self.inis['longitude'])
        self.pelt = int(self.inis['hour_pelt'])
        self.kz_obl = self.inis['kz_obl'].split('/')
        self.data = None
        self.date = None
        self.time = None
        self.ozone = 0
        self.uva = 0
        self.uvb = 0
        self.uve = 0
        self.mu_amas_hs = []
        self.nm = []
        self.channel = []

    def main_func_2(self, file, o3_mode='ozone'):
        """Построение графика из файла
        file            - исходный файл
        kx, ky          - коэффициенты изменения отображения графика
        plotx, ploty    - размеры окна
        xshag, yshag    - шаг сетки
        """
        allinfo = readfile(file)  # new main_func
        if allinfo.get('data'):
            self.data = allinfo['data']
            self.date = allinfo['date']
            self.time = allinfo['time']
            self.mu_amas_hs = allinfo['mu_amas_hs']
            self.nm = allinfo['nm']
            self.channel = allinfo['channel']
            dt = self.graph_in2(allinfo, o3_mode)
            return dt

    def graph_in2(self, t, o3_mode='ozone'):
        """Построение графика из кортежа данных "t"
            o3_mode - режим расчёта ozone, spectr, uva, uvb, uve
            gr_ok - режим построения графика и расчёта озона (0,1,2)
            t - кортеж t=()"""
        # curr_o3 = [0, 0, 0, 0, 0]
        if o3_mode == 'ozone':
            """Расчет озона"""

            if t and self.data:
                p_mas = []
                j = 0
                while j < 4:
                    jj = ps[j]  # Points in pixels
                    p_mas.append(sredne(self.data[jj - self.prom:jj + self.prom + 1], 'ozone', 3))
                    j += 1
                """312,    332,    332,    352"""
                p1 = 1  # 1
                p2 = 2  # 2
                # Не менять
                w1 = 1  # Чувствительность линейки, уже учтена в формуле!
                w2 = 1  # Чувствительность линейки, уже учтена в формуле!

                try:
                    mu = self.mu_amas_hs[0]
                    amas = self.mu_amas_hs[1]
                    hg = self.mu_amas_hs[2]
                except:
                    mu, amas, hg = sunheight(self.latitude, self.longitude, self.time, self.pelt, self.date)
                """i1o3, i2o3 - измеренные значения
                w1, w2 - чувствительность линейки
                iatm1, iatm2 - внеатмосферные значения
                alpha1, alpha2 - коэффикиент поглощения озона
                beta1, beta2 - коэффициент рассеивания в атмосфере
                amas - солнечная масса
                mu - озонная масса
                kz - зенитный коэффициент (солнце => зенит)
                kz_obl - облачный коэффициент
                digs - точность вычисления озона
                con[i] = [pix,lambda,alpha,beta,iatm]"""
                """Расчёт облачного коэффициента"""
                p_mas2 = []
                for i in p330_350:
                    p_mas2.append(srznach(self.data[i - self.prom:i + self.prom + 1], 'spectr'))
                k_obl = [self.kz_obl, p_mas2]
                # Расчет озона
                if self.channel == 'Z-D':
                    try:
                        o3 = ozon(p_mas[0], p_mas[1],
                                  w1, w2,
                                  0, 0,
                                  0, 0,
                                  0, 0,
                                  amas,
                                  mu,
                                  self.kz,
                                  k_obl,
                                  3,
                                  self.inis)
                        dt = {'date': self.date,
                              'o3': o3,
                              'time': self.time,
                              'datetime': datetime.datetime.strptime('{} {}'.format(self.date, self.time),
                                                                     '%d.%m.%Y %H:%M:%S')}
                        return dt
                    except ZeroDivisionError:
                        print('Ошибка в файле измерений!')
                    except Exception as err:
                        print('Plotter: ', err)


def save_csv(path, headers, data, new=True, file_name_text=""):
    if file_name_text == []:
        file_name_text = _strftime(datetime.datetime.now())
    out_name = os.path.join(path, '{}{}.csv'.format(headers[1], file_name_text))
    if not os.path.exists(out_name) or new:
        with open(out_name, 'w') as fw:
            print(';'.join(headers), file=fw)
            for line in data:
                print(';'.join([str(i) for i in line]), file=fw)
    else:
        with open(out_name, 'a') as fa:
            for line in data:
                print(';'.join([str(i) for i in line]), file=fa)
    return out_name


def bit_change():
    global bit
    if bit == 0:
        bit = 1
    else:
        bit = 0


def b_remake():
    """Добавление в файл mu, amas, hs"""
    global bit
    bit = 1
    files = make_txt_list(path)
    filesZD = []
    for i in files:
        if i.count('Z-D') > 0:
            filesZD.append(i)
    os.chdir(path)
    i = 0
    j = 1
    but_remake.config(command=bit_change)
    while i < len(filesZD) and bit == 1:
        file_old = os.path.join(path, filesZD[i])
        file_new = os.path.join(path, '{0}.txt'.format(j))
        shutil.copy(file_old, file_new)
        but_remake.config(text='{0}/{1}'.format(j, len(filesZD)))
        i += 1
        j += 1
        root.update()
    but_remake.config(command=b_remake)
    but_remake.config(text='Новый формат Z-D')
    refresh_txtlist(path)


def analyze(text1, file):
    tmp = 0
    len_t = len(text1)
    while tmp < 100:
        text = file.readline()
        if text[:len_t] == text1:
            txt = text.split('=')[1].split('\n')[0]
            return (txt)
        tmp += 1
    return 0


def readfile(f):
    global home
    """Чтение файла с данными"""
    allinfo = {}
    text = ''
    txt = ''
    tmp = 0
    tmp2 = ''
    try:
        file = open(f, 'r')
        for i in range(2):
            text = file.readline()
            if text[:12] == ';Measurement':
                if text[33:34] == '-':
                    # Z-D, S-D
                    allinfo['channel'] = text[32:35]
                    allinfo['date'] = text[44:54]
                    allinfo['time'] = text[63:71]
                else:
                    # Z, S, D
                    allinfo['channel'] = text[32:33]
                    allinfo['date'] = text[42:52]
                    allinfo['time'] = text[61:69]
        file.seek(0)
        allinfo['expo'] = analyze('Exposure', file)
        if allinfo['expo'] == 0:
            file.seek(0)
            allinfo['expo'] = analyze('StartInterval', file)
        if allinfo['expo'] == 0:
            allinfo['expo'] = 'Нет\n'
        file.seek(0)
        allinfo['summ'] = analyze('Accummulate', file)
        if allinfo['summ'] == 0:
            file.seek(0)
            allinfo['summ'] = analyze('NumberOfScan', file)
        if allinfo['summ'] == 0:
            allinfo['summ'] = 'Нет\n'
        file.seek(0)
        allinfo['temp'] = analyze('Temperature', file)
        file.seek(0)
        allinfo['gain'] = analyze('Gain', file)
        file.seek(0)
        allinfo['mu_amas_hs'] = find_mu_amas_hs(file)
        mu_amas_hs = allinfo['mu_amas_hs']
        file.seek(0)
        while tmp < 100 and text != '[Value]\n':
            text = file.readline()
            tmp += 1
        tmp = 0
        allinfo['data'] = []
        allinfo['index'] = []
        allinfo['nm'] = []
        string = ''
        mmo = '1'
        while mmo != '':
            mmo = file.readline()
            string += mmo
        file.close()
        tmp2 = string.split('\n')
        index = 0
        for iii in tmp2:
            try:
                # float_number
                allinfo['data'].append(float(iii))
                allinfo['index'].append(int(index))
                if gr_ok != 0:
                    allinfo['nm'].append(pix2nm(main_func.inis['pix2nm'].split('/'), int(index), 2, add))
                index += 1
            except:
                pass
        # Расчет mu amas hs при отсутствии их в файле
        if allinfo['mu_amas_hs'] == 0:
            ot = ozone_uv(home, ome, allinfo['data'], allinfo['date'], allinfo['time'], expo_grad, allinfo['channel'])
            allinfo['mu_amas_hs'] = [ot['mu'], ot['amas'], ot['hg'], ot['o3'], ot['uva'], ot['uvb'], ot['uve']]
        if allinfo['data'] == []:
            allinfo = None
    except Exception as err:
        print('plotter.readfile() - ', err)
        print(tmp2)
        if tmp == 0:
            allinfo = None
        else:
            allinfo = 0
    finally:
        return allinfo


def ind_d(allinfo, plotx):
    t0 = allinfo['data']
    t1 = allinfo['index']
    t_1 = allinfo['nm']
    n = 1
    t2 = {}
    t2['data'] = []
    t2['index'] = []
    t2['nm'] = []
    i = 0
    while i < len(t0):
        t2['data'].append(t0[i])
        t2['index'].append(t1[i])
        if gr_ok != 0:
            t2['nm'].append(t_1[i])
        i += n
    return t2


def get_uv_letter(o3_mode):
    a = o3_mode[-1]
    if a == 'a':
        a = 'A'
    elif a == 'b':
        a = 'Б'
    elif a == 'e':
        a = 'Э'
    else:
        a = 'err'
    return (a)


def main_func(color, o3_mode, gr_ok, file1, kx, ky, plotx, ploty, xshag, yshag, some_root):
    """Построение графика из файла
    file            - исходный файл
    kx, ky          - коэффициенты изменения отображения графика
    plotx, ploty    - размеры окна
    xshag, yshag    - шаг сетки
    """
    global currnt_data
    global home
    global conf2
    global o3srednee
    main_func.inis = read_ini(home, 'r', '')
    conf2 = main_func.inis['pix2nm'].split('/')
    main_func.data = None
    main_func.date = None
    main_func.time = None
    main_func.ozone = 0
    main_func.uva = 0
    main_func.uvb = 0
    main_func.uve = 0
    main_func.mu_amas_hs = 0
    currnt_data.configure(text='')
    lab_err.configure(text='')
    lab_uva.configure(text='')
    lab_uvb.configure(text='')
    lab_uve.configure(text='')
    if file1 != 0 and main_func.inis != None:
        allinfo = readfile(file1)
        if allinfo['data']:
            main_func.data = allinfo['data']
            main_func.date = allinfo['date']
            main_func.time = allinfo['time']
            main_func.mu_amas_hs = allinfo['mu_amas_hs']
            main_func.nm = allinfo['nm']
            main_func.channel = allinfo['channel']
            t = allinfo
            ymax = round(max(t['data']) + min(t['data']))
            if ymax == 0 or ymax < 350:
                ymax = 350
            xmax = len(t['data'])
            if kx == -1 or kx == 0:
                kx = xmax / plotx
                xshag = plotx / xshag
            x = xmax
            if ky == -1:
                ky = ploty / 4096
                yshag = ploty / yshag
            elif ky == 0:
                ky = ploty / ymax
                yshag = ploty / yshag
            y = ymax
            dt = graph_in(o3_mode, gr_ok, t, kx, ky, x, y, plotx, ploty, xshag, yshag, some_root)
            if dt['o3lab']:
                if dt['o3lab'].find('.') != -1:
                    tex = 'Дата: {0}\nУФ-{1}'.format(dt['o3lab'], get_uv_letter(o3_mode))
                else:
                    tex = 'Дата: {1}\nЗначение озона: {0}'.format(dt['o3lab'], main_func.date)
                main_func.ozone = dt['o3lab']
                main_func.uva = dt['uvalab']
                main_func.uvb = dt['uvblab']
                main_func.uve = dt['uvelab']
            else:
                tex = 'Дата: {1}\nЗначение озона: {0}'.format(dt['o3lab'], main_func.date)
            lab_ozon.configure(text=tex)
    elif file1 == 0:
        refresh_txtlist(path)
        dir_list.opened = False
        ky = ploty / 4096
        kx = 1
        dt = graph_in(o3_mode, gr_ok, 0, kx, ky, 0, 0, plotx, ploty, xshag, yshag, some_root)
        allinfo = None
    else:
        allinfo = None
    lab_uva.configure(text='Значение УФ-А: {0}'.format(dt['uvalab']))
    lab_uvb.configure(text='Значение УФ-Б: {0}'.format(dt['uvblab']))
    lab_uve.configure(text='Значение УФ-Э: {0}'.format(dt['uvelab']))
    return (allinfo)


def make_txt_list(directory):
    global file_list
    txtfiles = []
    try:
        old_selection = file_list.curselection()[0]
    except:
        old_selection = 0
    try:
        for files in os.listdir(directory):
            if (files[-3:] == 'txt' and
                    files[0] in 'mp' and
                    (((files[4] == '.' and files[5] in 'ZDS')
                      or (files[5] == '.' and files[6] in 'ZDS')) or files[1] in 'ZDS')):
                txtfiles.append(files)
        file_list.delete(0, END)
        for i in sorted(txtfiles):
            file_list.insert(END, i)
        file_list.selection_set(old_selection)
        file_list.see(old_selection)
    except:
        pass
    return txtfiles


def plot_file(*event):
    global ida
    global o3_plotted
    global color
    global ok
    global add
    get_add()
    if ida != '' or ok == 0:
        canvas.after_cancel(ida)
        ida = ''
    geom = root.geometry().split('+')[0].split('x')
    plotx = int(geom[0]) - 280
    ploty = int(geom[1]) - 150
    lab_currnt_data.configure(text='Данные: ')
    ok = plot_file_xy(color, plotx, ploty)
    o3_plotted = 0


def plot_file_xy(color, plotx, ploty):
    """Если kx = 0, то график строится по ширине окна,
       Если ky = 0, то график строится по высоте окна,
       Если ky - ненулевое число, то график строится
       до значения ky
    """
    global ok
    global file_name
    for i in buttons:
        i.configure(state=DISABLED)
    root.update()
    uv.set(4)
    v = var.get()
    if v == 0:
        kx = - 1
        ky = - 1
    elif v == 1 or v == 2:
        kx = 0
        ky = 0
    gr_ok = 2
    xshag = 15  # Количество делений равно plotx/xshag
    yshag = 20  # Количество делений равно ploty/yshag
    try:
        d1 = file_list.selection_get()
        file_name = d1.split('_')[1]
        file = os.path.join(path, d1)
        allinfo = main_func(color, 'spectr', gr_ok, file, kx, ky, plotx, ploty, xshag, yshag, right_panel)
        if allinfo == 0:
            currnt_data.configure(text='== ! ==\nНужен новый формат файлов\n')
        elif allinfo == None:
            currnt_data.configure(text='== ! ==\nВ этом файле измерений\nне найдено')
        else:
            data = ('Канал: ' + allinfo['channel']
                    + '\nВремя: ' + allinfo['time']
                    + '\nДата: ' + allinfo['date']
                    + '\nТемпература: ' + allinfo['temp']
                    + '\nЭкспозиция: ' + allinfo['expo']
                    + '\nЧисло суммирований: ' + allinfo['summ'])
            currnt_data.configure(text=data)
        ok = 1
    except Exception as err:
        ok = 0
        print('plot_file_xy(): ', err)
    finally:
        for i in buttons:
            i.configure(state=NORMAL)
        return (ok)


def change_dir(event):
    global dirs_list
    global path
    global last_dir
    d1 = dirs_list.selection_get()
    if os.path.isdir(os.path.join(path, d1)):
        if len(last_dir) > 0:
            if d1 == '..':
                if len(last_dir) > 1:
                    path = last_dir.pop()  # Возврат на одну директорию вверх
                else:
                    path = last_dir[0]
            elif d1 == '' or d1 == None:
                path = last_dir[-1]
            else:
                if path != last_dir[0]:
                    last_dir.append(path)  # Сохранение текущей директории "last_dir"
                path = os.path.join(path, d1)  # Создание абсолютного пути
        else:
            path = drive
            last_dir.append(drive)
    try:
        new_dirs = os.listdir(path)
    except Exception as err:
        new_dirs = os.listdir(drive)
    dirs_list.delete(0, END)
    dirs_list.insert(END, '..')
    dirs_list.selection_set(0)
    for i in sorted(new_dirs):
        if os.path.isdir(os.path.join(path, i)):
            dirs_list.insert(END, i)
    refresh_txtlist(path)


def change_mwt_dir():
    global last_path
    global path
    global o3_mode

    class sdi():
        def add(path_loc):
            new_path = path_loc.replace(r'\UFOS', r'\UFOS\SDI')
            return (new_path)

        def remove(path_loc):
            new_path = path_loc.replace(r'\SDI', r'')
            return (new_path)

    uv_get = uv.get()
    chk_var_mwt_get = chk_var_mwt.get()
    if uv_get == 4:  # Spectr
        if chk_var_mwt_get:  # chk_mwt = 1
            if path.find('SDI') == -1:  # Есть SDI
                path = sdi.add(path)
                chk_var_mwt.set(1)
        else:  # chk_mwt = 0
            if path.find('SDI') != -1:  # Есть SDI
                path = sdi.remove(path)
                chk_var_mwt.set(0)
    elif uv_get == 0:  # Ozon
        if path.find('SDI') != -1:  # Есть SDI
            path = sdi.remove(path)
            chk_var_mwt.set(0)
    elif uv_get in [1, 2, 3]:  # UV
        if path.find('SDI') == -1:  # Есть SDI
            path = sdi.add(path)
            chk_var_mwt.set(1)
    refresh_txtlist(path)
    last_path = read_path(home, path, 'w')
    return (path)


def refresh_txtlist(path):
    global last_path
    global lab_path
    if os.path.isdir(path):
        make_txt_list(path)
        if len(path) > 70:
            path2 = last_dir[0] + '..  ..' + path[-65:]
        else:
            path2 = path
        if last_path != path:
            last_path = read_path(home, path, 'w').split('\n')[0]
        lab_path.configure(text=path2)


def only_draw_dirs():
    global dirs_list
    global last_dir
    global path
    last_dir = []
    try:
        old_selection = file_list.curselection()[0]
    except:
        old_selection = 0
    try:
        new_dirs = os.listdir(path)
    except:
        new_dirs = os.listdir(drive)
    dirs_list.delete(0, END)
    dirs_list.insert(END, '..')
    dirs_list.selection_set(old_selection)
    dirs_list.see(old_selection)
    for i in sorted(new_dirs):
        if os.path.isdir(os.path.join(path, i)):
            dirs_list.insert(END, i)
    t = path.split(p_sep)
    t2 = t[0] + p_sep
    last_dir.append(t2)
    i = 1
    while i < len(t) - 1:
        t2 = os.path.join(t2, t[i])
        last_dir.append(t2)
        i += 1


def dir_list_show(*event):
    if dir_list.opened:
        dir_list.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list.opened = False
    else:
        dir_list(path)
        refresh_txtlist(path)
        dir_list.opened = True


def dirs_window_destroy(*event):
    if dir_list.opened:
        dir_list.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list.opened = False


def dir_list(set_dir):
    global dirs_list
    global disk_list
    dir_list.dirs_window = Toplevel()
    dir_list.opened = True
    dir_list.dirs_window.deiconify()
    dir_list.dirs_window.title('Каталог')
    dir_list.dirs_window.protocol('WM_DELETE_WINDOW', dirs_window_destroy)
    geom = root.geometry().split('+')
    AxB = '150x320+'
    dA, dB = 25, 65
    dir_list.dirs_window.geometry('{0}{1}+{2}'.format(AxB, int(geom[1]) + dA, int(geom[2]) + dB))
    dir_list.dirs_window.resizable(False, False)
    lab_disk = ttk.Label(dir_list.dirs_window, text='Выбор диска:')
    disk_list = ttk.Combobox(dir_list.dirs_window, values=make_list(), width=6)
    lab_dir = ttk.Label(dir_list.dirs_window, text='Выбор каталога:')
    dirs_list = Listbox(dir_list.dirs_window, selectmode=SINGLE, height=15)
    scrs_lefty = ttk.Scrollbar(dir_list.dirs_window, command=dirs_list.yview)
    dirs_list.configure(yscrollcommand=scrs_lefty.set)
    lab_disk.grid(row=0, column=0, sticky='nwse', padx=1, pady=1)
    disk_list.grid(row=1, column=0, sticky='we')
    lab_dir.grid(row=2, column=0, sticky='nwse', padx=1, pady=1)
    dirs_list.grid(row=3, column=0, sticky='nwe', padx=1, pady=1)
    scrs_lefty.grid(row=3, column=1, sticky='nws')
    disk_list.bind('<<ComboboxSelected>>', set_disk_but)
    dirs_list.bind('<Double-Button-1>', change_dir)
    dirs_list.bind('<Double-space>', change_dir)
    dirs_list.bind('<Return>', change_dir)
    only_draw_dirs()


def refresh():
    refresh_txtlist(path)


def normalize(mdhminute):
    text = str(mdhminute)
    if len(text) == 1:
        text = '0' + text
    return (text)


def after_o3file():
    global ida
    global path
    global tmp_path
    ida = ''
    if chk_var_auto.get():
        tmp_path = path
        with open(os.path.join(home, 'outbox.txt'), 'r') as f:
            data = f.readline()
            data = data.split()[0].split('-')
            path = os.path.join(home, data[0], data[1], data[2])
    refresh_txtlist(path)
    make_o3file()


def _strptime(string):
    return datetime.datetime.strptime(string, "%Y{0}%m{0}%d".format(p_sep))


def _strftime(date_time):
    return datetime.datetime.strftime(date_time, "%Y{0}%m{0}%d".format(p_sep))


def count_files(home, last_calculated_o3_date):
    working_files = 0
    out = False
    for top, dirs, nondirs in os.walk(home):
        for file in nondirs:
            if file.count("Z-D") > 0:
                a = _strptime(os.path.join(*top.split(p_sep)[-3:]))
                b = last_calculated_o3_date
                if a <= b:
                    out = True
                    break
                else:
                    working_files += 1
        if out:
            out = False
            continue
    return working_files


def calc_ozone(new=True, *event):
    a = Ozone(home)
    try:
        if not new:
            last_calculated_o3_date = LastCalculatedOzone().get()
        else:
            raise
    except:
        last_calculated_o3_date = LastCalculatedOzone().set(datetime.datetime(1990, 1, 1))
    all_files_count = count_files(home, last_calculated_o3_date)
    current_count = 0
    start_flag = True
    for top, dirs, nondirs in os.walk(home):
        working_files = []
        for file in sorted(nondirs):
            if file.count("Z-D") > 0:
                working_files.append(file)
        if working_files:
            if start_flag:
                start_flag = False
                save_csv(home, ["Datetime", "Ozone"], [], new=new)
                save_csv(home, ["Datetime", "DailyMeanOzone"], [], new=new)
            daily_ozone = []
            data = []
            mean_data = []
            date_from_dir = top.split(p_sep)[-3:]
            path = os.path.join(*date_from_dir)
            # Дата текущей директории меньше пследней считанной?
            if _strptime(path) <= last_calculated_o3_date:
                continue
            # Дата текущей директории больше пследней считанной?
            else:
                for file in working_files:
                    try:
                        file_path = os.path.join(path, file)
                        out = a.main_func_2(file_path)
                        data.append([out["datetime"], out["o3"]])
                        daily_ozone.append(out["o3"])
                        current_count += 1
                        but_calc_all_ozone.configure(text="{} {}/{}".format(out["datetime"],
                                                                            current_count,
                                                                            all_files_count))
                        root.update()

                    except Exception as err:
                        print(err)
                mean_data.append(['.'.join(date_from_dir), sredne(daily_ozone, 'ozone', 0)])
                out_name = save_csv(home, ["Datetime", "Ozone"], data, new=False)
                out_name_mean = save_csv(home, ["Datetime", "DailyMeanOzone"], mean_data, new=False)
                last_calculated_o3_date = LastCalculatedOzone().set(_strptime(path))
    if current_count == all_files_count:
        try:
            print("File saved to: {}".format(out_name))
            print("File saved to: {}".format(out_name_mean))
        except:
            pass
    if new:
        but_calc_all_ozone.configure(text="Пересчёт завершён!")
    else:
        but_calc_all_ozone_continue.configure(text="Пересчёт завершён!")


def make_txt_list_ZSD(directory):
    txtfiles = []
    try:
        for file in os.listdir(directory):
            if file[-3:] == "txt" and (file.count("Z-D") > 0):
                txtfiles.append(file)
    except:
        pass
    return sorted(txtfiles)


def make_o3file():
    global path
    global curr_o3
    global canvas
    global gr_ok
    global curr_time
    global ida
    global o3_plotted
    global root
    global o3_mod
    global file_name
    global tmp_path

    for i in buttons:
        i.configure(state=DISABLED)
    if ida != '':
        canvas.after_cancel(ida)
        ida = ''
    mode = uv.get()
    # mode = 0
    if mode == 0:
        o3_mode = 'ozone'
        tex = 'Идет пересчёт озона'
    elif mode == 1:
        o3_mode = 'uva'
        tex = 'Идет пересчёт УФ-А'
    elif mode == 2:
        o3_mode = 'uvb'
        tex = 'Идет пересчёт УФ-Б'
    elif mode == 3:
        o3_mode = 'uve'
        tex = 'Идет пересчёт УФ-Э'
    o3_mod = o3_mode
    path = change_mwt_dir()
    lab_ozon.configure(text=tex)
    root.update()
    geom = root.geometry().split('+')[0].split('x')
    plotx = int(geom[0]) - 267 - 10
    ploty = int(geom[1]) - 118
    curr_time = []
    o3zn = {'index': [], 'data': [], 'time': [], 'color': []}
    txt = make_txt_list_ZSD(path)
    gr_ok = 0
    j = 1
    for i in txt:
        file_name = i.split('_')[1]
        if i.find("Z-") != -1:
            color = 'black'
        else:
            color = 'blue'
        file = os.path.join(path, i)
        if main_func(color, o3_mode, gr_ok, file, 0, 0, plotx, ploty, 60, 40, right_panel):
            if mode == 1:
                curr_o3[1] = curr_o3[2]
            elif mode == 2:
                curr_o3[1] = curr_o3[3]
            elif mode == 3:
                curr_o3[1] = curr_o3[4]
            o3zn['index'].append(j)
            o3zn['data'].append(curr_o3[1])
            o3zn['time'].append(curr_o3[0])
            o3zn['color'].append(color)
            j += 1
    ki = 0
    if o3zn['data']:  # try:
        try:
            xmax = len(o3zn['data'])
            ymax = round(max(o3zn['data']))
            kx = -1
            ky = -1
            xshag = 25
            yshag = 10
            tmp = []
            gr_ok = 1
            if kx == -1:
                kx = xmax / plotx
            elif kx == 0:
                x = xmax
            x = xmax
            if ky == -1:
                if o3_mode == 'ozone':
                    ky = ploty / (ozon_scale_max - 250)
                else:
                    if ymax != 0:
                        ky = ploty / ymax
                    else:
                        ky = 1

            elif ky == 0:
                ky = ploty / ymax
            y = ymax
            dt = 1
            dt = graph_in(o3_mode, gr_ok, o3zn, kx, ky, x, y, plotx, ploty, xshag, yshag, right_panel)
            lab_currnt_data.configure(text='Дата: {0}'.format(main_func.date))
            if o3_mode == 'ozone':
                if dt['o3lab'] == '':
                    tex = 'Ошибка в файле'
                else:
                    tex = '3Значение озона: {0}'.format(dt['o3lab'])
            elif o3_mode == 'uva':
                tex = 'УФ-А'
            elif o3_mode == 'uvb':
                tex = 'УФ-Б'
            elif o3_mode == 'uve':
                tex = 'УФ-Э'

            o3_plotted = 1
        except Exception as err:
            print(dt)
            path = tmp_path
            txt = make_txt_list_ZSD(path)
            change_mwt_dir()
            print('plotter.make_o3file(): Нет измерений за сегодня.\n', err)
            tex = 'Нет измерений\nза сегодня.'
        finally:
            gr_ok = 2
            lab_uva.configure(text='')
            lab_uvb.configure(text='')
            lab_uve.configure(text='')
            lab_sun.configure(text='')
            root.update()
    ##            if ida == '':
    ##                ida = canvas.after(600000,after_o3file)

    for i in buttons:
        i.configure(state=NORMAL)


"""============== <Main> =============="""
root = Tk()
host, port, data4send = "10.65.25.2", 20000, ''
ida = ''
last_dir = []
disks = []
file_name = ''
path = os.getcwd()
home = os.getcwd()
tmp_path = home
ini_s = read_ini(home, 'r', '')
add = float(ini_s['zenith_add'])
if sys_pf == 'darwin':
    drive = "/"
else:
    drive = os.getcwd()[:3]
path2 = ''
(plotx, ploty) = root.maxsize()
plotx -= 300
ploty -= 200
o3min = 200
ozon_scale_max = 600
color = 'black'
ima = []
label = ''
o3srednee = ''
bit = 1
ok = 1
scale_printed = 0
last_path = read_path(home, path, 'r').split('\n')[0]
try:
    if path != last_path and os.path.exists(last_path):
        path = last_path
    else:
        pass
except:
    path = home
curr_o3 = [0, 0, 0, 0, 0]

try:
    ome = read_sensitivity(home)  # Чувствительность прибора
except:
    ome = None
    print('Чувствительность прибора не найдена в каталоге программы')
curr_time = []
gr_ok = 2
o3_mode = ''
o3_plotted = 1
conf2 = []  # Заполняется с первым запуском функции main_func()

"""
gr_ok = 0 - озон расчитывается, график не строится
gr_ok = 1 - озон не расчитывается, график строится
gr_ok = 2 - озон расчитывается, график строится
"""

root.title('УФОС Просмотр')
root.protocol('WM_DELETE_WINDOW', window_closed)
root.wm_state('zoomed')
root.resizable(True, True)
appHighlightFont = font2.Font(family='Helvetica', size=14)  # , weight='bold')
top_panel = ttk.Frame(root, padding=(1, 1), relief='solid')  # ,width=800
common_panel = ttk.Frame(top_panel, padding=(1, 1), relief='solid')
admin_panel = ttk.Frame(top_panel, padding=(1, 1), relief='solid')
left_panel = ttk.Frame(root, padding=(1, 1), relief='sunken')
right_panel = ttk.Frame(root, padding=(1, 1), relief='sunken')
downline = ttk.Frame(root, padding=(1, 1), relief='solid', height=20)

canvas = Canvas(right_panel, bg="white", width=plotx, height=ploty)  # white

but_refresh = ttk.Button(common_panel, text='Обновить', command=refresh)
but_dir = ttk.Button(common_panel, text='Выбор каталога', command=dir_list_show)
var = IntVar()
var.set(1)
rad_4096 = ttk.Radiobutton(admin_panel, text='Единая шкала', variable=var, value=0)
rad_ytop = ttk.Radiobutton(admin_panel, text='Оптимальная шкала', variable=var, value=1)
chk_var_auto = IntVar()
chk_var_auto.set(1)
chk_autorefresh = ttk.Checkbutton(admin_panel, text='Автообновление', variable=chk_var_auto)  # ,command=after_o3file)
chk_var = IntVar()
chk_var.set(1)
chk_kz_obl = ttk.Checkbutton(admin_panel, text='KzОбл.', variable=chk_var)
chk_var_mwt = IntVar()
chk_var_mwt.set(0)
chk_mwt = ttk.Checkbutton(common_panel, text='mWt', variable=chk_var_mwt, command=change_mwt_dir)
but_plot_more = ttk.Button(admin_panel, text='Подробный просмотр', command=plot_more)
uv = IntVar()
uv.set(4)
rad_spectr = ttk.Radiobutton(common_panel, text='Спектр', variable=uv, value=4, command=plot_file)
rad_o3file = ttk.Radiobutton(common_panel, text='Озон', variable=uv, value=0, command=make_o3file)
rad_uva = ttk.Radiobutton(common_panel, text='УФ-А', variable=uv, value=1, command=make_o3file)
rad_uvb = ttk.Radiobutton(common_panel, text='УФ-Б', variable=uv, value=2, command=make_o3file)
rad_uve = ttk.Radiobutton(common_panel, text='УФ-Э', variable=uv, value=3, command=make_o3file)
but_remake = ttk.Button(admin_panel, text='Новый формат Z-D', command=b_remake)
but_send = ttk.Button(admin_panel, text=host, command=send_all_files_plotter)

# ================================================================================================

but_calc_all_ozone = ttk.Button(admin_panel, text='Новый пересчёт озона', command=lambda: calc_ozone(new=True))
but_calc_all_ozone_continue = ttk.Button(admin_panel, text='Продолжить пересчёт озона',
                                         command=lambda: calc_ozone(new=False))

# ================================================================================================

ent_code = ttk.Entry(common_panel, width=2)
file_list = Listbox(left_panel, selectmode=SINGLE, height=16, width=28)
scr_lefty = ttk.Scrollbar(left_panel, command=file_list.yview)
file_list.configure(yscrollcommand=scr_lefty.set)
lab_currnt_data = ttk.Label(left_panel, text='Данные: ')
currnt_data = ttk.Label(left_panel, text='')
lab_ozon = ttk.Label(left_panel, text='Значение озона: ', foreground='blue', font=appHighlightFont)
lab_uva = ttk.Label(left_panel, text='Значение УФ-А: ', foreground='blue')
lab_uvb = ttk.Label(left_panel, text='Значение УФ-Б: ', foreground='blue')
lab_uve = ttk.Label(left_panel, text='Значение УФ-Э: ', foreground='blue')
lab_sun = ttk.Label(left_panel, text='')
lab_path = ttk.Label(downline, text=path)
lab_err = ttk.Label(downline, text='', width=20)

buttons = [but_refresh, but_dir, rad_4096, rad_ytop, chk_kz_obl, chk_mwt, but_plot_more, rad_spectr, rad_o3file,
           rad_uva, rad_uvb, rad_uve, but_remake, but_send]

"""============== GUI Structure =============="""
top_panel.grid(row=0, column=0, sticky='nwe', columnspan=4)
common_panel.grid(row=0, column=0, sticky='nwe')
but_refresh.grid(row=0, column=0, sticky='w')
but_dir.grid(row=0, column=1, sticky='w')

obj_grid()

but_send.grid(row=0, column=10, sticky='w')
but_calc_all_ozone.grid(row=0, column=11, sticky='w')
but_calc_all_ozone_continue.grid(row=0, column=12, sticky='w')
ent_code.grid(row=0, column=13, sticky='e')
right_panel.grid(row=1, column=3, sticky='nwse', padx=1)
left_panel.grid(row=1, column=0, sticky='nwse', padx=1)
file_list.grid(row=0, column=0, sticky='nwse', padx=1)
scr_lefty.grid(row=0, column=1, sticky='nws')
lab_currnt_data.grid(row=2, column=0, sticky='we', padx=1)
lab_ozon.grid(row=3, column=0, sticky='we', padx=1)
lab_uva.grid(row=4, column=0, sticky='we', padx=1)
lab_uvb.grid(row=5, column=0, sticky='we', padx=1)
lab_uve.grid(row=6, column=0, sticky='we', padx=1)
lab_sun.grid(row=7, column=0, sticky='we', padx=1)
currnt_data.grid(row=8, column=0, sticky='we', padx=1)
"""=============================================================="""
main_func(color, 'spectr', 2, 0, 0, 0, plotx, ploty, 60, 40, right_panel)
change_mwt_dir()
point = main_func.inis['points'].split(',')
p_uva1, p_uva2 = nm2pix(315, conf2, add), nm2pix(400, conf2, add)
p_uvb1, p_uvb2 = nm2pix(280, conf2, add), nm2pix(315, conf2, add)
p_uve1, p_uve2 = 0, 3691  # nm2pix(290),nm2pix(420)
p_1 = nm2pix(float(point[0]), conf2, add)
p_2 = nm2pix(float(point[1]), conf2, add)
p_3 = nm2pix(float(point[2]), conf2, add)
p_4 = nm2pix(float(point[3]), conf2, add)
ps = [p_1, p_2, p_3, p_4]
p330_350 = [nm2pix(point[2], conf2, add), nm2pix(point[3], conf2, add)]

common = [rad_4096, rad_ytop, chk_kz_obl, but_plot_more, but_remake]
sertification = [rad_4096, rad_ytop, chk_kz_obl, but_plot_more, rad_uva, rad_uvb, rad_uve, but_remake]
change_privileges(common, 0)

"""=============================================================="""
downline.grid(row=6, column=0, sticky='nswe', columnspan=4)
lab_path.grid(row=0, column=0, sticky='w')
lab_err.grid(row=0, column=1, sticky='e')

"""============== GUI Actions =============="""
file_list.bind('<Double-Button-1>', plot_file)
file_list.bind('<Return>', plot_file)
file_list.bind('<Button-1>', dirs_window_destroy)
canvas.bind('<Button-1>', dirs_window_destroy)
left_panel.bind('<Button-1>', dirs_window_destroy)
ent_code.bind('<Return>', check_code)
root.mainloop()
