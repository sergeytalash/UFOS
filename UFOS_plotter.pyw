# Version: 2.0
# Modified: 12.07.2019
# Author: Sergey Talash
import gc
from shutil import copy
from sys import platform as sys_pf
from tkinter import font

if sys_pf == 'darwin':
    import matplotlib

    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from procedures import *


def canvs_destroy(canvs):
    # global timer
    # try:
    #     timer.stop()
    # except:
    #     pass
    for i in canvs:
        try:
            i.get_tk_widget().destroy()
        except TclError:
            pass
    gc.collect()


class PlotClass:
    def __init__(self, window, o3_mode, plotx, ploty, recalculate_value, show_all, use_sensitivity):
        """

        :param window: ttk.Frame where graph is created
        :param o3_mode: Mode of measurements ('spectr', 'ozone', 'uva', 'uvb', 'uve')
        :param plotx: Width of picture in pixels
        :param ploty: Height of picture in pixels
        :param recalculate_value: Read measured files (1 or 0)
        :param show_all: Show all calculated values, ignore correction filters (1 or 0)
        :param use_sensitivity: Use sensitivity (1 or 0)
        """
        global timer
        global canvs
        self.show_all = show_all
        self.use_sensitivity = use_sensitivity
        self.recalculate_value = recalculate_value
        self.common_pars = Settings.get_common(home)
        self.var_settings = Settings.get_device(home, self.common_pars['device']['id'])
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
        self.fig = ''
        self.ax = ''
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
        self.confZ = self.var_settings['calibration']['nm(pix)']['Z']
        self.prom = int(self.var_settings['calibration2']['pix+-'] / eval(self.confZ[1]))
        self.f = self.var_settings['station']['latitude']
        self.l = self.var_settings['station']['longitude']
        self.pelt = int(self.var_settings['station']['timezone'])
        self.y1 = []
        self.y2 = []
        self.x1 = []
        self.x2 = []
        # self.sh1 = []
        # self.sh2 = []
        # Calc UV
        self.uv = 0
        self.uvs_or_o3['SD'] = {}
        self.curr_o3_dict = {'uva': [2, p_uva1, p_uva2],
                             'uvb': [3, p_uvb1, p_uvb2],
                             'uve': [4, p_uve1, p_uve2]}
        self.sensitivity = read_sensitivity(home, self.var_settings['device']['id'], "sensitivity")
        self.sensitivity_eritem = read_sensitivity(home, self.var_settings['device']['id'], "senseritem")
        self.confS = self.var_settings['calibration']['nm(pix)']['S']

    def calc_ozon(self):
        self.spectrum = spectr2zero(p_zero, p_lamst, self.data['spectr'], "calc_ozon")
        """Расчет озона"""
        self.o3 = {}
        correct = {}
        addational_data = {}
        for pair, values in lambda_consts.items():
            print("sum:", pair, sum(self.spectrum))
            print({pair: [lambda_consts[pair], lambda_consts_pix[pair]]})

            self.o3[pair], correct[pair], addational_data[pair] = pre_calc_o3(lambda_consts[pair],
                                                                              lambda_consts_pix[pair], self.spectrum,
                                                                              self.prom,
                                                                              self.data['mu'],
                                                                              self.var_settings, home, pair)
            print(self.o3[pair], correct[pair], addational_data[pair])
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
        self.spectrum = spectr2zero(p_zero, p_lamst, self.data['spectr'], 'calc_uv')
        ultraviolet = 0
        try:
            if uv_mode in ['uva', 'uvb']:
                if self.use_sensitivity:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]) * np.array(self.sensitivity[p1:p2]))
                else:
                    ultraviolet = sum(np.array(self.spectrum[p1:p2]))
                ultraviolet *= float(eval(self.confS[1])) * self.var_settings['device']['graduation_expo'] / \
                               self.data['expo']
            elif uv_mode == 'uve':
                if self.use_sensitivity:
                    ultraviolet = sum([float(self.spectrum[i]) *
                                       self.sensitivity_eritem[i] *
                                       self.sensitivity[i] for i in range(p1, p2, 1)]
                                      )
                else:
                    ultraviolet = sum([float(self.spectrum[i]) * self.sensitivity_eritem[i] for i in range(p1, p2, 1)])

                    ultraviolet *= float(eval(self.confS[1])) * self.var_settings['device']['graduation_expo'] / \
                                   self.data['expo']
                    ultraviolet *= float(self.var_settings['calibration']['{}_koef'.format(uv_mode)])
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

    def fig_destroy(self):
        self.fig.clf()
        plt.close()
        gc.collect()

    def set_x_limit(self, x, y, x_min, x_max, y_min, y_max, mode):
        if self.o3_mode != 'ozone':
            if max(x) > x_max: x_max = max(x)
            if min(x) < x_min: x_min = min(x)
            # if max(y) > y_max: y_max = max(y) * 1.05
            y_max = max(y)
            # if min(y) < y_min: y_min = min(y) * 0.95
            y_min = min(y)
        else:
            if max(x) > x_max: x_max = max(x)
            if min(x) < x_min: x_min = min(x)
            y_max = self.ozone_y_max
            y_min = self.ozone_y_min
        if mode == 'hour':
            self.ax.set(xlim=[x_min - datetime.timedelta(minutes=15), x_max + datetime.timedelta(minutes=15)],
                        ylim=[y_min, y_max])
            self.ax.xaxis.set_major_locator(mdates.HourLocator())
            self.ax.xaxis.set_minor_locator(mdates.MinuteLocator(np.arange(0, 60, 10)))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif mode == 'degree':
            self.ax.set(xlim=[x_min - 0.5, x_max + 0.5], ylim=[y_min, y_max])
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    def plot(self, path):
        global timer
        global canvs
        self.zen_path = path
        try:
            self.fig_destroy()
        except:
            pass
        self.fig, self.ax = plt.subplots(1)
        # print(self.fig.get_size_inches())
        self.fig.set_size_inches(self.plotx / 80, self.ploty / 80)
        self.fig.set_dpi(80)
        plt.subplots_adjust(left=0.07, right=0.97, bottom=0.07, top=0.95)
        if self.o3_mode == 'first':
            pass
        # ====================== Spectr ======================
        elif self.o3_mode == 'spectr':
            print('new spectr')
            self.ax.set_xlabel('nm')
            self.ax.set_ylabel('mV')
            conf = self.confZ
            if self.data['channel'].count('S') > 0:
                conf = self.confS
            self.ax.set_ylabel('mWt/m^2*nm')
            if self.use_sensitivity:  # Use sensitivity
                new_spectr = []
                for i in range(len(self.spectrum)):
                    new_spectr.append(
                        self.spectrum[i] *
                        self.sensitivity[i] *
                        var_settings['device']['graduation_expo'] /
                        self.data['expo'])
                self.spectrum = new_spectr
            self.ax.plot([pix2nm(conf, i, 3, 0) for i in range(len(self.spectrum))], self.spectrum, self.point,
                         color='k')
            if var_top.get():
                self.max_y = max(self.spectrum) + 100
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
            canvs_destroy(canvs)
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
            canvs_destroy(canvs)

        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        canvs.append(canvas)
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
    if os.name != 'posix':
        path = disks[disk_list.current()] + ':\\'
    else:
        path = p_sep
    print(path)
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
    dir_list.opened = False
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
    plotx, ploty = change_geometry(root)
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
    AxB = '200x320+'
    da, db = 25, 65
    dir_list.dirs_window.geometry('{0}{1}+{2}'.format(AxB, int(geom[1]) + da, int(geom[2]) + db))
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


