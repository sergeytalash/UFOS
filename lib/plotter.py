# Version: 2.0
# Modified: 11.05.2025
# Author: Sergey Talash

import gc
import json
import os
import sys
from _tkinter import TclError
from datetime import datetime
from datetime import timedelta
from shutil import copy
from sys import platform as sys_pf
from tkinter import Canvas
from tkinter import DISABLED
from tkinter import END
from tkinter import IntVar
from tkinter import Listbox
from tkinter import NORMAL
from tkinter import SINGLE
from tkinter import Tk
from tkinter import Toplevel
from tkinter import font
from tkinter import ttk

import numpy as np

try:
    from lib import calculations as calc
    from lib import core
    from lib import gui
except (ImportError, ModuleNotFoundError):
    import calculations as calc
    import core
    import gui

if sys_pf == 'darwin':
    import matplotlib

    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

if os.name == 'posix':
    p_sep = '/'
else:
    p_sep = '\\'


class PlotClass:
    def __init__(self, root, window, o3_mode, plot_x, plot_y, recalculate_value,
                 show_all, use_sensitivity_z, use_sensitivity_s, var_top, ps_z,
                 ps_s, canvas_list):
        """

        Args:
            window (ttk.Frame):  where graph is created
            o3_mode (str): Mode of measurements ('spectr', 'ozone', 'uva', 'uvb', 'uve')
            plot_x (int): Width of picture in pixels
            plot_y (int): Height of picture in pixels
            recalculate_value (int): Read measured files (1 or 0)
            show_all (int): Show all calculated values, ignore correction filters (1 or 0)
            use_sensitivity_z (int): Use sensitivity (1 or 0)
            use_sensitivity_s (int): Use sensitivity (1 or 0)
        """
        self.root = root
        self.show_all = show_all
        self.use_sensitivity_z = use_sensitivity_z
        self.use_sensitivity_s = use_sensitivity_s
        self.var_top = var_top
        self.canvas_list = canvas_list
        self.recalculate_value = recalculate_value
        self.plot_x = plot_x
        self.plot_y = plot_y
        self.window = window
        self.o3_mode = o3_mode
        self.date_time = ''
        self.zen_path = ''
        self.ozone_y_min = 0
        self.ozone_y_max = 650
        self.data = {}
        self.hs = 0
        self.mu = 0
        self.amas = 0
        self.max_y = 4096
        self.spectr = []
        self.uvs_or_o3 = {}
        self.ozone = 0
        self.fig, self.ax = plt.subplots(1)
        plt.subplots_adjust(left=0.07, right=0.97, bottom=0.07, top=0.95)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.nexday_allow_flag = 0
        self.dates = []
        self.hss = []
        self.ozone_list = []
        self.spectrum = []
        self.old_file_list = os.listdir(core.PATH)
        self.hours = mdates.HourLocator()
        self.minutes = mdates.MinuteLocator()
        self.DateFmt = mdates.DateFormatter('%H:%M')
        if self.o3_mode in ['ozone', 'uva', 'uvb', 'uve']:
            self.point = 'o'
        elif self.o3_mode == 'spectr':
            self.point = '-'
        self.psZ = ps_z
        self.psS = ps_s
        # Calc ozone
        self.o3 = {}
        self.uvs_or_o3['ZD'] = {}
        self.prom = int(core.PARS['calibration2']['pix+-'] / eval(calc.CONF_Z[1]))
        self.y1 = []
        self.y2 = []
        self.x1 = []
        self.x2 = []
        # Calc UV
        self.uv = 0
        self.uvs_or_o3['SD'] = {}
        self.curr_o3_dict = {'uva': [2, calc.P1_UVA, calc.P2_UVA],
                             'uvb': [3, calc.P1_UVB, calc.P2_UVA],
                             'uve': [4, calc.P1_UVE, calc.P2_UVE]}
        self.sensitivityZ = core.read_sensitivity("Z")
        self.sensitivityS = core.read_sensitivity("S")
        self.sensitivity_eritem = core.read_sensitivity("E")

    def calc_ozone(self):
        self.spectrum = calc.spectr2zero(self.data['spectr'])
        """Расчет озона"""
        self.o3 = {}
        correct = {}
        additional_data = {}
        for pair, values in calc.LAMBDA_CONSTS.items():
            self.o3[pair], correct[pair], additional_data[pair] = calc.pre_calc_o3(
                calc.LAMBDA_CONSTS[pair],
                calc.LAMBDA_CONSTS_PIX[pair],
                self.spectrum,
                self.prom,
                self.data['mu'],
                pair)
        self.uvs_or_o3['ZD'] = {'o3_1': self.o3["1"],
                                'o3_2': self.o3["2"],
                                'correct_1': correct["1"],
                                'correct_2': correct["2"],
                                'additional_data_1': additional_data["1"],
                                'additional_data_2': additional_data["2"]}
        if self.o3_mode != 'spectr':
            if self.show_all or correct["1"] == 1:
                self.x1.append(self.data['datetime'])
                self.y1.append(self.o3["1"])
                # self.sh1.append(self.data["calculated"]["sunheight"])
            if self.show_all or correct["2"] == 1:
                self.x2.append(self.data['datetime'])
                self.y2.append(self.o3["2"])
                # self.sh2.append(self.data["calculated"]["sunheight"])

    def calc_uv(self, uv_mode, add_point):
        p1 = self.curr_o3_dict[uv_mode][1]
        p2 = self.curr_o3_dict[uv_mode][2]
        self.spectrum = calc.spectr2zero(self.data['spectr'])
        ultraviolet = 0
        try:
            if uv_mode in ['uva', 'uvb']:
                if self.use_sensitivity_s:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]) * np.array(self.sensitivityS[p1:p2]))
                else:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]))
                ultraviolet *= float(eval(calc.CONF_S[1])) * core.PARS['device']['graduation_expo'] / \
                               self.data['expo']
            elif uv_mode == 'uve':
                if self.use_sensitivity_s:
                    ultraviolet = sum([float(self.spectrum[i]) *
                                       self.sensitivity_eritem[i] *
                                       self.sensitivityS[i] for i in range(p1, p2, 1)]
                                      )
                else:
                    ultraviolet = sum([float(self.spectrum[i]) * self.sensitivity_eritem[i] for i in range(p1, p2, 1)])

                    ultraviolet *= float(eval(calc.CONF_S[1])) * core.PARS['device']['graduation_expo'] / \
                                   self.data['expo']
                    ultraviolet *= float(core.PARS['calibration']['{}_koef'.format(uv_mode)])
        except:
            ultraviolet = 0
        self.uv = int(round(ultraviolet, 0))
        self.uvs_or_o3['SD'][uv_mode] = self.uv
        if self.o3_mode != 'spectr' and add_point:
            self.x1.append(self.data['datetime'])
            self.y1.append(self.uv)

    @staticmethod
    def get_spectr_new(file_path, flag):
        """Get data from NEW file"""
        try:
            with open(file_path, errors='ignore') as f:
                data = json.load(f)
            if flag:
                new_data = {'spectr': data['spectr'],
                            'datetime': datetime.strptime(data['mesurement']['datetime_local'],
                                                          '%Y%m%d %H:%M:%S'),
                            'hs': data['calculated']['sunheight'],
                            'amas': data['calculated']['amas'],
                            'mu': data['calculated']['mu'],
                            'expo': data['mesurement']['exposition'],
                            'accumulate': data['mesurement']['accummulate'],
                            'channel': data['mesurement']['channel'],
                            'latitude': data['mesurement']['latitude'],
                            'longitude': data['mesurement']['longitude'],
                            'timezone': data['mesurement']['timezone']
                            }
                try:
                    new_data['temperature_ccd'] = data['mesurement']['temperature_ccd']
                    new_data['temperature_poly'] = data['mesurement']['temperature_poly']
                except KeyError:
                    new_data['temperature_ccd'] = 'None'
                    new_data['temperature_poly'] = 'None'
            else:
                new_data = data
            return new_data
        except json.decoder.JSONDecodeError as err:
            gui.show_error_in_separate_window(err, "Ufos measurement file is invalid.")
        except Exception as err:
            gui.show_error_in_separate_window(err)

    @staticmethod
    def get_spectr_old(file_path):
        """Get data from OLD file"""
        with open(file_path) as f:
            new_data = {}
            line = '1'
            while line:
                if line.count('time') > 0:
                    tmp = line.split(' = ')
                    new_data['channel'] = tmp[1].split(',')[0]
                    new_data['datetime'] = datetime.strptime(
                        '{} {}'.format(tmp[2].split(',')[0], tmp[3].strip()),
                        '%d.%m.%Y %H:%M:%S')
                elif line.count('Exposure') > 0:
                    new_data['expo'] = int(line.split('=')[1])
                elif line.count('Temperature') > 0:
                    new_data['temperature_poly'] = float(line.split('=')[1])
                    new_data['temperature_ccd'] = 'None'
                elif line.count('Accummulate') > 0:
                    new_data['accumulate'] = int(line.split('=')[1])
                elif line.count('hs') > 0:
                    new_data['hs'] = float(line.split()[0])
                elif line.count('amas') > 0:
                    new_data['amas'] = float(line.split()[0])
                elif line.count('mu') > 0:
                    new_data['mu'] = float(line.split()[0])
                elif line.count('Value') > 0:
                    new_data['spectr'] = []
                    line = f.readline().strip()
                    while line:
                        new_data['spectr'].append(int(line))
                        line = f.readline().strip()
                line = f.readline()
            return new_data

    def get_spectr(self, file_path, flag=True):
        """Get data from OLD file"""
        if os.path.basename(file_path).split('_')[2] in ['ZD', 'Dz', 'Z', 'SD', 'Ds', 'S']:
            self.data = self.get_spectr_new(file_path, flag)
        else:
            self.data = self.get_spectr_old(file_path)
        self.spectrum = self.data['spectr']
        return self.data

    def fig_prepare(self):
        while len(self.canvas_list) > 0:
            canvas_i, fig_i = self.canvas_list.pop()
            fig_i.clf()
            canvas_i.get_tk_widget().destroy()
        self.fig.clf()
        plt.close()
        gc.collect()
        self.plot_x, self.plot_y = gui.update_geometry(self.root)
        self.fig, self.ax = plt.subplots(1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)

    def set_plot_limits(self, x, y, x_min, x_max, mode):
        if max(x) > x_max: x_max = max(x)
        if min(x) < x_min: x_min = min(x)
        if self.o3_mode != 'ozone':
            y_max = max(y) * 1.05
            y_min = min(y) * 0.95
        else:
            y_max = self.ozone_y_max
            y_min = self.ozone_y_min
        if mode == 'hour':
            self.ax.set(xlim=[x_min - timedelta(minutes=15),
                              x_max + timedelta(minutes=15)],
                        ylim=[y_min, y_max])
            self.ax.xaxis.set_major_locator(mdates.HourLocator())
            self.ax.xaxis.set_minor_locator(mdates.MinuteLocator(np.arange(0, 60, 10)))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif mode == 'degree':
            self.ax.set(xlim=[x_min - 0.5, x_max + 0.5], ylim=[y_min, y_max])
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    def apply_sensitivity(self, sensitivity):
        new_spectr = []
        for index, value in enumerate(self.spectrum):
            new_spectr.append(
                value * sensitivity[index] * core.PARS['device']['graduation_expo'] / self.data['expo'])
        self.spectrum = new_spectr

    def plot(self, path):
        self.zen_path = path
        self.fig_prepare()

        self.fig.set_size_inches(self.plot_x / 82, self.plot_y / 80)
        self.fig.set_dpi(80)

        if self.o3_mode == 'first':
            # self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
            # canvs.append(self.canvas)
            # self.canvas.draw()
            # print("canvs: {}".format(len(canvs)))
            # canvs.append(self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe'))
            pass
        # ====================== Spectr ======================
        elif self.o3_mode == 'spectr':
            print('show spectr')
            self.ax.set_xlabel('нм')
            self.ax.set_ylabel('мВ')
            if 'Z' in self.data['channel']:
                conf = calc.CONF_Z
                if self.use_sensitivity_z:
                    self.apply_sensitivity(self.sensitivityZ)
            else:
                conf = calc.CONF_S
                if self.use_sensitivity_s:
                    self.apply_sensitivity(self.sensitivityS)
            self.ax.set_ylabel('мВт/м^2*нм')
            self.ax.plot([calc.pix2nm(index, conf) for index, value in enumerate(self.spectrum)],
                         self.spectrum, self.point, color='k')
            if self.var_top.get():
                self.max_y = max(self.spectrum[slice(*core.PARS['device']['pix_work_interval'])]) + 100
            if 'Z' in self.data['channel']:
                ps = self.psZ
            else:
                ps = self.psS

            for key in ps.keys():
                for point in ps[key]:
                    point_nm = calc.pix2nm(point, conf, 1)
                    self.ax.plot([point_nm] * 2, [0, self.max_y], '--', color='red')
                    self.ax.text(point_nm, self.max_y - 50, str(point_nm), horizontalalignment='center')

            self.ax.set(xlim=[calc.pix2nm(0, conf, 1, 0), calc.pix2nm(3692, conf, 1, 0)], ylim=[0, self.max_y])
            self.ax.grid(True)

            self.fig.canvas.draw()
        else:
            self.ax.set_xlabel('Time')
            # ====================== Ozone ======================
            if self.o3_mode == 'ozone':
                print('show ozone')
                self.ax.set_ylabel('o3')
            # ====================== UV =========================
            elif self.o3_mode == 'uva':
                self.ax.set_ylabel('мВт/м^2')
                print('show uva')
            elif self.o3_mode == 'uvb':
                self.ax.set_ylabel('мВт/м^2')
                print('show uvb')
            elif self.o3_mode == 'uve':
                self.ax.set_ylabel('мВт/м^2')
                print('show uve')
            # ===================================================
            for x_mas, y_mas, color in zip([self.x1, self.x2], [self.y1, self.y2], ['blue', 'green']):
                if y_mas:
                    tmp_y = []
                    tmp_x = []
                    for x, y in zip(x_mas, y_mas):
                        if y < 0:
                            y = 0
                        tmp_y.append(y)
                        tmp_x.append(x)
                    y_mas = tmp_y
                    x_mas = tmp_x
                    self.ax.plot(x_mas, y_mas, self.point, color=color)
                    self.set_plot_limits(x_mas, y_mas, min(x_mas), min(x_mas) + timedelta(hours=2), 'hour')
            self.ax.grid(True)
            self.fig.canvas.draw()
            gui.canvs_destroy(self.canvas_list)

        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        self.canvas_list.append((canvas, self.fig))
        canvas.draw()


