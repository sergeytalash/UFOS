# Version: 1.0
# Modified: 04.02.2018
# Author: Sergey Talash
import matplotlib

from sys import platform as sys_pf
from sys import path as sys_path

if sys_pf == 'darwin':
  import matplotlib

  matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import gc
import datetime
import os
from os.path import split as p_split
import json
from tkinter import *
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt

settings_home = p_split(p_split(os.getcwd())[0])[0]
sys_path.insert(0, settings_home)
# import procedures
# from procedures import Settings
from lib.core import *

import collections


def nm2pix(nm, abc, add=0):
  nm = float(nm)
  pix = 0
  if 270 < nm < 350:
    ans_nm = pix2nm(abc, pix, 1, add)
    while ans_nm < nm and pix < 1500:
      pix += 1
      ans_nm = pix2nm(abc, pix, 1, add)
      # print(pix,ans_nm)
  elif 350 <= nm < 430 and 1500 < pix < 3692:
    pix = 1500
    ans_nm = pix2nm(abc, pix, 1, add)
    while ans_nm < nm:
      pix += 1
      ans_nm = pix2nm(abc, pix, 1, add)
      # print(pix, ans_nm)
  else:
    print(nm, 'nm2pix: error')
  return pix


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


class Calc:
  def __init__(self, PARS):
    self.dates = {}
    PARS = PARS
    self.dates_no_data = []
    self.files = {}
    self.pixels = {}
    self.type = 'Morning'
    self.start_mu = True
    self.home = 'calibration_files'
    self.dict_polynoms = {}
    self.dict_polynom_tmp = {}
    self.Ls = {'sko': [], 'mean': [], 'mu': []}
    self.data2file = []
    confZ = PARS['calibration']['nm(pix)']['Z']
    self.p_zero1 = nm2pix(285, confZ, 0)
    self.p_zero2 = nm2pix(290, confZ, 0)
    self.sensitivityZ = read_sensitivity("Z")

  def get_dates(self):
    with open(os.path.join(self.home, 'Calibration_dates.txt')) as f:
      data = f.readlines()
    for i in data:
      d = i.split()
      self.dates[d[0]] = d[1]  # 'YYYY.MM.DD': 'Ozone'
    return self.dates

  def get_filenames(self):
    for date in self.dates.keys():
      d = date.split('.')  # YYYY.MM.DD
      path = os.path.join(settings_home,
                          'Ufos_{}'.format(PARS['device']['id']),
                          'Mesurements',
                          str(d[0]),
                          '{}-{}'.format(d[0], d[1]),
                          '{}-{}-{}'.format(d[0], d[1], d[2]))
      if os.path.exists(path):
        self.files[date] = [os.path.join(path, name) for name in os.listdir(path) if name.count('txt') > 0]

  def calculate(self, abc, x, num):
    deg = len(abc) - 1
    out = 0
    for i in abc:
      out += eval(str(i)) * float(x) ** deg
      deg -= 1
    return round(out, num)

  def pix2nm(self, pix, chan):
    return self.calculate(PARS['calibration']['nm(pix)'][chan], pix, 3)

  def nm2pix(self, nm, chan, pix=0):
    nm = float(nm)
    if not 270 < nm < 440:
      print(nm, 'nm2pix: error')
    if 350 <= nm < 440:
      pix = 1500
    ans_nm = 0
    while ans_nm < nm:
      pix += 1
      ans_nm = self.pix2nm(pix, chan)
    return pix

  def get_pixels(self, chan):
    for pair in PARS['calibration']['points'].keys():
      self.pixels[pair] = []

      if pair != 'Fraunhofer_pair':
        self.Ls[pair] = []
      for nm in PARS['calibration']['points'][pair]:
        self.pixels[pair].append(self.nm2pix(nm, chan))

  def open_file(self, path):
    with open(path) as f:
      data = json.load(f)
    return data

  def split_mas(self, x, y, num_mas):
    """Разделение массива на интервалы
        x = mu
        y - значения
        num_mas - массив чисел, ограничивающих интервалы
        num_mas = [3,5]"""
    new_x = [[]]
    new_y = [[]]
    for i in num_mas:
      new_x.append([])
      new_y.append([])
    for xi, yi in zip(x, y):
      if xi <= num_mas[0] * 1.1:
        new_x[0].append(xi)
        new_y[0].append(yi)
      if num_mas[0] * 0.9 <= xi <= num_mas[1] * 1.1:
        new_x[1].append(xi)
        new_y[1].append(yi)
      if num_mas[1] * 0.9 <= xi:
        new_x[2].append(xi)
        new_y[2].append(yi)
    return new_x, new_y

  def get_Ls(self, date, chan):
    self.Ls = {'sko': [], 'mean': [], 'mu': []}
    for pair in self.pixels.keys():
      if pair != 'Fraunhofer_pair':
        self.Ls.setdefault(pair, [])
    if date in self.files:
      for file in sorted(self.files[date]):  # ['YYYY.MM.DD']
        if file.count(chan + 'D') > 0:
          try:
            file_data = self.open_file(file)
            mv_list = [file_data['spectr'][i] for i in range(self.p_zero1, self.p_zero2 + 1)]
            mv = sum(mv_list) / len(mv_list)

            spectr = [i - mv for i in file_data['spectr']]
            len_sp, len_sens = len(spectr), len(self.sensitivityZ)
            if len_sp != len_sens:
              print("Spectr and sensitivity length not equal for {}"
                    "(Spectr: {}, SensitivityZ: {})".format(date, len_sp, len_sens))
            len_min = min(len_sp, len_sens)

            spectr = [i * k for i, k in zip(spectr[:len_min], self.sensitivityZ[:len_min])]

            sko = file_data['calculated']['sko']
            mean = file_data['calculated']['mean']
            mu = file_data['calculated']['mu']
            for pair_name, pixels in self.pixels.items():
              if pair_name != 'Fraunhofer_pair':
                p = {str(i): int(pixels[i]) for i in [0, 1]}
                I = {str(i): spectr[
                             p[str(i)] - int(PARS['calibration']['pix_interval']):
                             p[str(i)] + int(PARS['calibration']['pix_interval'])] for i in [0, 1]}
                self.Ls[pair_name].append(round(sum(I['0']) / sum(I['1']), 6))
            self.Ls['sko'].append(sko)
            self.Ls['mean'].append(mean)
            self.Ls['mu'].append(mu)
          except Exception as err:
            print(err, file)
            raise err

  def polynom_add(self, date, dates_count, *event):
    if date[dates_count] not in calc.dates_no_data:
      self.dict_polynoms = self.update(self.dict_polynoms, self.dict_polynom_tmp)

  def update(self, d, u):
    for k, v in u.items():
      if isinstance(v, collections.Mapping):
        d[k] = self.update(d.get(k, {}), v)
      else:
        d[k] = v
    return d

  def table_create(self, name, date, mu, condition):
    text = ''
    for pair in ['o3_pair_', 'cloud_pair_']:
      L = 0
      if self.dict_polynoms[date][pair + name][condition][1]:
        L = self.calculate(self.dict_polynoms[date][pair + name][condition][0], mu, 6)
      text += ';{}'.format(L)
    return text