def normalize(var):
    var = str(var)
    if len(var) == 1:
        return var.zfill(2)
    else:
        return var


def change_geometry(root):
    geom = root.geometry().split('+')[0].split('x')
    if geom[0] == '1' or geom[1] == '1':
        (plotx, ploty) = root.maxsize()
        plotx -= 225
        ploty -= 110
    else:
        plotx = int(geom[0]) - 225
        ploty = int(geom[1]) - 70
    return plotx, ploty


def make_o3file():
    global path
    global curr_o3
    global canvas
    global canvs
    global gr_ok
    global curr_time
    global ida
    global o3_plotted
    global root
    global o3_mod
    global file_name
    global tmp_path

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
        dir_list.dirs_window.destroy()
        refresh_txtlist(path)
        dir_list.opened = False
    except:
        pass
    but_make_mean_file.configure(state=DISABLED)
    for i in buttons:
        i.configure(state=DISABLED)
    if ida != '':
        canvas.after_cancel(ida)
        ida = ''
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
    plotx, ploty = change_geometry(root)
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
{0}{1}Ufos_{2}\{1}Mesurements?)""".format(home, p_sep, start.var_settings['device']['id'])

    else:  # Пересчёт
        mean_file = 0
        global ts
        global shs
        global calc_results
        ts, shs, calc_results = [], [], []
        saving = FinalFile(start.var_settings, home, annual_file=False, but_make_mean_file=but_make_mean_file)
        for i in sorted(txt):
            start.uvs_or_o3['ZD'] = {}
            start.uvs_or_o3['SD'] = {}

            chan = ''
            file_name = i.split('_')[1]
            if i.count("Z-D") > 0 or i.count("ZD") > 0:
                color = 'black'
            else:
                color = 'blue'
            file = os.path.join(path, i)
            if o3_mode == 'ozone':
                chan = 'ZD'
                if i.count("Z-D") > 0 or i.count("ZD") > 0:
                    start.data = start.get_spectr(file)
                    if 'm11_002_ZD_202008200542.txt' in i:
                        print("File:", i)
                    else:
                        continue
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


if __name__ == '__main__':
    human_text = ""
    try:
        args = sys.argv[1:]
        if args:
            show_ozone_pairs = [i for i in args if i in ["1", "2"]]
        else:
            show_ozone_pairs = ["2"]
        root = Tk()
        host, port, data4send = "10.65.25.2", 20000, ''
        ida = ''
        img = ''
        last_dir = []
        disks = []
        file_name = ''
        timer = ''
        canvs = []
        ts, shs, calc_results = [], [], []
        path = os.getcwd()
        home = os.getcwd()
        tmp_path = home
        human_text = "Common settings file is invalid"
        common_pars = Settings.get_common(home)
        human_text = "Ufos settings file is invalid"
        var_settings = Settings.get_device(home, common_pars['device']['id'])
        if os.name != 'posix':
            drive = os.getcwd()[:3]
        else:
            drive = p_sep
        path2 = ''
        plotx, ploty = change_geometry(root)
        o3min = 200
        ozon_scale_max = 600
        color = 'black'
        ima = []
        label = ''
        o3srednee = ''
        bit = 1
        ok = 1
        scale_printed = 0
        canvs = []
        last_path = last_used_path(home, path, 'r')
        try:
            if path != last_path and os.path.exists(last_path):
                path = last_path
            else:
                pass
        except:
            path = home
        curr_o3 = [0, 0, 0, 0, 0]
        try:
            # Check if file exists
            human_text = 'Чувствительность прибора УФОС' \
                         ' sensitivity{} - не найдена в каталоге программы!'.format(var_settings['device']['id'])
            read_sensitivity(home, var_settings['device']['id'], "sensitivity")  # Световая чувствительность прибора
            human_text = 'Чувствительность прибора УФОС' \
                         ' senseritem{} - не найдена в каталоге программы!'.format(var_settings['device']['id'])
            read_sensitivity(home, var_settings['device']['id'], "senseritem")  # Эритемная Чувствительность прибора
        except Exception as err:
            raise err
        curr_time = []
        gr_ok = 2
        o3_mode = ''
        o3_plotted = 1
        """
        gr_ok = 0 - озон расчитывается, график не строится
        gr_ok = 1 - озон не расчитывается, график строится
        gr_ok = 2 - озон расчитывается, график строится
        """

        root.title('УФОС Просмотр')
        root.protocol('WM_DELETE_WINDOW', window_closed)
        root.wm_state('zoomed')
        # root.geometry('908x530+200+100') #'908x530+200+100'
        root.resizable(True, True)
        appHighlightFont = font.Font(family='Helvetica', size=14)  # , weight='bold')
        top_panel = ttk.Frame(root, padding=(1, 1), relief='solid')  # ,width=800
        menu_panel = ttk.Frame(top_panel, padding=(1, 1), relief='solid')
        admin_panel = ttk.Frame(top_panel, padding=(1, 1), relief='solid')
        left_panel = ttk.Frame(root, padding=(1, 1), relief='sunken')
        right_panel = ttk.Frame(root, padding=(1, 1), relief='sunken')
        downline = ttk.Frame(root, padding=(1, 1), relief='solid', height=20)

        canvas = Canvas(right_panel, bg="white", width=plotx, height=ploty)  # white

        # Admin Menu
        chk_var_with_sens = IntVar()
        chk_var_with_sens.set(1)
        chk_with_sens = ttk.Checkbutton(admin_panel, text='Использовать чувствительность', variable=chk_var_with_sens)
        var_recalculate_source_files = IntVar()
        var_recalculate_source_files.set(0)
        chk_recalculate_source_files = ttk.Checkbutton(admin_panel, text='Пересчёт графика',
                                                       variable=var_recalculate_source_files)
        var_show_all = IntVar()
        var_show_all.set(0)
        chk_show_all = ttk.Checkbutton(admin_panel, text='Отобразить всё', variable=var_show_all)
        chk_var_show_correct1 = IntVar()
        chk_var_show_correct1.set(0)
        chk_show_correct1 = ttk.Checkbutton(admin_panel, text='Откл Корр 1', variable=chk_var_show_correct1)
        but_save_to_final_file = ttk.Button(admin_panel, text='Сохранить в файл')
        but_make_mean_file = ttk.Button(admin_panel, text='Сохранить в файл среднего')
        var_top = IntVar()
        var_top.set(1)
        rad_4096 = ttk.Radiobutton(admin_panel, text='Единая шкала', variable=var_top, value=0)
        rad_ytop = ttk.Radiobutton(admin_panel, text='Оптимальная шкала', variable=var_top, value=1)

        but_plot_more = ttk.Button(admin_panel, text='Подробный просмотр', command=plot_more)
        uv = IntVar()
        uv.set(4)
        but_remake = ttk.Button(admin_panel, text='Новый формат Z-D', command=b_remake)
        # but_send = ttk.Button(admin_panel, text=host, command=send_all_files_plotter)

        # Annual ozone calculations
        ent_year = ttk.Entry(admin_panel)
        ent_year.insert(0, "2018")
        but_annual_ozone = ttk.Button(admin_panel, text='Сохранить озон за год')

        admin_menu_obj = [chk_with_sens, chk_show_all, chk_show_correct1, chk_recalculate_source_files,
                          but_save_to_final_file,
                          but_make_mean_file,
                          rad_4096, rad_ytop, but_plot_more, but_remake,
                          # but_send
                          ent_year, but_annual_ozone
                          ]

        # Main Menu
        but_refresh = ttk.Button(menu_panel, text='Обновить', command=refresh)
        but_dir = ttk.Button(menu_panel, text='Выбор каталога', command=dir_list_show)
        rad_spectr = ttk.Radiobutton(menu_panel, text='Спектр', variable=uv, value=4, command=plot_spectr)
        rad_o3file = ttk.Radiobutton(menu_panel, text='Озон', variable=uv, value=0, command=make_o3file)
        rad_uva = ttk.Radiobutton(menu_panel, text='УФ-А', variable=uv, value=1, command=make_o3file)
        rad_uvb = ttk.Radiobutton(menu_panel, text='УФ-Б', variable=uv, value=2, command=make_o3file)
        rad_uve = ttk.Radiobutton(menu_panel, text='УФ-Э', variable=uv, value=3, command=make_o3file)
        ent_code = ttk.Entry(menu_panel, width=2)
        main_menu_obj = [but_refresh, but_dir, rad_spectr, rad_o3file, rad_uva, rad_uvb, rad_uve, ent_code]

        file_list = Listbox(left_panel, selectmode=SINGLE, height=16, width=28)
        scr_lefty = ttk.Scrollbar(left_panel, command=file_list.yview)
        file_list.configure(yscrollcommand=scr_lefty.set)
        lab_currnt_data = ttk.Label(left_panel, text='Данные: ')
        currnt_data = ttk.Label(left_panel, text='')
        lab_ozon = ttk.Label(left_panel, text='', foreground='blue', font=appHighlightFont)
        lab_uva = ttk.Label(left_panel, text=': ', foreground='blue')
        lab_uvb = ttk.Label(left_panel, text=': ', foreground='blue')
        lab_uve = ttk.Label(left_panel, text=': ', foreground='blue')
        lab_sun = ttk.Label(left_panel, text='')
        lab_path = ttk.Label(downline, text=path)
        lab_err = ttk.Label(downline, text='', width=20)

        buttons = main_menu_obj + admin_menu_obj

        """============== GUI Structure =============="""
        top_panel.grid(row=0, column=0, sticky='nwe', columnspan=4)
        menu_panel.grid(row=0, column=0, sticky='nwe')
        but_refresh.grid(row=0, column=0, sticky='w')
        but_dir.grid(row=0, column=1, sticky='w')

        obj_grid()

        # but_send.grid(row=0, column=10, sticky='w')
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
        confZ = var_settings['calibration']['nm(pix)']['Z']
        confS = var_settings['calibration']['nm(pix)']['S']
        lambda_consts = {pair: var_settings['calibration']['points']['o3_pair_{}'.format(pair)] +
                               var_settings['calibration']['points']['cloud_pair_{}'.format(pair)] for pair in
                         ["1", "2"]}
        points = var_settings['calibration']['points']
        p_uva1, p_uva2 = nm2pix(315, confS, 0), nm2pix(400, confS, 0)
        p_uvb1, p_uvb2 = nm2pix(280, confS, 0), nm2pix(315, confS, 0)
        p_uve1, p_uve2 = 0, 3691  # nm2pix(290),nm2pix(420)

        p_zero = {pair: nm2pix(nm, confZ, 0) for pair, nm in zip(["1", "2"], [290, 295])}
        p_lamst = nm2pix(290, confZ, 0)
        # Массив констант лямбда в пикселях
        lambda_consts_pix = {pair: [nm2pix(i, confZ, 0) for i in const] for pair, const in lambda_consts.items()}
        psZ = {}
        psS = {}
        for key in points.keys():
            psZ[key] = []
            psS[key] = []
            for point in points[key]:
                psZ[key].append(nm2pix(point, confZ, 0))
                psS[key].append(nm2pix(point, confS, 0))

        start = first_clear_plot(plotx, ploty, right_panel)

        # Скрыть следующие кнопки
        common = [rad_4096, rad_ytop, but_plot_more, but_remake]
        sertification = [rad_4096, rad_ytop, but_plot_more, rad_uva, rad_uvb, rad_uve, but_remake,
                         chk_recalculate_source_files,
                         but_save_to_final_file, but_make_mean_file]

        # Uncomment after debug will be finished
        change_privileges(common, 0)

        """=============================================================="""
        downline.grid(row=6, column=0, sticky='nswe', columnspan=4)
        lab_path.grid(row=0, column=0, sticky='w')
        lab_err.grid(row=0, column=1, sticky='e')

        """============== GUI Actions =============="""
        file_list.bind('<Double-Button-1>', plot_spectr)
        ##file_list.bind('<space>', plot_spectr)
        file_list.bind('<Return>', plot_spectr)
        file_list.bind('<Button-1>', dirs_window_destroy)
        canvas.bind('<Button-1>', dirs_window_destroy)
        left_panel.bind('<Button-1>', dirs_window_destroy)
        right_panel.bind('<Button-1>', dirs_window_destroy)
        ent_code.bind('<Return>', check_code)

        root.mainloop()
    except Exception as error:
        root.destroy()
        err = ""
        try:
            raise error
        except FileNotFoundError as e:
            err = e
        except json.decoder.JSONDecodeError as e:
            err = e
        show_error_in_separate_window(err, human_text)
        # raise error