class Main:
    def __init__(self, show_ozone_pairs):
        self.dirs_list = None
        self.disk_list = None
        self.dir_list_widget_window = None
        self.show_ozone_pairs = show_ozone_pairs
        self.human_error_text = ""
        self.ts, self.shs, self.calc_results = [], [], []
        self.human_error_text = "Common settings file is invalid"
        self.human_error_text = "Ufos settings file is invalid"
        if os.name != 'posix':
            self.drive = os.getcwd()[:3]
        else:
            self.drive = p_sep
        self.dir_list_opened = False
        self.path2 = ''
        self.o3min = 200
        self.ozon_scale_max = 600
        self.color = 'black'
        self.disks = []
        self.label = ''
        self.o3srednee = ''
        self.bit = 1
        self.ok = 1
        self.scale_printed = 0
        self.canvas_list = []
        self.last_dir = []
        self.last_path = core.last_used_path(core.HOME, core.PATH, 'r')
        try:
            if core.PATH != self.last_path and os.path.exists(self.last_path):
                core.PATH = self.last_path
        except:
            core.PATH = core.HOME
        self.curr_o3 = [0, 0, 0, 0, 0]
        try:
            # Check if file exists
            self.human_error_text = 'Чувствительность прибора УФОС' \
                                    ' sensitivity{} - не найдена в каталоге программы!'.format(
                core.PARS['device']['id'])
            core.read_sensitivity("S")  # Световая чувствительность прибора
            self.human_error_text = 'Чувствительность прибора УФОС' \
                                    ' senseritem{} - не найдена в каталоге программы!'.format(core.PARS['device']['id'])
            core.read_sensitivity("E")  # Эритемная Чувствительность прибора
        except Exception as err:
            raise err
        self.o3_mode = ''
        self.o3_plotted = 1

        try:
            self.root = Tk()
            self.appHighlightFont = font.Font(self.root, family='Helvetica', size=14)
            self.plotx, self.ploty = gui.update_geometry(self.root)
            self.root.title('УФОС Просмотр')
            self.root.protocol('WM_DELETE_WINDOW', self.window_closed)
            if sys_pf != 'linux':
                self.root.wm_state('zoomed')
            else:
                self.root.wm_state('normal')
            # self.root.geometry('908x530+200+100') #'908x530+200+100'
            self.root.resizable(True, True)
            self.top_panel = ttk.Frame(self.root, padding=(1, 1), relief='solid')  # ,width=800
            self.menu_panel = ttk.Frame(self.top_panel, padding=(1, 1), relief='solid')
            self.admin_panel = ttk.Frame(self.top_panel, padding=(1, 1), relief='solid')
            self.left_panel = ttk.Frame(self.root, padding=(1, 1), relief='sunken')
            self.right_panel = ttk.Frame(self.root, padding=(1, 1), relief='sunken')
            self.downline = ttk.Frame(self.root, padding=(1, 1), relief='solid', height=20)

            self.canvas = Canvas(self.right_panel, bg="white", width=self.plotx, height=self.ploty)  # white

            # Admin Menu
            self.chk_var_sens_z = IntVar()
            self.chk_var_sens_z.set(1)
            self.chk_sens_z = ttk.Checkbutton(
                self.admin_panel,
                text='SensZ',
                variable=self.chk_var_sens_z)

            self.chk_var_sens_s = IntVar()
            self.chk_var_sens_s.set(1)
            self.chk_sens_s = ttk.Checkbutton(
                self.admin_panel,
                text='SensS',
                variable=self.chk_var_sens_s)

            self.var_recalculate_source_files = IntVar()
            self.var_recalculate_source_files.set(0)
            self.chk_recalculate_source_files = ttk.Checkbutton(
                self.admin_panel,
                text='Пересчёт графика',
                variable=self.var_recalculate_source_files)
            self.var_show_all = IntVar()
            self.var_show_all.set(0)
            self.chk_show_all = ttk.Checkbutton(self.admin_panel, text='Отобразить всё', variable=self.var_show_all)
            self.chk_var_show_correct1 = IntVar()
            self.chk_var_show_correct1.set(0)
            self.chk_show_correct1 = ttk.Checkbutton(self.admin_panel, text='Откл Корр 1',
                                                     variable=self.chk_var_show_correct1)
            self.but_save_to_final_file = ttk.Button(self.admin_panel, text='Сохранить в файл')
            self.but_make_mean_file = ttk.Button(self.admin_panel, text='Сохранить в файл среднего')
            self.var_scale = IntVar()
            self.var_scale.set(1)
            self.rad_4096_scale = ttk.Radiobutton(self.admin_panel,
                                                  text='Единая шкала',
                                                  variable=self.var_scale, value=0)
            self.rad_dynamic_scale = ttk.Radiobutton(self.admin_panel,
                                                     text='Оптимальная шкала',
                                                     variable=self.var_scale, value=1)

            self.but_plot_more = ttk.Button(self.admin_panel, text='Подробный просмотр', command=self.plot_more)
            self.uv = IntVar()
            self.uv.set(4)
            self.but_remake = ttk.Button(self.admin_panel, text='Новый формат Z-D', command=self.b_remake)
            # but_send = ttk.Button(self.admin_panel, text=host, command=send_all_files_plotter)

            # Annual ozone calculations
            self.ent_year = ttk.Entry(self.admin_panel)
            self.ent_year.insert(0, "2024")
            self.but_annual_ozone = ttk.Button(self.admin_panel, text='Сохранить озон за год')

            self.admin_menu_obj = [self.chk_sens_z, self.chk_sens_s, self.chk_show_all, self.chk_show_correct1,
                                   self.chk_recalculate_source_files,
                                   self.but_save_to_final_file,
                                   self.but_make_mean_file,
                                   self.rad_4096_scale, self.rad_dynamic_scale, self.but_plot_more, self.but_remake,
                                   # but_send
                                   self.ent_year, self.but_annual_ozone
                                   ]

            # Main Menu
            self.but_refresh = ttk.Button(self.menu_panel, text='Обновить', command=self.refresh)
            self.but_dir = ttk.Button(self.menu_panel, text='Выбор каталога', command=self.dir_list_show)
            self.rad_spectr = ttk.Radiobutton(self.menu_panel, text='Спектр', variable=self.uv, value=4,
                                              command=self.plot_spectr)
            self.rad_o3file = ttk.Radiobutton(self.menu_panel, text='Озон', variable=self.uv, value=0,
                                              command=self.make_o3file)
            self.rad_uva = ttk.Radiobutton(self.menu_panel, text='УФ-А', variable=self.uv, value=1,
                                           command=self.make_o3file)
            self.rad_uvb = ttk.Radiobutton(self.menu_panel, text='УФ-Б', variable=self.uv, value=2,
                                           command=self.make_o3file)
            self.rad_uve = ttk.Radiobutton(self.menu_panel, text='УФ-Э', variable=self.uv, value=3,
                                           command=self.make_o3file)
            self.ent_code = ttk.Entry(self.menu_panel, width=2)
            self.main_menu_obj = [self.but_refresh,
                                  self.but_dir, self.rad_spectr,
                                  self.rad_o3file, self.rad_uva,
                                  self.rad_uvb, self.rad_uve,
                                  self.ent_code]

            self.file_list = Listbox(self.left_panel, selectmode=SINGLE, height=16, width=28)
            self.scr_lefty = ttk.Scrollbar(self.left_panel, command=self.file_list.yview)
            self.file_list.configure(yscrollcommand=self.scr_lefty.set)
            self.lab_current_data = ttk.Label(self.left_panel, text='Данные: ')
            self.current_data = ttk.Label(self.left_panel, text='')
            self.lab_ozone = ttk.Label(self.left_panel, text='', foreground='blue', font=self.appHighlightFont)
            self.lab_uva = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_uvb = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_uve = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_sun = ttk.Label(self.left_panel, text='')
            self.lab_path = ttk.Label(self.downline, text=core.PATH)
            self.lab_err = ttk.Label(self.downline, text='', width=20)

            self.buttons = self.main_menu_obj + self.admin_menu_obj

            """============== GUI Structure =============="""
            self.top_panel.grid(row=0, column=0, sticky='nwe', columnspan=4)
            self.menu_panel.grid(row=0, column=0, sticky='nwe')
            self.but_refresh.grid(row=0, column=0, sticky='w')
            self.but_dir.grid(row=0, column=1, sticky='w')

            self.draw_panels()

            # but_send.grid(row=0, column=10, sticky='w')
            self.ent_code.grid(row=0, column=13, sticky='e')
            self.right_panel.grid(row=1, column=3, sticky='nwse', padx=1)
            self.left_panel.grid(row=1, column=0, sticky='nwse', padx=1)
            self.file_list.grid(row=0, column=0, sticky='nwse', padx=1)
            self.scr_lefty.grid(row=0, column=1, sticky='nws')
            self.lab_current_data.grid(row=2, column=0, sticky='we', padx=1)
            self.lab_ozone.grid(row=3, column=0, sticky='we', padx=1)
            self.lab_uva.grid(row=4, column=0, sticky='we', padx=1)
            self.lab_uvb.grid(row=5, column=0, sticky='we', padx=1)
            self.lab_uve.grid(row=6, column=0, sticky='we', padx=1)
            self.lab_sun.grid(row=7, column=0, sticky='we', padx=1)
            self.current_data.grid(row=8, column=0, sticky='we', padx=1)
            """=============================================================="""
            calc.CONF_Z = core.PARS['calibration']['nm(pix)']['Z']
            calc.CONF_S = core.PARS['calibration']['nm(pix)']['S']

            self.points = core.PARS['calibration']['points']
            self.p_uva1, self.p_uva2 = calc.nm2pix(315, calc.CONF_S, 0), calc.nm2pix(400, calc.CONF_S, 0)
            self.p_uvb1, self.p_uvb2 = calc.nm2pix(280, calc.CONF_S, 0), calc.nm2pix(315, calc.CONF_S, 0)
            self.p_uve1, self.p_uve2 = 0, 3691  # calc.nm2pix(290),calc.nm2pix(420)

            self.p_zero = {pair: calc.nm2pix(nm, calc.CONF_Z, 0) for pair, nm in zip(["1", "2"], [290, 295])}
            self.p_lamst = calc.nm2pix(290, calc.CONF_Z, 0)
            # Массив констант лямбда в пикселях
            self.psZ = {}
            self.psS = {}
            for key in self.points.keys():
                self.psZ[key] = []
                self.psS[key] = []
                for point in self.points[key]:
                    self.psZ[key].append(calc.nm2pix(point, calc.CONF_Z, 0))
                    self.psS[key].append(calc.nm2pix(point, calc.CONF_S, 0))

            self.start = self.first_clear_plot(self.root, self.plotx, self.ploty, self.right_panel)

            # Скрыть следующие кнопки
            self.common = [self.rad_4096_scale, self.rad_dynamic_scale, self.but_plot_more, self.but_remake]
            self.certification = [self.rad_4096_scale, self.rad_dynamic_scale, self.but_plot_more,
                                  self.rad_uva, self.rad_uvb, self.rad_uve, self.but_remake,
                                  self.chk_recalculate_source_files,
                                  self.but_save_to_final_file, self.but_make_mean_file]
            self.admin_panel.grid_forget()

            """=============================================================="""
            self.downline.grid(row=6, column=0, sticky='nswe', columnspan=4)
            self.lab_path.grid(row=0, column=0, sticky='w')
            self.lab_err.grid(row=0, column=1, sticky='e')

            """============== GUI Actions =============="""
            self.file_list.bind('<Double-Button-1>', self.plot_spectr)
            self.file_list.bind('<Return>', self.plot_spectr)
            self.file_list.bind('<Button-1>', self.dirs_window_destroy)
            self.canvas.bind('<Button-1>', self.dirs_window_destroy)
            self.left_panel.bind('<Button-1>', self.dirs_window_destroy)
            self.right_panel.bind('<Button-1>', self.dirs_window_destroy)
            self.ent_code.bind('<Return>', self.check_code)

            self.root.mainloop()
        except (FileNotFoundError, json.decoder.JSONDecodeError) as err:
            gui.show_error_in_separate_window(err, self.human_error_text)
        except Exception as err:
            print("show_error_in_separate_window", str(err))
        finally:
            pass

    def check_code(self, *event):
        code = self.ent_code.get()
        if code == '9':
            self.draw_panels()
        else:
            self.admin_panel.grid_forget()

    def draw_panels(self):
        r = 0
        c = 0
        self.bit = 1
        for i in self.main_menu_obj:
            i.grid(row=r, column=c, sticky='we')
            c += 1
        r += 1
        c = 0
        self.admin_panel.grid(row=r, column=c, sticky='nwe')
        self.but_annual_ozone.configure(
            command=lambda: calc.AnnualOzone(self.ent_year.get(), self.start, self.root, self.but_annual_ozone).run())
        if not self.var_recalculate_source_files.get():
            self.but_save_to_final_file.configure(state=DISABLED)
            self.but_make_mean_file.configure(state=DISABLED)
        for i in self.admin_menu_obj:
            i.grid(row=r, column=c, sticky='we')
            c += 1
            if self.admin_menu_obj.index(i) > 5 and self.bit:
                r += 1
                c = 0
                self.bit = 0

    def window_closed(self):
        self.root.quit()
        self.root.destroy()

    def plot_more(self):
        pass

    def set_disk_but(self, event):
        if os.name != 'posix':
            path = self.disks[self.disk_list.current()] + ':\\'
        else:
            path = p_sep
        self.drive = path
        self.only_draw_dirs()
        self.refresh_txtlist(path)

    def bit_change(self):
        if self.bit == 0:
            self.bit = 1
        else:
            self.bit = 0

    def b_remake(self):
        """Добавление в файл mu, amas, hs"""
        self.bit = 1
        files = self.make_txt_list(core.PATH)
        filesZD = []
        for i in files:
            if i.count('Z-D') > 0:
                filesZD.append(i)
        os.chdir(core.PATH)
        i = 0
        j = 1
        self.but_remake.config(command=self.bit_change)
        while i < len(filesZD) and self.bit == 1:
            file_old = os.path.join(core.PATH, filesZD[i])
            file_new = os.path.join(core.PATH, '{0}.txt'.format(j))
            copy(file_old, file_new)
            self.but_remake.config(text='{0}/{1}'.format(j, len(filesZD)))
            i += 1
            j += 1
            self.root.update()
        self.but_remake.config(command=self.b_remake)
        self.but_remake.config(text='Новый формат Z-D')
        self.refresh_txtlist(core.PATH)

    @staticmethod
    def analyze(text1, file):
        tmp = 0
        len_t = len(text1)
        while tmp < 100:
            text = file.readline()
            if text[:len_t] == text1:
                txt = text.split('=')[1].split('\n')[0]
                return txt
            tmp += 1
        return 0

    def first_clear_plot(self, root, plotx, ploty, some_root):
        self.refresh_txtlist(core.PATH)
        self.dir_list_opened = False
        start = PlotClass(root, some_root, 'first', plotx, ploty,
                          True,
                          False,
                          False,
                          False,
                          self.var_scale, self.psZ, self.psS,
                          self.canvas_list)
        start.plot(core.PATH)
        return start

    def make_txt_list(self, directory):
        txtfiles = []
        try:
            old_selection = self.file_list.curselection()[0]
        except:
            old_selection = 0
        try:
            for files in os.listdir(directory):
                try:
                    if (files[-3:] == 'txt' and files[0] in 'mp' and (((files[4] == '.' and files[5] in 'ZDS')
                                                                       or (files[5] == '.' and files[6] in 'ZDS'))
                                                                      or files[1] in 'ZDS')):
                        txtfiles.append(files)
                    if files[0] == 'm' and files.split('_')[2] in ['ZD', 'Z', 'Dz', 'SD', 'S', 'Ds']:
                        txtfiles.append(files)
                except:
                    pass

            self.file_list.delete(0, END)
            for i in sorted(txtfiles):
                self.file_list.insert(END, i)
            self.file_list.selection_set(old_selection)
            self.file_list.see(old_selection)
        except:
            pass
        return txtfiles

    def plot_spectr(self, *event):
        # ===== SPECTR =====
        self.uv.set(4)
        for i in self.buttons:
            i.configure(state=DISABLED)
        self.lab_ozone.configure(text='Значение озона: ')
        for mode, var in zip(['uva', 'uvb', 'uve'], [self.lab_uva, self.lab_uvb, self.lab_uve]):
            var.configure(text='Значение UV-{}: '.format(mode[-1].upper()))
        self.root.update()
        plotx, ploty = gui.update_geometry(self.root)
        start = PlotClass(self.root, self.right_panel, 'spectr', plotx, ploty, True, False,
                          self.chk_var_sens_z.get(),
                          self.chk_var_sens_s.get(),
                          self.var_scale, self.psZ, self.psS, self.canvas_list)
        try:
            file = self.file_list.selection_get()
        except TclError:
            self.file_list.selection_set(0)
            file = self.file_list.selection_get()
        start.data = start.get_spectr(os.path.join(core.PATH, file))
        if start.data['channel'].count("Z-D") > 0 or start.data['channel'].count("ZD") > 0:
            try:
                start.calc_ozone()
                self.lab_ozone.configure(text='\n'.join(
                    ['Значение озона'] + ['(P{}): {} е.Д.'.format(pair, start.o3[pair]) for pair in
                                          self.show_ozone_pairs]))
            except TclError:
                pass
        if start.data['channel'].count("S-D") > 0 or start.data['channel'].count("SD") > 0:
            for mode, var in zip(['uva', 'uvb', 'uve'], [self.lab_uva, self.lab_uvb, self.lab_uve]):
                start.calc_uv(mode, False)
                var.configure(text='Значение UV-{}: {} мВт/м^2'.format(mode[-1].upper(), int(start.uv)))
        data = (
            """Канал: {}
Дата Время: {}
Высота Солнца: {} (mu={})
Темп. CCD: {}
Темп. Полихроматора: {}
Экспозиция: {}
Число суммирований: {}""".format(
                start.data['channel'],
                start.data['datetime'],
                start.data['hs'],
                start.data['mu'],
                start.data['temperature_ccd'],
                start.data['temperature_poly'],
                start.data['expo'],
                start.data['accumulate']))
        self.current_data.configure(text=data)
        start.x2 = range(len(start.spectrum))
        start.y2 = start.spectrum
        start.plot(core.PATH)
        for i in self.buttons:
            i.configure(state=NORMAL)

    def change_dir(self, event):
        d1 = self.dirs_list.selection_get()
        if os.path.isdir(os.path.join(core.PATH, d1)):
            if len(self.last_dir) > 0:
                if d1 == '..':
                    if len(self.last_dir) > 1:
                        core.PATH = self.last_dir.pop()  # Возврат на одну директорию вверх
                    else:
                        core.PATH = self.last_dir[0]
                elif d1 == '' or d1 is None:
                    core.PATH = self.last_dir[-1]
                else:
                    if core.PATH != self.last_dir[0]:
                        self.last_dir.append(core.PATH)  # Сохранение текущей директории "last_dir"
                    core.PATH = os.path.join(core.PATH, d1)  # Создание абсолютного пути
            else:
                core.PATH = self.drive
                self.last_dir.append(self.drive)
        try:
            new_dirs = os.listdir(core.PATH)
        except:
            new_dirs = os.listdir(self.drive)
        self.dirs_list.delete(0, END)
        self.dirs_list.insert(END, '..')
        self.dirs_list.selection_set(0)
        for i in sorted(new_dirs):
            if os.path.isdir(os.path.join(core.PATH, i)):
                self.dirs_list.insert(END, i)
        self.refresh_txtlist(core.PATH)

    def refresh_txtlist(self, path):
        if os.path.isdir(path):
            self.make_txt_list(path)
            if len(path) > 70:
                path2 = self.last_path[0]  # +'..  ..'+path[-65:]
            else:
                path2 = path
            if self.last_path != path:
                self.last_path = core.last_used_path(core.HOME, path, 'w')
            self.lab_path.configure(text=path2)

    def only_draw_dirs(self):
        self.last_dir = []
        try:
            old_selection = self.file_list.curselection()[0]
        except:
            old_selection = 0
        try:
            new_dirs = os.listdir(core.PATH)
        except:
            new_dirs = os.listdir(self.drive)
        self.dirs_list.delete(0, END)
        self.dirs_list.insert(END, '..')
        self.dirs_list.selection_set(old_selection)
        self.dirs_list.see(old_selection)
        for i in sorted(new_dirs):
            if os.path.isdir(os.path.join(core.PATH, i)):
                self.dirs_list.insert(END, i)
        t = core.PATH.split(p_sep)
        t2 = t[0] + p_sep
        self.last_dir.append(t2)
        i = 1
        while i < len(t) - 1:
            t2 = os.path.join(t2, t[i])
            self.last_dir.append(t2)
            i += 1

    def dir_list_show(self, *event):
        if self.dir_list_opened:
            self.dir_list_widget_window.destroy()
            self.refresh_txtlist(core.PATH)
            self.dir_list_opened = False
        else:
            self.dir_list_widget()
            self.refresh_txtlist(core.PATH)
            self.dir_list_opened = True

    def dirs_window_destroy(self, *event):
        if self.dir_list_opened:
            self.dir_list_widget_window.destroy()
            self.refresh_txtlist(core.PATH)
            self.dir_list_opened = False

    def dir_list_widget(self):
        self.dir_list_widget_window = Toplevel()
        self.dir_list_opened = True
        self.dir_list_widget_window.deiconify()
        self.dir_list_widget_window.title('Каталог')
        self.dir_list_widget_window.protocol('WM_DELETE_WINDOW', self.dirs_window_destroy)
        geom = self.root.geometry().split('+')
        window_size = '200x320+'
        da, db = 25, 65
        self.dir_list_widget_window.geometry('{0}{1}+{2}'.format(window_size, int(geom[1]) + da, int(geom[2]) + db))
        self.dir_list_widget_window.resizable(False, False)
        lab_disk = ttk.Label(self.dir_list_widget_window, text='Выбор диска:')
        self.disk_list = ttk.Combobox(self.dir_list_widget_window, values=self.make_list(), width=6)
        lab_dir = ttk.Label(self.dir_list_widget_window, text='Выбор каталога:')
        self.dirs_list = Listbox(self.dir_list_widget_window, selectmode=SINGLE, height=15)
        scrs_lefty = ttk.Scrollbar(self.dir_list_widget_window, command=self.dirs_list.yview)
        self.dirs_list.configure(yscrollcommand=scrs_lefty.set)
        lab_disk.grid(row=0, column=0, sticky='nwse', padx=1, pady=1)
        self.disk_list.grid(row=1, column=0, sticky='we')
        lab_dir.grid(row=2, column=0, sticky='nwse', padx=1, pady=1)
        self.dirs_list.grid(row=3, column=0, sticky='nwe', padx=1, pady=1)
        scrs_lefty.grid(row=3, column=1, sticky='nws')
        self.disk_list.bind('<<ComboboxSelected>>', self.set_disk_but)
        self.dirs_list.bind('<Double-Button-1>', self.change_dir)
        self.dirs_list.bind('<Double-space>', self.change_dir)
        self.dirs_list.bind('<Return>', self.change_dir)
        self.only_draw_dirs()

    def refresh(self):
        self.refresh_txtlist(core.PATH)

    @staticmethod
    def normalize(var):
        var = str(var)
        if len(var) == 1:
            return var.zfill(2)
        else:
            return var

    def make_o3file(self):
        def make_txt_list_ZSD(directory):
            txtfiles = []
            try:
                for files in os.listdir(directory):
                    if files[-3:] == "txt" and files.count("-D") > 0:
                        txtfiles.append(files)
                    if files[0] == 'm' and files.split('_')[2] in ['ZD', 'SD']:
                        txtfiles.append(files)
            except:
                pass
            return txtfiles

        recalculate_source_files_value = self.var_recalculate_source_files.get()
        show_all_value = self.var_show_all.get()
        show_correct1_value = self.chk_var_show_correct1.get()
        gui.canvs_destroy(self.canvas_list)
        try:
            self.refresh_txtlist(core.PATH)
            self.dir_list_opened = False
        except:
            pass
        self.but_make_mean_file.configure(state=DISABLED)
        for i in self.buttons:
            i.configure(state=DISABLED)
        mode = self.uv.get()
        o3_mode = ''
        tex = ''
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
        self.current_data.configure(text='')
        self.lab_ozone.configure(text=tex)
        self.root.update()
        plotx, ploty = gui.update_geometry(self.root)
        txt = make_txt_list_ZSD(core.PATH)
        mean_file = 0
        start = PlotClass(self.root, self.right_panel, o3_mode, plotx, ploty, recalculate_source_files_value,
                          show_all_value,
                          self.chk_var_sens_z.get(),
                          self.chk_var_sens_s.get(),
                          self.var_scale, self.psZ, self.psS, self.canvas_list)
        if recalculate_source_files_value == 0:  # Чтение из файла
            column = {'ozone': -2, 'uva': -3, 'uvb': -2, 'uve': -1}
            # datetime_index = 0 # UTC
            datetime_index = 1  # Local time
            file_opened = 0  # File with ozone was opened
            if o3_mode == 'ozone':
                mode = 'Ozone'
            elif o3_mode in ['uva', 'uvb', 'uve']:
                mode = 'UV'
            path_name = os.path.split(core.PATH)
            directory = mode.join(path_name[0].split('Mesurements'))
            name0 = 'm{}_{}_{}.txt'.format(core.DEVICE_ID, mode, path_name[1].replace('-', ''))
            file = os.path.join(directory, name0)
            if mode == 'Ozone':
                # Mean file
                if show_correct1_value == 0:
                    mean_file = 1
                    name = 'mean_' + name0
                    file = os.path.join(directory, name)
                    if not os.path.exists(file):
                        # Read manual saved mean file
                        name = 'mean_New_' + name0
                        file = os.path.join(directory, name)
                # Common file
                elif show_correct1_value == 1:
                    mean_file = 0
                    name = name0
                    file = os.path.join(directory, name)
                    if not os.path.exists(file):
                        # Read manual saved file
                        name = 'New_' + name0
                        file = os.path.join(directory, name)
            elif mode == 'UV':
                if not os.path.exists(file):
                    # Read manual saved file
                    name = 'New_' + name0
                    file = os.path.join(directory, name)
            if os.path.exists(file):
                with open(file, errors='ignore') as f:
                    file_opened = 1
                    data_raw = f.readlines()
                    delimiter = '\t'
                    if mode == 'Ozone':

                        use_correct = 1
                        if data_raw[0].count('Correct') == 0:
                            column['ozone'] = -1
                            use_correct = 0
                        elif data_raw[0].count('Correct') == 1:
                            column['ozone'] = -2
                        elif data_raw[0].count('Correct') == 2:
                            column['ozone'] = [-4, -2]
                            delimiter = ';'
                        data = [i for i in data_raw if i[0].isdigit()]
                        for i in data:
                            line_arr = [j for j in i.split(delimiter) if j != '']
                            if use_correct:
                                if column['ozone'] == [-4, -2]:
                                    if "1" in self.show_ozone_pairs:
                                        if int(line_arr[-1]) or show_all_value:
                                            start.x1.append(
                                                datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                            start.y1.append(int(line_arr[column[o3_mode][0]]))
                                    if "2" in self.show_ozone_pairs:
                                        if int(line_arr[-1]) or show_all_value:
                                            start.x2.append(
                                                datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                            start.y2.append(int(line_arr[column[o3_mode][1]]))
                                if column['ozone'] == -2:
                                    if int(line_arr[-1]) or show_all_value:
                                        start.x2.append(
                                            datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                        start.y2.append(int(line_arr[column[o3_mode]]))
                        sr = {"1": 0, "2": 0}
                        if start.y1:
                            sr["1"] = int(np.mean(start.y1))
                        if start.y2:
                            sr["2"] = int(np.mean(start.y2))
                        tex = "Среднее значение озона\n"
                        for pair in self.show_ozone_pairs:
                            tex += "(P{}): {} е.Д.\n".format(pair, sr[pair])
                    elif mode == 'UV':
                        if data_raw[0].count('\t') == 0:
                            delimiter = ';'
                        data = [i for i in data_raw if i[0].isdigit()]
                        for i in data:
                            line_arr = [j for j in i.split(delimiter) if j != '']
                            start.x1.append(datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                            start.y1.append(int(line_arr[column[o3_mode]]))

            if file_opened:
                if len(start.x1) == 0 and len(start.x2) == 0:
                    tex = "Корректных значений озона в файле не найдено!\n" \
                          "Попробуйте отключить корректировку\n({})".format(os.path.basename(file))
            else:
                tex = "Конечного файла измерений не найдено!\n" \
                      "(Вы точно находитесь в папке:\n" \
                      "{0}{1}Ufos_{2}{1}Mesurements?)".format(core.HOME, p_sep, core.DEVICE_ID)

        else:  # Пересчёт
            mean_file = 0
            self.ts, self.shs, self.calc_results = [], [], []
            save_class = calc.SaveFile(annual_file=False, but_make_mean_file=self.but_make_mean_file)
            for i in txt:
                start.uvs_or_o3['ZD'] = {}
                start.uvs_or_o3['SD'] = {}

                chan = ''
                file = os.path.join(core.PATH, i)
                if o3_mode == 'ozone':
                    chan = 'ZD'
                    if i.count("Z-D") > 0 or i.count("ZD") > 0:
                        start.data = start.get_spectr(file)
                        start.calc_ozone()
                        # t - datetime utc
                        # sh - sunheight
                        # cr - o3
                        t, sh, cr = save_class.prepare(start.data,
                                                       start.uvs_or_o3['ZD'])
                        self.ts.append(t)
                        self.shs.append(sh)
                        self.calc_results.append(cr)
                elif o3_mode in ['uva', 'uvb', 'uve']:
                    chan = 'SD'
                    if i.count("S-D") > 0 or i.count("SD") > 0:
                        start.data = start.get_spectr(file)
                        arr = ['uva', 'uvb', 'uve']
                        arr.remove(o3_mode)
                        for o3_m in arr:
                            start.calc_uv(o3_m, False)
                        start.calc_uv(o3_mode, True)
                        # t - datetime utc
                        # sh - sunheight
                        # cr - uv
                        t, sh, cr = save_class.prepare(start.data,
                                                       start.uvs_or_o3['SD'])
                        self.ts.append(t)
                        self.shs.append(sh)
                        self.calc_results.append(cr)
            if start.x1:
                self.but_save_to_final_file.configure(
                    command=lambda: save_class.save(chan, self.ts, self.shs, self.calc_results))
            else:
                tex = 'Файлов измерений\nне найдено'
        try:
            if start.x1:
                self.lab_current_data.configure(text='Дата: {0}'.format(start.x1[0]))
                if o3_mode == 'ozone':
                    s = {"1": {"o3": start.y1}, "2": {"o3": start.y2}}
                    for o3_pair in ["1", "2"]:
                        try:
                            s[o3_pair]["mean"] = int(sum(s[o3_pair]["o3"]) // len(s[o3_pair]["o3"]))
                        except:
                            s[o3_pair]["mean"] = 0
                    tex = "Среднее значение озона\n"
                    for pair in self.show_ozone_pairs:
                        tex += "(P{}): {} е.Д.\n".format(pair, s[pair]["mean"])
                elif o3_mode == 'uva':
                    tex = 'УФ-А'
                elif o3_mode == 'uvb':
                    tex = 'УФ-Б'
                elif o3_mode == 'uve':
                    tex = 'УФ-Э'
                o3_plotted = 1
            else:
                o3_plotted = 0
            if mean_file:
                tex += ' .'
            else:
                tex += ''
            start.plot(core.PATH)

        except Exception as err:
            print('plotter.make_o3file():', end='')
            print(err, sys.exc_info()[-1].tb_lineno)
            raise err

        finally:
            self.lab_ozone.configure(text=tex)
            self.lab_uva.configure(text='')
            self.lab_uvb.configure(text='')
            self.lab_uve.configure(text='')
            self.lab_sun.configure(text='')

        for i in self.buttons:
            i.configure(state=NORMAL)

        if not recalculate_source_files_value:
            self.but_save_to_final_file.configure(state=DISABLED)
            self.but_make_mean_file.configure(state=DISABLED)

    def make_list(self):
        if os.name == 'posix':
            self.disks = '/'
        else:
            alp = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                   'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
            self.disks = []
            for i in alp:
                try:
                    os.chdir(i + ':\\')
                    self.disks.append(os.getcwd()[:1])
                except:
                    pass
        return tuple(self.disks)


if __name__ == "__main__":
    Main("1")