class GUI():
  def __init__(self, root, dates):
    self.plt = {}
    self.fig = {}
    self.file_meta = 'Sens_dev{}_{}_'.format(PARS["device"]["id"],
                                        datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d-%H%M'))
    self.file_format = '.csv'
    self.text_polynoms = '{}{}_polynoms_{}{}'
    self.text_tables = '{}{}_table_{}{}'
    self.mus = np.arange(PARS["calibration"]["polynom"]["mu_start"],
                         PARS["calibration"]["polynom"]["mu_end"],
                         PARS["calibration"]["polynom"]["mu_step"])
    self.channel = 'Z'  # Take ZD files (or set 'S' to taket ZS files)
    self.graph_names = ['1', '2']  # For pairs ['o3_pair_','cloud_pair_']
    self.polynom_vars = {i: [] for i in self.graph_names}
    self.polynom_chkbtns = {i: [] for i in self.graph_names}
    self.canvas = {}
    self.dates_count = 0
    self.dates_len = len(dates)
    self.dates = dates
    self.date = list(dates.keys())
    self.date.sort()
    self.root = root
    self.chk_btns = []
    self.root.title('УФОС Калибровка {}'.format(calc.type))
    self.root.geometry('+100+0')
    self.root.resizable(False, False)
    self.gui_elements = []
    self.left_frame = ttk.Frame(self.root)
    self.right_frame = ttk.Frame(self.root)
    self.gui_elements.append(ttk.Label(self.left_frame, text='Номер прибора:'))
    self.gui_elements.append(ttk.Label(self.left_frame, text=PARS['device']['id']))
    self.gui_elements.append(ttk.Label(self.left_frame, text='Номер станции:'))
    self.gui_elements.append(ttk.Label(self.left_frame, text=PARS['station']['id']))
    self.gui_elements.append(ttk.Label(self.left_frame))
    self.gui_elements.append(ttk.Label(self.left_frame))
    self.gui_elements.append(ttk.Label(self.left_frame, text='Дата'))
    self.gui_elements.append(ttk.Label(self.left_frame, text='Озон'))
    for i in self.date:
      self.gui_elements.append(ttk.Label(self.left_frame, text=i))
      self.gui_elements.append(ttk.Label(self.left_frame, text=dates[i]))

    self.btn_save_table = ttk.Button(self.right_frame, text='Сохранить табличные данные', command=self.save_to_table)
    self.btn_save_koeff = ttk.Button(self.right_frame, text='Сохранить коэффициенты', command=self.save_to_file)
    self.btn_save_poly = ttk.Button(self.right_frame, text='Запомнить эти полиномы',
                                    command=lambda: calc.polynom_add(self.date, self.dates_count))
    self.btn_next = ttk.Button(self.right_frame, text='Далее >', command=self.next_graphs)
    self.btn_refresh = ttk.Button(self.right_frame, text='Обновить', command=self.refresh_graphs)
    self.btn_prev = ttk.Button(self.right_frame, text='< Назад', command=self.prev_graphs)

  def draw_elements(self):
    self.left_frame.grid(row=0, column=0, sticky='wesn')
    self.right_frame.grid(row=0, column=1, sticky='wesn')
    r = 0
    c = 0
    for i in self.gui_elements:
      i.grid(row=r, column=c, sticky='w')
      if c == 0:
        c = 1
      else:
        c = 0
        r += 1

  def graph(self, plt_name, size, pos, calc):
    try:
      self.plt[plt_name].close()
      del self.plt[plt_name]
    except:
      pass
    for i in range(6):
      intvar = IntVar()
      self.polynom_vars[plt_name].append(intvar)
      chkbtn = ttk.Checkbutton(self.right_frame, text=str(i), variable=intvar)
      self.polynom_chkbtns[plt_name].append(chkbtn)
      chkbtn.grid(row=pos[0] + 1, column=i, sticky='w')
    self.plt[plt_name] = plt
    self.fig[plt_name] = Figure(figsize=size, tight_layout=True)
    self.canvas[plt_name] = FigureCanvasTkAgg(self.fig[plt_name], master=self.right_frame)
    self.canvas[plt_name].get_tk_widget().grid(row=pos[0], column=pos[1], sticky='wesn', columnspan=6)
    self.canvas[plt_name].draw()

  def buttons(self, r):
    self.btn_save_table.grid(row=r, column=5, sticky='w')
    self.btn_save_koeff.grid(row=r, column=4, sticky='w')
    self.btn_save_poly.grid(row=r, column=3, sticky='w')
    self.btn_next.grid(row=r, column=2, sticky='w')
    self.btn_refresh.grid(row=r, column=1, sticky='w')
    self.btn_prev.grid(row=r, column=0, sticky='w')
    self.btn_prev.configure(state=DISABLED)

  def subplot(self, plt_name, x, y, title, pos, legend, plot_pos):
    ax = self.fig[plt_name].add_subplot(plot_pos)
    ax.set_ylim(0, max(y) * 1.1)
    ax.set_xlim(min(x) * 0.9, max(x) * 1.1)
    ax.set_title(title)
    ax.grid(True)  # координатную сетку рисовать
    xx, yy = [x, x, x], [y, y, y]
    lines = []
    calc.dict_polynom_tmp[self.date[self.dates_count]][title] = {}
    calc.dict_polynom_tmp[self.date[self.dates_count]][title + '_mesure'] = {}
    for xi, yi, color, lab in zip(xx, yy, ['-r', '-g', '-b'], ['mu<3', '3<mu<5', '5<mu']):
      try:
        calc.dict_polynom_tmp[self.date[self.dates_count]][title + '_mesure']['mu'] = xi
        calc.dict_polynom_tmp[self.date[self.dates_count]][title + '_mesure']['L'] = yi
        sko = round(float(np.std(yi)), 4)
        lines.append(ax.plot(xi, yi, color, label=title + ' ' + lab + ' ' + str(sko))[0])
        z = np.polyfit(xi, yi, PARS["calibration"]["polynom"]["degree"])
        calc.dict_polynom_tmp[self.date[self.dates_count]][title][lab] = [z.tolist(), sko]
        y = [calc.calculate(z.tolist(), i, 6) for i in xi]
      except Exception as err:
        calc.dict_polynom_tmp[self.date[self.dates_count]][title][lab] = [[], None]

    ax.legend(loc='best', fancybox=True).get_frame().set_alpha(0.2)

  def next_graphs(self, *event):
    self.dates_count += 1
    self.refresh_graphs()
    if 0 < self.dates_count <= self.dates_len:
      self.btn_prev.configure(state=NORMAL)
    if self.dates_count >= self.dates_len - 1:
      self.btn_next.configure(state=DISABLED)

  def prev_graphs(self, *event):
    self.dates_count -= 1
    self.refresh_graphs()
    if 0 <= self.dates_count < self.dates_len:
      self.btn_next.configure(state=NORMAL)
    if self.dates_count <= 0:
      self.btn_prev.configure(state=DISABLED)

  def refresh_graphs(self, *event):
    curr_date = self.date[self.dates_count]
    for i in self.gui_elements:
      if i.cget("text") == curr_date:
        i.configure(font='Arial 10 bold')
      else:
        i.configure(font='Arial 10')
    calc.get_Ls(curr_date, self.channel)
    calc.dict_polynom_tmp = {curr_date: {}}
    self.chk_btns = []
    out = False
    for name, row in zip(self.graph_names,
                         [i * 2 for i in range(len(self.graph_names))]):  # graph_names = ['1','2']
      self.graph(name, (12, 3), (row, 0), calc)
      for pair, column, left, plot_pos in zip(['o3_pair_', 'cloud_pair_'], [0, 1], [0.050, 0.545], [121, 122]):
        if calc.Ls[pair + name]:
          self.subplot(name, calc.Ls['mu'], calc.Ls[pair + name], pair + name, (0, column),
                       [left, 0.1, 0.12, 0.17], plot_pos)
          self.canvas[name].draw()
        else:
          if not out:
            out = True
            calc.dates_no_data.append(curr_date)
            print("No data: {}".format(curr_date))
            break

  def save_to_file(self, *event):
    if not calc.dict_polynoms:
      print("No data to save")
    else:
      for name in self.graph_names:
        with open(os.path.join(
          calc.home, self.text_polynoms.format(self.file_meta, calc.type, name,
                                               self.file_format)), 'w') as f:
          # Headers Date;Ozone;
          f.write('Date;Ozone')
          for pair in ['o3_pair_', 'cloud_pair_']:
            for mu in ['mu<3', '3<mu<5', '5<mu']:
              for coeff in 'abcdef'[:PARS["calibration"]["polynom"]["degree"] + 1]:
                f.write(';{}{}_{}'.format(pair, mu, coeff))
              f.write(';SKO;Status')
          f.write('\n')

          for date in calc.dict_polynoms.keys():
            f.write('{};{}'.format(date, self.dates[date]))
            for pair in ['o3_pair_', 'cloud_pair_']:
              for mu in ['mu<3', '3<mu<5', '5<mu']:
                if calc.dict_polynoms[date][pair + name][mu][1]:
                  f.write(';{};{};{}'.format(
                    str(calc.dict_polynoms[date][pair + name][mu][0]).replace('[', '').replace(']',
                                                                                               '').replace(
                      ', ', ';'), calc.dict_polynoms[date][pair + name][mu][1], 1))
                else:
                  f.write(';{};{};{}'.format(
                    str([0] * (PARS["calibration"]["polynom"]["degree"] + 1)).replace('[', '').replace(
                      ']', '').replace(', ', ';'), 'NaN', 0))
            f.write('\n')
        print("Saved: " + self.text_polynoms.format(self.file_meta, calc.type, name, self.file_format))

  def save_to_table(self, *event):
    if not calc.dict_polynoms:
      print("No data to save")
    else:
      for name in self.graph_names:
        with open(os.path.join(
          calc.home, self.text_tables.format(self.file_meta, calc.type,
                                             name, self.file_format)), 'w') as f:
          # Headers Date;Ozone;
          f.write('Date;Ozone;Mu')
          for pair in ['o3_pair_', 'cloud_pair_']:
            f.write(';{}'.format(pair + name))
          f.write(';;Mu')
          for pair in ['o3_pair_', 'cloud_pair_']:
            f.write(';{}'.format(pair + name + '_mesure'))
          f.write('\n')
          for date in sorted(calc.dict_polynoms.keys()):
            i = 0
            self.mus = calc.dict_polynoms[date][pair + name + '_mesure']['mu']
            while i < len(self.mus):
              mu = self.mus[i]
              text = '{};{};{}'.format(date, self.dates[date], mu)
              if mu < PARS["calibration"]["polynom"]["mu_intervals"][0]:  # mu<3
                text += calc.table_create(name, date, mu, 'mu<3')
              elif PARS["calibration"]["polynom"]["mu_intervals"][0] <= mu < \
                PARS["calibration"]["polynom"]["mu_intervals"][1]:  # 3<=mu<5
                text += calc.table_create(name, date, mu, '3<mu<5')
              elif mu >= PARS["calibration"]["polynom"]["mu_intervals"][1]:  # mu>=5
                text += calc.table_create(name, date, mu, '5<mu')
              try:
                if i < len(calc.dict_polynoms[date][pair + name + '_mesure']['mu']):
                  text += ';;{}'.format(calc.dict_polynoms[date][pair + name + '_mesure']['mu'][i])
                  for pair in ['o3_pair_', 'cloud_pair_']:
                    text += ';{}'.format(calc.dict_polynoms[date][pair + name + '_mesure']['L'][i])
              except Exception as err:
                pass
              f.write('{}\n'.format(text))
              i += 1
        print('Saved: ' + self.text_tables.format(self.file_meta, calc.type, name, self.file_format))


if __name__ == "__main__":
  PARS = Settings.get_device(settings_home, Settings.get_common(settings_home).get('device').get('id'))
  calc = Calc(PARS)
  dates = calc.get_dates()
  calc.get_filenames()
  calc.get_pixels('Z')

  root = Tk()
  main = GUI(root, dates)
  main.draw_elements()
  main.refresh_graphs()
  main.buttons(4)

  root.mainloop()
