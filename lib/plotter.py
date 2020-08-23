# Version: 2.0
# Modified: 12.07.2019
# Author: Sergey Talash
from shutil import copy
import gc
from lib import core

from sys import platform as sys_pf

if sys_pf == 'darwin':
    import matplotlib

    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tkinter import font

from tkinter import NORMAL
from lib.core import *
from lib.calculations import *


class PlotClass:
    def __init__(self, window, o3_mode, plotx, ploty, recalculate_value, show_all, use_sensitivity):
        """

        Args:
            window (ttk.Frame):  where graph is created
            o3_mode (str): Mode of measurements ('spectr', 'ozone', 'uva', 'uvb', 'uve')
            plotx (int): Width of picture in pixels
            ploty (int): Height of picture in pixels
            recalculate_value (bool): Read measured files (1 or 0)
            show_all (bool): Show all calculated values, ignore correction filters (1 or 0)
            use_sensitivity (bool): Use sensitivity (1 or 0)
        """
        global canvs
        self.show_all = show_all
        self.use_sensitivity = use_sensitivity
        self.recalculate_value = recalculate_value
        self.plotx = plotx
        self.ploty = ploty
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
        self.spectr = []
        self.uvs_or_o3 = {}
        self.ozon = 0
        self.fig, self.ax = plt.subplots(1)
        plt.subplots_adjust(left=0.07, right=0.97, bottom=0.07, top=0.95)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.nexday_allow_flag = 0
        self.dates = []
        self.hss = []
        self.ozons = []
        self.spectrum = []
        self.oldfilelist = os.listdir(path)
        self.hours = mdates.HourLocator()
        self.minutes = mdates.MinuteLocator()
        self.DateFmt = mdates.DateFormatter('%H:%M')
        if self.o3_mode in ['ozone', 'uva', 'uvb', 'uve']:
            self.point = 'o'
        elif self.o3_mode == 'spectr':
            self.point = '-'
        # Calc ozone
        self.o3 = {}
        self.uvs_or_o3['ZD'] = {}
        self.prom = int(PARS['calibration2']['pix+-'] / eval(self.confZ[1]))
        self.f = PARS['station']['latitude']
        self.l = PARS['station']['longitude']
        self.pelt = int(PARS['station']['timezone'])
        self.y1 = []
        self.y2 = []
        self.x1 = []
        self.x2 = []
        # self.sh1 = []
        # self.sh2 = []
        # Calc UV
        self.uv = 0
        self.uvs_or_o3['SD'] = {}
        self.curr_o3_dict = {'uva': [2, P1_UVA, P2_UVA],
                             'uvb': [3, P1_UVB, P2_UVA],
                             'uve': [4, P1_UVE, P2_UVE]}

    def calc_ozon(self):
        self.spectrum = spectr2zero(self.data['spectr'])
        """Расчет озона"""
        self.o3 = {}
        correct = {}
        addational_data = {}
        for pair, values in LAMBDA_CONSTS.items():
            self.o3[pair], correct[pair], addational_data[pair] = pre_calc_o3(
                LAMBDA_CONSTS[pair],
                LAMBDA_CONSTS_PIX[pair],
                self.spectrum,
                self.prom,
                self.data['mu'],
                pair)
        self.uvs_or_o3['ZD'] = {'o3_1': self.o3["1"],
                                'o3_2': self.o3["2"],
                                'correct_1': correct["1"],
                                'correct_2': correct["2"],
                                'additional_data_1': addational_data["1"],
                                'additional_data_2': addational_data["2"]}
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
        self.spectrum = spectr2zero(self.data['spectr'])
        ultraviolet = 0
        try:
            if uv_mode in ['uva', 'uvb']:
                if self.use_sensitivity:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]) * np.array(self.sensitivity[p1:p2]))
                else:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]))
                ultraviolet *= float(eval(self.confS[1])) * PARS['device']['graduation_expo'] / \
                                   self.data['expo']
            elif uv_mode == 'uve':
                if self.use_sensitivity:
                    ultraviolet = sum([float(self.spectrum[i]) *
                                       self.sensitivity_eritem[i] *
                                       self.sensitivity[i] for i in range(p1, p2, 1)]
                                      )
                else:
                    ultraviolet = sum([float(self.spectrum[i]) * self.sensitivity_eritem[i] for i in range(p1, p2, 1)])

                    ultraviolet *= float(eval(self.confS[1])) * PARS['device']['graduation_expo'] / \
                                   self.data['expo']
                    ultraviolet *= float(PARS['calibration']['{}_koef'.format(uv_mode)])
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
            with open(file_path) as f:
                data = json.load(f)
                if flag:
                    new_data = {'spectr': data['spectr'],
                                'datetime': datetime.datetime.strptime(data['mesurement']['datetime_local'],
                                                                       '%Y%m%d %H:%M:%S'),
                                'hs': data['calculated']['sunheight'],
                                'amas': data['calculated']['amas'],
                                'mu': data['calculated']['mu'],
                                'expo': data['mesurement']['exposition'],
                                'accumulate': data['mesurement']['accummulate'],
                                'channel': data['mesurement']['channel']
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
            show_error_in_separate_window(err, "Ufos measurement file is invalid.")
        except Exception as err:
            show_error_in_separate_window(err)

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
                    new_data['datetime'] = datetime.datetime.strptime(
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
        while len(canvs) > 0:
            canvas_i, fig_i = canvs.pop()
            fig_i.clf()
            canvas_i.get_tk_widget().destroy()
        self.fig.clf()
        plt.close()
        gc.collect()
        self.plotx, self.ploty = update_geometry(root)
        self.fig, self.ax = plt.subplots(1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)

    def set_x_limit(self, x, y, x_min, x_max, y_min, y_max, mode):
        if self.o3_mode != 'ozone':
            if max(x) > x_max: x_max = max(x)
            if min(x) < x_min: x_min = min(x)
            # if max(y) > y_max: y_max = max(y) * 1.05
            y_max = max(y[slice(*PARS['device']['pix_work_interval'])])
            # if min(y) < y_min: y_min = min(y) * 0.95
            y_min = min(y)
        else:
            if max(x) > x_max: x_max = max(x)
            if min(x) < x_min: x_min = min(x)
            y_max = self.ozone_y_max
            y_min = self.ozone_y_min
        if mode == 'hour':
            self.ax.set(xlim=[x_min - datetime.timedelta(minutes=15),
                              x_max + datetime.timedelta(minutes=15)],
                        ylim=[y_min, y_max])
            self.ax.xaxis.set_major_locator(mdates.HourLocator())
            self.ax.xaxis.set_minor_locator(mdates.MinuteLocator(np.arange(0, 60, 10)))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif mode == 'degree':
            self.ax.set(xlim=[x_min - 0.5, x_max + 0.5], ylim=[y_min, y_max])
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    def plot(self, path):
        global canvs
        self.zen_path = path
        self.fig_prepare()

        self.fig.set_size_inches(self.plotx / 82, self.ploty / 80)
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
            print('new spectr')
            self.ax.set_xlabel('nm')
            self.ax.set_ylabel('mV')
            conf = self.confZ
            if 'S' in self.data['channel']:
                conf = self.confS
            self.ax.set_ylabel('mWt/m^2*nm')
            if self.use_sensitivity:  # Use sensitivity
                new_spectr = []
                for index, value in enumerate(self.spectrum):
                    new_spectr.append(
                        value * self.sensitivity[index] * var_settings['device']['graduation_expo'] / self.data['expo'])
                self.spectrum = new_spectr
            self.ax.plot([pix2nm(conf, index, 3, 0) for index, value in enumerate(self.spectrum)],
                         self.spectrum,
                         self.point,
                         color='k')
            if var_top.get():
                self.max_y = max(self.spectrum[slice(*PARS['device']['pix_work_interval'])]) + 100
            else:
                self.max_y = 4096
            if self.data['channel'].count('Z') > 0:
                ps = psZ
            else:
                ps = psS

            for key in ps.keys():
                for point in ps[key]:
                    point_nm = pix2nm(conf, point, 1, 0)
                    self.ax.plot([point_nm] * 2, [0, self.max_y], '--', color='red')
                    self.ax.text(point_nm, self.max_y - 50, str(point_nm), horizontalalignment='center')

            self.ax.set(xlim=[pix2nm(conf, 0, 1, 0), pix2nm(conf, 3692, 1, 0)], ylim=[0, self.max_y])
            self.ax.grid(True)

            self.fig.canvas.draw()
        else:
            self.ax.set_xlabel('Time')
            # ====================== Ozone ======================
            if self.o3_mode == 'ozone':
                print('new ozone')
                self.ax.set_ylabel('o3')
            # ====================== UV =========================
            elif self.o3_mode == 'uva':
                self.ax.set_ylabel('mWt/m^2')
                print('new uva')
            elif self.o3_mode == 'uvb':
                self.ax.set_ylabel('mWt/m^2')
                print('new uvb')
            elif self.o3_mode == 'uve':
                self.ax.set_ylabel('mWt/m^2')
                print('new uve')
            # ===================================================
            for x_mas, y_mas, color in zip([self.x1, self.x2], [self.y1, self.y2], ['blue', 'green']):
                if y_mas:
                    tmp_y = []
                    tmp_x = []
                    # print([_sh])
                    for x, y in zip(x_mas, y_mas):
                        if y < 0:
                            y = 0
                        # print([var_settings["calibration2"]["visible_sunheight_min"],
                        #        s,
                        #        var_settings["calibration2"]["visible_sunheight_max"]])
                        # if var_settings["calibration2"]["visible_sunheight_min"] < s < var_settings["calibration2"]["visible_sunheight_max"]:
                        tmp_y.append(y)
                        tmp_x.append(x)
                    y_mas = tmp_y
                    x_mas = tmp_x
                    self.ax.plot(x_mas, y_mas, self.point, color=color)
                    self.set_x_limit(x_mas, y_mas, min(x_mas), min(x_mas) + datetime.timedelta(hours=2),
                                     100,
                                     600,
                                     'hour')
            self.ax.grid(True)
            self.fig.canvas.draw()
            gui.canvs_destroy(canvs)

        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        canvs.append((canvas, self.fig))
        canvas.draw()


# def send_all_files_plotter():
#     lab_err.configure(text='')
#     root.update()
#     for i in os.listdir(path):
#         if i.find('-D') != -1:
#             file2send = os.path.join(path, i)
#             tex = send_files(home, file2send)
#             if tex != 'OK':
#                 print(tex)
#             lab_err.configure(text=i + tex)
#             root.update()


def check_code(*event):
    code = ent_code.get()
    if code == '9':
        obj_grid()
    else:
        change_privileges(common, 0)


def obj_grid():
    r = 0
    c = 0
    bit = 1
    for i in main_menu_obj:
        i.grid(row=r, column=c, sticky='we')
        c += 1
    r += 1
    c = 0
    admin_panel.grid(row=r, column=c, sticky='nwe')
    but_annual_ozone.configure(command=lambda: AnnualOzone(home, ent_year.get(), start, root, but_annual_ozone).run())
    if not var_recalculate_source_files.get():
        but_save_to_final_file.configure(state=DISABLED)
        but_make_mean_file.configure(state=DISABLED)
    for i in admin_menu_obj:
        i.grid(row=r, column=c, sticky='we')
        c += 1
        if admin_menu_obj.index(i) > 4 and bit:
            r += 1
            c = 0
            bit = 0


def change_privileges(priv, on_off):
    """Скрыть сервисную панель"""
    admin_panel.grid_forget()


def window_closed():
    global root
    root.quit()
    root.destroy()


def plot_more():
    pass


def set_disk_but(event):
    global path
    global drive
    if os.name != 'posix':
        path = disks[disk_list.current()] + ':\\'
    else:
        path = p_sep
    print(path)
    drive = path
    only_draw_dirs()
    refresh_txtlist(path)





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
        copy(file_old, file_new)
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


def first_clear_plot(plotx, ploty, some_root):
    refresh_txtlist(path)
    dir_list_widget.opened = False
    start = PlotClass(some_root, 'first', plotx, ploty, 1, 0, 0)
    start.plot(path)
    return start


def make_txt_list(directory):
    global file_list
    txtfiles = []
    try:
        old_selection = file_list.curselection()[0]
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

        file_list.delete(0, END)
        for i in sorted(txtfiles):
            file_list.insert(END, i)
        file_list.selection_set(old_selection)
        file_list.see(old_selection)
    except:
        pass
    return txtfiles


def plot_spectr(*event):
    # ===== SPECTR =====
    uv.set(4)
    for i in buttons:
        i.configure(state=DISABLED)
    lab_ozon.configure(text='Значение озона: ')
    for mode, var in zip(['uva', 'uvb', 'uve'], [lab_uva, lab_uvb, lab_uve]):
        var.configure(text='Значение UV-{}: '.format(mode[-1].upper()))
    root.update()
    plotx, ploty = update_geometry(root)
    start = PlotClass(right_panel, 'spectr', plotx, ploty, 1, 0, chk_var_with_sens.get())
    try:
        file = file_list.selection_get()
    except TclError:
        file_list.selection_set(0)
        file = file_list.selection_get()
    start.data = start.get_spectr(os.path.join(path, file))
    if start.data['channel'].count("Z-D") > 0 or start.data['channel'].count("ZD") > 0:
        try:
            start.calc_ozon()
            lab_ozon.configure(text='\n'.join(
                    ['Значение озона'] + ['(P{}): {} е.Д.'.format(pair, start.o3[pair]) for pair in show_ozone_pairs]))
        except TclError:
            pass
    if start.data['channel'].count("S-D") > 0 or start.data['channel'].count("SD") > 0:
        for mode, var in zip(['uva', 'uvb', 'uve'], [lab_uva, lab_uvb, lab_uve]):
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
    currnt_data.configure(text=data)
    start.x2 = range(len(start.spectrum))
    start.y2 = start.spectrum
    start.plot(path)
    for i in buttons:
        i.configure(state=NORMAL)


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
    except:
        new_dirs = os.listdir(drive)
    dirs_list.delete(0, END)
    dirs_list.insert(END, '..')
    dirs_list.selection_set(0)
    for i in sorted(new_dirs):
        if os.path.isdir(os.path.join(path, i)):
            dirs_list.insert(END, i)
    refresh_txtlist(path)


def refresh_txtlist(path):
    global last_path
    global lab_path
    if os.path.isdir(path):
        make_txt_list(path)
        if len(path) > 70:
            path2 = last_path[0]  # +'..  ..'+path[-65:]
        else:
            path2 = path
        if last_path != path:
            last_path = last_used_path(home, path, 'w')
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
    if dir_list_widget.opened:
        dir_list_widget.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list_widget.opened = False
    else:
        dir_list_widget(path)
        refresh_txtlist(path)
        dir_list_widget.opened = True


def dirs_window_destroy(*event):
    if dir_list_widget.opened:
        dir_list_widget.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list_widget.opened = False


def dir_list_widget(set_dir):
    global dirs_list
    global disk_list
    dir_list_widget.window = Toplevel()
    dir_list_widget.opened = True
    dir_list_widget.window.deiconify()
    dir_list_widget.window.title('Каталог')
    dir_list_widget.window.protocol('WM_DELETE_WINDOW', dirs_window_destroy)
    geom = root.geometry().split('+')
    AxB = '200x320+'
    da, db = 25, 65
    dir_list_widget.window.geometry('{0}{1}+{2}'.format(AxB, int(geom[1]) + da, int(geom[2]) + db))
    dir_list_widget.window.resizable(False, False)
    lab_disk = ttk.Label(dir_list_widget.window, text='Выбор диска:')
    disk_list = ttk.Combobox(dir_list_widget.window, values=make_list(), width=6)
    lab_dir = ttk.Label(dir_list_widget.window, text='Выбор каталога:')
    dirs_list = Listbox(dir_list_widget.window, selectmode=SINGLE, height=15)
    scrs_lefty = ttk.Scrollbar(dir_list_widget.window, command=dirs_list.yview)
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


def normalize(var):
    var = str(var)
    if len(var) == 1:
        return var.zfill(2)
    else:
        return var


def update_geometry(root):
    plotx, ploty = root.winfo_screenwidth() / 1.5, root.winfo_screenheight() / 1.5
    # geom = root.geometry().split('+')[0].split('x')
    # if geom[0] == '1' or geom[1] == '1':
    #     (plotx, ploty) = root.maxsize()
    #     plotx -= 225
    #     ploty -= 110
    # else:
    #     from PIL.ImageChops import screen
    #
    #     # plotx = int(geom[0]) - 225
    #     # ploty = int(geom[1]) - 70
    # print((plotx, ploty))
    return plotx, ploty


def make_o3file():
    global path
    global curr_o3
    global canvas
    global canvs
    global gr_ok
    global curr_time
    global o3_plotted
    global root
    global o3_mod

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

    recalculate_source_files_value = var_recalculate_source_files.get()
    show_all_value = var_show_all.get()
    show_correct1_value = chk_var_show_correct1.get()
    canvs_destroy(canvs)
    try:
        dir_list_widget.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list_widget.opened = False
    except:
        pass
    but_make_mean_file.configure(state=DISABLED)
    for i in buttons:
        i.configure(state=DISABLED)
    mode = uv.get()
    #    mode=0
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
    currnt_data.configure(text='')
    lab_ozon.configure(text=tex)
    root.update()
    plotx, ploty = update_geometry(root)
    curr_time = []
    txt = make_txt_list_ZSD(path)
    gr_ok = 0
    mean_file = 0
    start = PlotClass(right_panel, o3_mode, plotx, ploty, recalculate_source_files_value, show_all_value,
                      chk_var_with_sens.get())
    if recalculate_source_files_value == 0:  # Чтение из файла
        column = {'ozone': -2, 'uva': -3, 'uvb': -2, 'uve': -1}
        # datetime_index = 0 # UTC
        datetime_index = 1  # Local time
        file_opened = 0  # File with ozone was opened
        if o3_mode == 'ozone':
            mode = 'Ozone'
        elif o3_mode in ['uva', 'uvb', 'uve']:
            mode = 'UV'
        path_name = os.path.split(path)
        directory = mode.join(path_name[0].split('Mesurements'))
        name0 = 'm{}_{}_{}.txt'.format(start.var_settings['device']['id'], mode, path_name[1].replace('-', ''))
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
            print("Read:", file)
        elif mode == 'UV':
            if not os.path.exists(file):
                # Read manual saved file
                name = 'New_' + name0
                file = os.path.join(directory, name)
        if os.path.exists(file):
            with open(file) as f:
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
                                if "1" in show_ozone_pairs:
                                    if int(line_arr[-1]) or show_all_value:
                                        start.x1.append(
                                                datetime.datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                        start.y1.append(int(line_arr[column[o3_mode][0]]))
                                if "2" in show_ozone_pairs:
                                    if int(line_arr[-1]) or show_all_value:
                                        start.x2.append(
                                                datetime.datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                        start.y2.append(int(line_arr[column[o3_mode][1]]))
                            if column['ozone'] == -2:
                                if int(line_arr[-1]) or show_all_value:
                                    start.x2.append(
                                            datetime.datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                                    start.y2.append(int(line_arr[column[o3_mode]]))
                    sr = {"1": 0, "2": 0}
                    if start.y1:
                        sr["1"] = int(np.mean(start.y1))
                    if start.y2:
                        sr["2"] = int(np.mean(start.y2))
                    tex = "Среднее значение озона\n"
                    for pair in show_ozone_pairs:
                        tex += "(P{}): {} е.Д.\n".format(pair, sr[pair])
                elif mode == 'UV':
                    if data_raw[0].count('\t') == 0:
                        delimiter = ';'
                    data = [i for i in data_raw if i[0].isdigit()]
                    for i in data:
                        line_arr = [j for j in i.split(delimiter) if j != '']
                        start.x1.append(datetime.datetime.strptime(line_arr[datetime_index], '%Y%m%d %H:%M:%S'))
                        start.y1.append(int(line_arr[column[o3_mode]]))

        if file_opened:
            if len(start.x1) == 0 and len(start.x2) == 0:
                tex = "Корректных значений озона в файле не найдено!\nПопробуйте отключить корректировку\n({})".format(
                        os.path.basename(file))
        else:
            tex = """Конечного файла измерений не найдено!
(Вы точно находитесь в папке:
{0}{1}Ufos_{2}{1}Mesurements?)""".format(home, p_sep, start.var_settings['device']['id'])

    else:  # Пересчёт
        mean_file = 0
        global ts
        global shs
        global calc_results
        ts, shs, calc_results = [], [], []
        saving = FinalFile(annual_file=False, but_make_mean_file=but_make_mean_file)
        for i in txt:
            start.uvs_or_o3['ZD'] = {}
            start.uvs_or_o3['SD'] = {}

            chan = ''
            if i.count("Z-D") > 0 or i.count("ZD") > 0:
                color = 'black'
            else:
                color = 'blue'
            file = os.path.join(path, i)
            if o3_mode == 'ozone':
                chan = 'ZD'
                if i.count("Z-D") > 0 or i.count("ZD") > 0:
                    start.data = start.get_spectr(file)
                    start.calc_ozon()
                    # t - datetime utc
                    # sh - sunheight
                    # cr - o3
                    t, sh, cr = saving.prepare(start.data['datetime'],
                                               start.uvs_or_o3['ZD'])
                    ts.append(t)
                    shs.append(sh)
                    calc_results.append(cr)
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
                    t, sh, cr = saving.prepare(start.data['datetime'],
                                               start.uvs_or_o3['SD'])
                    ts.append(t)
                    shs.append(sh)
                    calc_results.append(cr)
        if start.x1:
            but_save_to_final_file.configure(
                    command=lambda: saving.save(start.var_settings, home, chan, ts, shs, calc_results))
        else:
            tex = 'Файлов измерений\nне найдено'
    try:
        if start.x1:
            lab_currnt_data.configure(text='Дата: {0}'.format(start.x1[0]))
            if o3_mode == 'ozone':
                s = {"1": {"o3": start.y1}, "2": {"o3": start.y2}}
                for o3_pair in ["1", "2"]:
                    try:
                        s[o3_pair]["mean"] = int(sum(s[o3_pair]["o3"]) // len(s[o3_pair]["o3"]))
                    except:
                        s[o3_pair]["mean"] = 0
                tex = "Среднее значение озона\n"
                for pair in show_ozone_pairs:
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
        start.plot(path)

    except Exception as err:
        print('plotter.make_o3file():', end='')
        print(err, sys.exc_info()[-1].tb_lineno)
        raise err

    finally:
        lab_ozon.configure(text=tex)
        lab_uva.configure(text='')
        lab_uvb.configure(text='')
        lab_uve.configure(text='')
        lab_sun.configure(text='')

    for i in buttons:
        i.configure(state=NORMAL)

    if not recalculate_source_files_value:
        but_save_to_final_file.configure(state=DISABLED)
        but_make_mean_file.configure(state=DISABLED)


class Main:
    def __init__(self, show_ozone_pairs):
        self.show_ozone_pairs = show_ozone_pairs
        self.human_error_text = ""
        self.ts, self.shs, self.calc_results = [], [], []
        self.human_error_text = "Common settings file is invalid"
        self.common_pars = Settings.get_common(self.home)
        self.human_error_text = "Ufos settings file is invalid"
        if os.name != 'posix':
            self.drive = os.getcwd()[:3]
        else:
            self.drive = p_sep
        self.path2 = ''
        self.o3min = 200
        self.ozon_scale_max = 600
        self.color = 'black'
        self.ima = []
        self.label = ''
        self.o3srednee = ''
        self.bit = 1
        self.ok = 1
        self.scale_printed = 0
        self.canvs = []
        self.last_path = last_used_path(self.home, self.path, 'r')
        try:
            if self.path != self.last_path and os.path.exists(self.last_path):
                self.path = self.last_path
            else:
                pass
        except:
            self.path = self.home
        self.curr_o3 = [0, 0, 0, 0, 0]
        try:
            # Check if file exists
            self.human_error_text = 'Чувствительность прибора УФОС' \
                         ' sensitivity{} - не найдена в каталоге программы!'.format(PARS['device']['id'])
            read_sensitivity(self.home, PARS['device']['id'], "sensitivityS")  # Световая чувствительность прибора
            self.human_error_text = 'Чувствительность прибора УФОС' \
                         ' senseritem{} - не найдена в каталоге программы!'.format(PARS['device']['id'])
            read_sensitivity(self.home, PARS['device']['id'], "senseritem")  # Эритемная Чувствительность прибора
        except Exception as err:
            raise err
        self.curr_time = []
        self.gr_ok = 2
        self.o3_mode = ''
        self.o3_plotted = 1
        """
        gr_ok = 0 - озон расчитывается, график не строится
        gr_ok = 1 - озон не расчитывается, график строится
        gr_ok = 2 - озон расчитывается, график строится
        """
        self.appHighlightFont = font.Font(family='Helvetica', size=14)  # , weight='bold')

    def init_gui(self):
        try:
            self.root = Tk()
            self.plotx, self.ploty = update_geometry(self.root)
            self.root.title('УФОС Просмотр')
            self.root.protocol('WM_DELETE_WINDOW', window_closed)
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
            self.chk_var_with_sens = IntVar()
            self.chk_var_with_sens.set(1)
            self.chk_with_sens = ttk.Checkbutton(
                self.admin_panel,
                                                 text='Использовать чувствительность',
                                                 variable=self.chk_var_with_sens)
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
            self.chk_show_correct1 = ttk.Checkbutton(self.admin_panel, text='Откл Корр 1', variable=self.chk_var_show_correct1)
            self.but_save_to_final_file = ttk.Button(self.admin_panel, text='Сохранить в файл')
            self.but_make_mean_file = ttk.Button(self.admin_panel, text='Сохранить в файл среднего')
            self.var_top = IntVar()
            self.var_top.set(1)
            self.rad_4096 = ttk.Radiobutton(self.admin_panel, text='Единая шкала', variable=self.var_top, value=0)
            self.rad_ytop = ttk.Radiobutton(self.admin_panel, text='Оптимальная шкала', variable=self.var_top, value=1)

            self.but_plot_more = ttk.Button(self.admin_panel, text='Подробный просмотр', command=plot_more)
            self.uv = IntVar()
            self.uv.set(4)
            self.but_remake = ttk.Button(self.admin_panel, text='Новый формат Z-D', command=b_remake)
            # but_send = ttk.Button(self.admin_panel, text=host, command=send_all_files_plotter)

            # Annual ozone calculations
            self.ent_year = ttk.Entry(self.admin_panel)
            self.ent_year.insert(0, "2018")
            self.but_annual_ozone = ttk.Button(self.admin_panel, text='Сохранить озон за год')

            self.admin_menu_obj = [self.chk_with_sens, self.chk_show_all, self.chk_show_correct1, self.chk_recalculate_source_files,
                              self.but_save_to_final_file,
                              self.but_make_mean_file,
                              self.rad_4096, self.rad_ytop, self.but_plot_more, self.but_remake,
                              # but_send
                              self.ent_year, self.but_annual_ozone
                              ]

            # Main Menu
            self.but_refresh = ttk.Button(self.menu_panel, text='Обновить', command=refresh)
            self.but_dir = ttk.Button(self.menu_panel, text='Выбор каталога', command=dir_list_show)
            self.rad_spectr = ttk.Radiobutton(self.menu_panel, text='Спектр', variable=uv, value=4, command=plot_spectr)
            self.rad_o3file = ttk.Radiobutton(self.menu_panel, text='Озон', variable=uv, value=0, command=make_o3file)
            self.rad_uva = ttk.Radiobutton(self.menu_panel, text='УФ-А', variable=uv, value=1, command=make_o3file)
            self.rad_uvb = ttk.Radiobutton(self.menu_panel, text='УФ-Б', variable=uv, value=2, command=make_o3file)
            self.rad_uve = ttk.Radiobutton(self.menu_panel, text='УФ-Э', variable=uv, value=3, command=make_o3file)
            self.ent_code = ttk.Entry(self.menu_panel, width=2)
            self.main_menu_obj = [self.but_refresh,
                                  self.but_dir, self.rad_spectr,
                                  self.rad_o3file, self.rad_uva,
                                  self.rad_uvb, self.rad_uve,
                                  self.ent_code]

            self.file_list = Listbox(self.left_panel, selectmode=SINGLE, height=16, width=28)
            self.scr_lefty = ttk.Scrollbar(self.left_panel, command=self.file_list.yview)
            self.file_list.configure(yscrollcommand=self.scr_lefty.set)
            self.lab_currnt_data = ttk.Label(self.left_panel, text='Данные: ')
            self.currnt_data = ttk.Label(self.left_panel, text='')
            self.lab_ozon = ttk.Label(self.left_panel, text='', foreground='blue', font=self.appHighlightFont)
            self.lab_uva = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_uvb = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_uve = ttk.Label(self.left_panel, text=': ', foreground='blue')
            self.lab_sun = ttk.Label(self.left_panel, text='')
            self.lab_path = ttk.Label(self.downline, text=self.path)
            self.lab_err = ttk.Label(self.downline, text='', width=20)

            self.buttons = self.main_menu_obj + self.admin_menu_obj

            """============== GUI Structure =============="""
            self.top_panel.grid(row=0, column=0, sticky='nwe', columnspan=4)
            self.menu_panel.grid(row=0, column=0, sticky='nwe')
            self.but_refresh.grid(row=0, column=0, sticky='w')
            self.but_dir.grid(row=0, column=1, sticky='w')

            obj_grid()

            # but_send.grid(row=0, column=10, sticky='w')
            self.ent_code.grid(row=0, column=13, sticky='e')
            self.right_panel.grid(row=1, column=3, sticky='nwse', padx=1)
            self.left_panel.grid(row=1, column=0, sticky='nwse', padx=1)
            self.file_list.grid(row=0, column=0, sticky='nwse', padx=1)
            self.scr_lefty.grid(row=0, column=1, sticky='nws')
            self.lab_currnt_data.grid(row=2, column=0, sticky='we', padx=1)
            self.lab_ozon.grid(row=3, column=0, sticky='we', padx=1)
            self.lab_uva.grid(row=4, column=0, sticky='we', padx=1)
            self.lab_uvb.grid(row=5, column=0, sticky='we', padx=1)
            self.lab_uve.grid(row=6, column=0, sticky='we', padx=1)
            self.lab_sun.grid(row=7, column=0, sticky='we', padx=1)
            self.currnt_data.grid(row=8, column=0, sticky='we', padx=1)
            """=============================================================="""
            self.confZ = PARS['calibration']['nm(pix)']['Z']
            self.confS = PARS['calibration']['nm(pix)']['S']

            self.points = PARS['calibration']['points']
            self.p_uva1, self.p_uva2 = nm2pix(315, self.confS, 0), nm2pix(400, self.confS, 0)
            self.p_uvb1, self.p_uvb2 = nm2pix(280, self.confS, 0), nm2pix(315, self.confS, 0)
            self.p_uve1, self.p_uve2 = 0, 3691  # nm2pix(290),nm2pix(420)

            self.p_zero = {pair: nm2pix(nm, self.confZ, 0) for pair, nm in zip(["1", "2"], [290, 295])}
            self.p_lamst = nm2pix(290, self.confZ, 0)
            # Массив констант лямбда в пикселях
            self.sZ = {}
            self.psS = {}
            for key in self.points.keys():
                self.psZ[key] = []
                self.psS[key] = []
                for point in self.points[key]:
                    self.psZ[key].append(nm2pix(point, self.confZ, 0))
                    self.psS[key].append(nm2pix(point, self.confS, 0))

            self.start = first_clear_plot(self.plotx, self.ploty, self.right_panel)

            # Скрыть следующие кнопки
            self.common = [self.rad_4096, self.rad_ytop, self.but_plot_more, self.but_remake]
            self.sertification = [self.rad_4096, self.rad_ytop, self.but_plot_more, self.rad_uva, self.rad_uvb, self.rad_uve, self.but_remake,
                             self.chk_recalculate_source_files,
                             self.but_save_to_final_file, self.but_make_mean_file]

            # Uncomment after debug will be finished
            change_privileges(common, 0)

            """=============================================================="""
            self.downline.grid(row=6, column=0, sticky='nswe', columnspan=4)
            self.lab_path.grid(row=0, column=0, sticky='w')
            self.lab_err.grid(row=0, column=1, sticky='e')

            """============== GUI Actions =============="""
            self.file_list.bind('<Double-Button-1>', plot_spectr)
            self.file_list.bind('<Return>', plot_spectr)
            self.file_list.bind('<Button-1>', dirs_window_destroy)
            self.canvas.bind('<Button-1>', dirs_window_destroy)
            self.left_panel.bind('<Button-1>', dirs_window_destroy)
            self.right_panel.bind('<Button-1>', dirs_window_destroy)
            self.ent_code.bind('<Return>', check_code)

            self.root.mainloop()
        except (FileNotFoundError, json.decoder.JSONDecodeError) as err:
            show_error_in_separate_window(err, self.human_error_text)
        except Exception as err:
            print(err)
        finally:
            self.root.destroy()


if __name__ == "__main__":
    pass
