from datetime import datetime, timedelta
from math import *
from tkinter import NORMAL
import threading
import queue as queue_th

from lib.core import *
from lib.gui import *
from lib.measure import *


class FinalFile:
    def __init__(self, annual_file, but_make_mean_file):
        """

        Args:
            annual_file (bool):
            but_make_mean_file ():
        """
        self.path_file = ''
        self.annual_file = annual_file
        self.but_make_mean_file = but_make_mean_file

    @staticmethod
    def prepare(date_utc, calc_result):
        """

        Args:
            date_utc (datetime):
            calc_result (dict):

        Returns:
            tuple: date_utc_str, sh, calc_result
        """
        if isinstance(date_utc, str):
            date_utc_str = date_utc
            date_utc_date = datetime.strptime(date_utc, '%Y%m%d %H:%M:%S')
        else:
            date_utc_str = datetime.strftime(date_utc, '%Y%m%d %H:%M:%S')
            date_utc_date = date_utc
        mu, amas, sh = sunheight(PARS["station"]["latitude"],
                                 PARS["station"]["longitude"],
                                 date_utc_date,
                                 PARS["station"]["timezone"])
        return date_utc_str, sh, calc_result

    def save(self, chan, ts, shs, calc_results):
        """

        Args:
            chan (str):
            ts ():
            shs ():
            calc_results ():

        Returns:

        """
        create_new_file = True
        analyse_file_name = ''
        for date_utc, sh, calc_result in zip(ts, shs, calc_results):
            self.path_file = write_final_file(chan,
                                              date_utc,
                                              round(sh, 1),
                                              calc_result,
                                              'New_',
                                              create_new_file)
            if chan == 'ZD':
                analyse_file_name = write_analyse_file(chan,
                                                       date_utc,
                                                       round(sh, 1),
                                                       calc_result,
                                                       'Analyse_',
                                                       create_new_file)
            create_new_file = False
        if not self.annual_file:
            print('1) Files saved:\n{}\n{}'.format(self.path_file, analyse_file_name))
            self.but_make_mean_file.configure(
                command=lambda: calculate_final_files(self.path_file, chan, True, "file"))
            self.but_make_mean_file.configure(state=NORMAL)
        return self.path_file


class AnnualOzone:
    # Procedure for annual ozone calculations (make_annual_ozone_file)

    def __init__(self, year, data, root, but_annual_ozone):
        self.year = year
        self.data = data
        self.annual_data = {}
        self.root = root
        self.but_annual_ozone = but_annual_ozone
        self.debug = False
        self.num_worker_threads = 100
        self.type_of_parallel = [None, 'asyncio', 'threading'][2]
        # asyncio =     0:00:05.442841
        # threading =   0:00:05.311453

    def run(self):
        self.make_annual_ozone_file(self.year)
        # self.write_annual_ozone()
        self.but_annual_ozone.configure(text="Сохранить озон за год")
        self.root.update()
        print("Done.")

    @staticmethod
    def open_annual_files_for_write(year):
        file_descriptors = {}
        dir_path = make_dirs(DEVICE_DIR_L + ["Ozone"])
        if os.path.exists(dir_path):
            for pair in ["1", "2"]:
                annual_file_name = "Ufos_{}_ozone_{}_pair_{}.txt".format(DEVICE_ID, year[:4], pair)
                path = os.path.join(dir_path, annual_file_name)
                if not os.path.exists(path):
                    with open(path, 'w') as f:
                        print("Date\t" +
                              "Mean_All\tSigma_All\tO3_Count\t" +
                              "Mean_Morning\tSigma_Morning\tO3_Count\t" +
                              "Mean_Evening\tSigma_Evening\tO3_Count", file=f)
                file_descriptors[pair] = open(path, 'a')
        return file_descriptors

    @staticmethod
    def write_annual_line(fw, day_string, line):
        """

        Args:
            fw (Optional[_Writer]):
            day_string (str):
            line (dict):

        """
        line_data = [day_string]
        for part_of_day in ['all', 'morning', 'evening']:
            for item in ['mean', 'sigma', 'o3_count']:
                if item in line[part_of_day].keys():
                    line_data.append(str(line[part_of_day][item]))
                else:
                    line_data.append('')
        print("\t".join(line_data), file=fw)

    @staticmethod
    def print_line(line: dict, debug: bool):
        if debug:
            print('line', line)
        else:
            print(os.path.basename(list(line.values())[0][0]))

    def process_one_file_none(self, file_path, main, saving, day, num, debug=False):
        data = self.data.get_spectr(file_path, False)
        calc_result, chan = main.add_calculated_line_to_final_file(data["spectr"],
                                                                   data["calculated"]["mu"],
                                                                   data["mesurement"]["exposition"],
                                                                   self.data.sensitivity,
                                                                   self.data.sensitivity_eritem, False)
        # Fix datetime_local of the file after Reformat procedure (datetime_local do not present in file)
        try:
            data["mesurement"]["datetime_local"]
        except KeyError:
            data["mesurement"]["datetime_local"] = datetime.strptime(
                data["mesurement"]['datetime'], "%Y%m%d %H:%M:%S") + timedelta(
                hours=int(data["mesurement"]['timezone']))

        # Prepare daily ozone
        date_utc_str, sh, calc_result = saving.prepare(data["mesurement"]['datetime'], calc_result)
        # Prepare day for annual ozon
        day_string = {day: ";".join([str(i) for i in [data["mesurement"]['datetime'],
                                                      data["mesurement"]["datetime_local"],
                                                      data["calculated"]["sunheight"],
                                                      calc_result[chan]["o3_1"],
                                                      calc_result[chan]["correct_1"],
                                                      calc_result[chan]["o3_2"],
                                                      calc_result[chan]["correct_2"]
                                                      ]
                                     ]
                                    )
                      }
        out = {str(num): [file_path, date_utc_str, sh, calc_result, day_string]}
        self.print_line(out, debug)
        return out

    def process_one_file_threading(self, main, saving, queue_in, queue_out, debug=False):
        while True:
            if queue_in.empty():
                # sleep(1)
                pass
            else:
                item = queue_in.get()
                if item is None:
                    break
                file_path, num, day = item
                data = self.data.get_spectr(file_path, False)
                calc_result, chan = main.add_calculated_line_to_final_file(data["spectr"],
                                                                           data["calculated"]["mu"],
                                                                           data["mesurement"]["exposition"],
                                                                           self.data.sensitivity,
                                                                           self.data.sensitivity_eritem, False)
                # Fix datetime_local of the file after Reformat procedure (datetime_local do not present in file)
                try:
                    data["mesurement"]["datetime_local"]
                except KeyError:
                    data["mesurement"]["datetime_local"] = datetime.strptime(
                        data["mesurement"]['datetime'], "%Y%m%d %H:%M:%S") + timedelta(
                        hours=int(data["mesurement"]['timezone']))

                # Prepare daily ozone
                date_utc_str, sh, calc_result = saving.prepare(data["mesurement"]['datetime'], calc_result)
                # Prepare day for annual ozone
                day_string = {day: ";".join([str(i) for i in [data["mesurement"]['datetime'],
                                                              data["mesurement"]["datetime_local"],
                                                              data["calculated"]["sunheight"],
                                                              calc_result[chan]["o3_1"],
                                                              calc_result[chan]["correct_1"],
                                                              calc_result[chan]["o3_2"],
                                                              calc_result[chan]["correct_2"]
                                                              ]
                                             ]
                                            )
                              }
                out = {str(num): [file_path, date_utc_str, sh, calc_result, day_string]}
                self.print_line(out, debug)
                out = json.dumps(out)
                queue_out.put(out)
                queue_in.task_done()

    @staticmethod
    def get_zd_count(year):
        count = 0
        for dir_path, dirs, files in os.walk(os.path.join(*MEASUREMENTS_DIR_L, year), topdown=True):
            for file in files:
                if file.count("ZD") > 0:
                    count += 1
        return count

    def make_annual_ozone_file(self, year):
        """data - PlotClass.init()"""
        annual_file_descriptors = {}
        measure = MeasureClass()
        saving = FinalFile(annual_file=True, but_make_mean_file=None)
        measure.chan = "ZD"
        create_annual_files = True
        current = 0
        max_files = self.get_zd_count(year)
        queue_th_input = queue_th.Queue()
        queue_th_output = queue_th.Queue()
        threads = []

        for dir_path, dirs, files in os.walk(os.path.join(*MEASUREMENTS_DIR_L, year)):
            create_annual_files = True
            annual_file_descriptors = {}
            if self.type_of_parallel:
                print('Running in parallel: ' + self.type_of_parallel)
            # if self.type_of_parallel == 'asyncio':
            # Asyncio
            # queue = asyncio.Queue()
            if self.type_of_parallel == 'threading':
                # Threading
                threads = []
                for i in range(self.num_worker_threads):
                    t = threading.Thread(target=lambda: self.process_one_file_threading(
                        measure, saving, queue_th_input, queue_th_output, debug=self.debug))
                    t.start()
                    threads.append(t)
            print("...", dir_path)
            daily_o3_to_file = {}
            create_daily_files = True
            num = 0
            max_day_files = len([name for name in files if name.count("ZD") > 0])
            day = None
            tasks = []
            all_data = {}
            timer = [datetime.now()]
            for file in files:
                if file.count("ZD") > 0:
                    current += 1
                    # print('{} of {}'.format(current, max_files))
                    day = os.path.basename(dir_path)
                    if create_daily_files:
                        daily_o3_to_file[day] = []
                        create_daily_files = False
                    if create_annual_files:
                        annual_file_descriptors = self.open_annual_files_for_write(year)
                        create_annual_files = False
                    file_path = os.path.join(dir_path, file)

                    if self.type_of_parallel == 'threading':
                        queue_th_input.put((file_path, num, day))
                    else:
                        line = self.process_one_file_none(file_path, measure, saving, day, num, debug=self.debug)
                        all_data.update(line)
                        if self.debug:
                            print('dict', all_data[list(line.keys())[0]])
                    self.but_annual_ozone.configure(text=file[-16:-4])
                    self.root.update()
                    num += 1
            # print([v[3]['ZD'] for v in all_data.values()])
            if day:
                self.but_annual_ozone.configure(text=files[-1][-16:-4])
                self.root.update()

                if self.type_of_parallel == 'threading':

                    # Block until all Input tasks are done
                    queue_th_input.join()
                    # Stop workers
                    for i in range(self.num_worker_threads):
                        queue_th_input.put(None)
                    for t in threads:
                        t.join()
                    # Collect data
                    while not queue_th_output.empty():
                        line = queue_th_output.get()
                        queue_th_output.task_done()
                        line = json.loads(line)
                        all_data.update(line)
                        if self.debug:
                            print('dict', all_data[list(line.keys())[0]])
                    # Block until all Output tasks are done
                    queue_th_output.join()
                else:
                    pass
                [print(datetime.now() - i) for i in timer]
                # loop.close()
                ts = [all_data[str(j)][1] for j in range(max_day_files)]
                shs = [all_data[str(j)][2] for j in range(max_day_files)]
                calc_results = [all_data[str(j)][3][measure.chan] for j in range(max_day_files)]
                daily_o3_to_file[day] = [all_data[str(j)][4][day] for j in range(max_day_files)]
                for day_string, day_data in daily_o3_to_file.items():
                    # Save ozone to daily file
                    path_file = saving.save(measure.chan, ts, shs, calc_results)
                    if self.debug:
                        print('1) Daily File Saved: {}'.format(path_file))
                    # Save ozone to mean daily file
                    calculate_final_files(path_file, measure.chan, True, "file")
                    # Save ozone to annual file
                    print("3) Writing to annual files...{}".format(day_string), end=' ')
                    for pair, fw in annual_file_descriptors.items():
                        daily_data = calculate_final_files(day_data, measure.chan, False, "calculate")
                        self.write_annual_line(fw, day_string, daily_data[pair])
                        print(pair, end=' ')
                    print()

            for pair, fw in annual_file_descriptors.items():
                fw.close()
            if annual_file_descriptors:
                print('4) Annual files were saved.')


class Correction:
    def __init__(self, data):
        self.data = data
        # Массив старых строк с лишними \t с делением на \t
        self.lines_arr_raw_to_file = []

    @staticmethod
    def get_second_corrects(o3s, o3s_first_corrected):
        """Среднеквадратичное отклонение
        o3s - Весь озон
        o3s_first_corrected - Озон с первой корректировкой (100 - 600)"""
        sigma_count = PARS['calibration']['sigma_count']
        if o3s_first_corrected:
            sigma = round(float(np.std(o3s_first_corrected)), 2)
            mean = int(np.mean(o3s_first_corrected))
            corrects = []
            for i in o3s:
                # corrects.append('1')
                if mean - sigma_count * sigma < i < mean + sigma_count * sigma:
                    corrects.append('1')
                else:
                    corrects.append('0')
            return corrects, sigma, mean
        else:
            return [0] * len(o3s), 0, 0

    @staticmethod
    def collect_data(data):
        """
        Collect data with First correction
        Args:
            data (list): List of o3 in CSV format (20190518 02:14:04;20190518 05:14:04;5.1;431;0;386;0)
        Returns:
            tuple: o3s_k, lines_arr_raw_to_file
        """
        sh_previous = 0
        # Sunheight correction
        sh_correction_on = False
        lines_arr_raw_to_file = []
        o3s_k = {"1": {"all": {"o3": [], "k": []},
                       "morning": {"o3": [], "k": []},
                       "evening": {"o3": [], "k": []}
                       },
                 "2": {"all": {"o3": [], "k": []},
                       "morning": {"o3": [], "k": []},
                       "evening": {"o3": [], "k": []}
                       }
                 }
        for line_raw in data:
            line_arr = line_raw.split(';')
            lines_arr_raw_to_file.append(line_arr)
            sh = float(line_arr[2])
            sh_condition = PARS['calibration2']['visible_sunheight_min'] < sh < PARS['calibration2'][
                'visible_sunheight_max']
            if sh_previous <= sh:
                part_of_day = "morning"
            else:
                part_of_day = "evening"
            sh_previous = sh
            current_o3 = {"1": int(line_arr[3]), "2": int(line_arr[5])}
            if sh_correction_on:
                corrects = {"1": int(line_arr[4] if sh_condition else 0), "2": int(line_arr[6] if sh_condition else 0)}
            else:
                corrects = {"1": int(line_arr[4]), "2": int(line_arr[6])}
            for pair in ["1", "2"]:
                for part_day in [part_of_day, 'all']:
                    o3s_k[pair][part_day]['o3'].append(current_o3[pair])
                    o3s_k[pair][part_day]["k"].append(corrects[pair])
                    o3s_k[pair][part_day]["text"] = ""
        return o3s_k, lines_arr_raw_to_file

    def second_correction(self, o3s_k1):
        """

        Args:
            o3s_k1 (dict):

        Returns:
            dict
        """
        o3s_k2 = {"1": {"all": {"o3": [], "k": []},
                        "morning": {"o3": [], "k": []},
                        "evening": {"o3": [], "k": []}
                        },
                  "2": {"all": {"o3": [], "k": []},
                        "morning": {"o3": [], "k": []},
                        "evening": {"o3": [], "k": []}
                        }
                  }
        no_data_for_part_of_day = {"all": False, "morning": False, "evening": False}
        for pair in ["1", "2"]:
            for part_of_day in ["all", "morning", "evening"]:
                text = '\n'
                if no_data_for_part_of_day[part_of_day]:
                    continue
                if o3s_k1[pair][part_of_day]["o3"]:
                    o3s_k2[pair][part_of_day]["o3"] = o3s_k1[pair][part_of_day]["o3"]
                    o3_corrected = []
                    for o3, k in zip(o3s_k1[pair][part_of_day]['o3'], o3s_k1[pair][part_of_day]['k']):
                        if k == 1:
                            o3_corrected.append(o3)
                    o3s_k2[pair][part_of_day]['k'], \
                    o3s_k2[pair][part_of_day]["sigma"], \
                    o3s_k2[pair][part_of_day]["mean"] = self.get_second_corrects(
                        o3s_k1[pair][part_of_day]["o3"], o3_corrected)
                    # Если в первой корректировке 0, то во второй будет тоже 0,
                    # иначе будет значение второй корректировки
                    # TODO: Repair mean/sigma correct condition
                    # o3s_k2[pair][part_of_day]["k"] = [str(int(i1) and int(i2)) for i1, i2 in
                    #                                   zip(o3s_k1[pair][part_of_day]["k"],
                    #                                       o3s_k2[pair][part_of_day]["k"])]

                    o3s_k2[pair][part_of_day]["k"] = o3s_k1[pair][part_of_day]["k"]

                    try:
                        text = 'Среднее значение ОСО (P{}): {}\nСтандартное отклонение: {}\n'.format(
                            pair, o3s_k2[pair][part_of_day]["mean"], o3s_k2[pair][part_of_day]["sigma"])
                    except KeyError as err:
                        print("INFO: procedures.py: No data files for {} (line: {})".format(
                            err, sys.exc_info()[-1].tb_lineno))
                        no_data_for_part_of_day[part_of_day] = True
                o3s_k2[pair][part_of_day]['text'] = text
        return o3s_k2


def calculate_final_files(source, mode, write_daily_file, data_source_flag):
    """

    Args:
        source (str | list): Source to read (Filename or Data)
        mode (str): "ZD" or "SD"
        write_daily_file (bool): Allow writing file with mean ozone, else just calculate (True or False)
        data_source_flag (str): Select source of data: read from file or get ozone from variable ("file" or "calculate")

    Returns:
        dict
    """
    perform_second_correction = True
    all_data = []
    data = []
    corr = Correction(data)
    if source:
        try:
            if data_source_flag == "file":
                with open(source) as f:
                    all_data = f.readlines()
                    data = sorted(all_data[1:])
            elif data_source_flag == "calculate":
                data = source
            if mode == "ZD":
                # === First correction check (100 < o3 < 600) and sunheight values from parameters (15 < 40) ===
                o3s_k1, lines_arr_raw_to_file = corr.collect_data(data)
                if perform_second_correction:
                    # === Second correction check ===
                    o3s_k2 = corr.second_correction(o3s_k1)
                    if write_daily_file is True and data_source_flag == "file":
                        with open(os.path.join(os.path.dirname(source), 'mean_' + os.path.basename(source)), 'w') as f:
                            print(';'.join(all_data[:1]), file=f, end='')
                            for line, correct1, correct2 in zip(lines_arr_raw_to_file, o3s_k2["1"]["all"]['k'],
                                                                o3s_k2["2"]["all"]['k']):
                                part1 = line[:-3]
                                part2 = line[-2:-1]
                                print(';'.join(part1 + [str(correct1)] + part2 + [str(correct2)]), file=f)
                            print(o3s_k2['1']['all']['text'] + o3s_k2['2']['all']['text'], file=f)
                            print('2) Mean File Saved:\n{}'.format(
                                os.path.join(os.path.dirname(source), 'mean_' + os.path.basename(source))))
                    for pair in ['1', '2']:
                        for part_of_day in ["all", "morning", "evening"]:
                            o3s_k2[pair][part_of_day]["o3_count"] = len(o3s_k2[pair][part_of_day]["o3"])
                    return o3s_k2
            elif mode == "SD":
                pass
        except Exception as err:
            print(err, sys.exc_info()[-1].tb_lineno)
            raise err


def get_polynomial_result(coefficients, x):
    return sum([float(k) * float(x) ** degree for k, degree in zip(coefficients, range(len(coefficients)))])


def sumarize(a):
    return round(sum([float(i) for i in a if i != '']), 3)


def find_index_value_greater_x(list, x):
    index_value_high = next((list.index(value) for value in list if value > x), len(list) - 1)
    "Если ниже минимального значения - берём 2 ближайших значения"
    if index_value_high == 0:
        index_value_high = 1
    return index_value_high


def get_ozone_by_nomographs(r12clear, mueff, o3_num):
    """
    Reads nomograph
    Args:
        r12clear ():
        mueff ():
        o3_num ():

    Returns:

    """
    mueff_list, r12_list, ozone_list = read_nomographs(o3_num)
    "Найти значения mueff, между которыми находится наше значение"
    index_mueff_high = find_index_value_greater_x(mueff_list, mueff)
    index_mueff_low = index_mueff_high - 1
    "вычисление r12 на нижней и на верхней номограмме путём линейной интерполяции"
    r12high_index = find_index_value_greater_x(r12_list[index_mueff_high], r12clear)
    r12low_index = r12high_index - 1
    r12low = (r12_list[index_mueff_low][r12low_index]
              + (r12_list[index_mueff_high][r12low_index]
                 - r12_list[index_mueff_low][r12low_index])
              * (mueff - mueff_list[index_mueff_low])
              / (mueff_list[index_mueff_high]
                 - mueff_list[index_mueff_low]))
    r12high = (r12_list[index_mueff_low][r12high_index]
               + (r12_list[index_mueff_high][r12high_index]
                  - r12_list[index_mueff_low][r12high_index])
               * (mueff - mueff_list[index_mueff_low])
               / (mueff_list[index_mueff_high]
                  - mueff_list[index_mueff_low]))
    ozone = (ozone_list[r12low_index]
             + ((ozone_list[r12high_index]
                 - ozone_list[r12low_index])
                * (r12clear - r12low))
             / (r12high - r12low))
    return ozone


def erithema(x, c):
    nm = (x ** 2) * eval(c[0]) + x * eval(c[1]) + eval(c[2])
    a = 0
    if nm <= 298:
        a = 1
    elif 298 < nm:  # <=325:
        a = 10 ** (0.094 * (298 - nm))
    # elif nm>325:
    #     a = 10**(-0.015 * (410 - nm))
    return a


def nm2pix(nm, abc, add):
    nm = float(nm)
    pix = 0
    if not 270 < nm < 430:
        print(nm, 'nm2pix: error')
        return 0
    if 350 < nm < 430:
        pix = 1500
    while pix2nm(abc, pix, 1, add) < nm:
        pix += 1
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
        print("Check settings file nm(pix) section")
        return 0


def spectr2zero(p_zero, p_lamst, spectr):
    spectrum = [0] * len(spectr)
    try:
        mv = sum(spectr[p_zero["1"]:p_zero["2"]]) / len(spectr[p_zero["1"]:p_zero["2"]])
        for i in range(p_lamst, len(spectr) - 1):
            spectrum[i] = round(spectr[i] - mv)
    except IndexError as err:
        show_error_in_separate_window(err, "В файле отсутствует спектр")
    finally:
        return spectrum


def pre_calc_o3(lambda_consts, lambda_consts_pix, spectrum, prom, mu, o3_num):
    p_mas = []
    j = 0
    try:
        # Mu effective correction
        correct_mu_eff_start = PARS['calibration2']['coorect_mu_eff_start']
        correct_mu_eff_end = PARS['calibration2']['coorect_mu_eff_end']
    except KeyError:
        correct_mu_eff_start = 0
        correct_mu_eff_end = 30
    while j < len(lambda_consts):
        jj = lambda_consts_pix[j]  # in Pixels
        s = sumarize(spectrum[jj - prom:jj + prom + 1])
        if s:
            p_mas.append(s)
        else:
            p_mas.append(1)
        j += 1
    r12m = p_mas[0] / p_mas[1]
    r23m = p_mas[2] / p_mas[3]
    mueff = (1 + mu) / 2
    if mueff < PARS['calibration2']["mu_effect_" + o3_num]:
        r23clean = get_polynomial_result(PARS['calibration2']['kzLess' + o3_num], mueff)
    else:
        r23clean = get_polynomial_result(PARS['calibration2']['kzLarger' + o3_num], mueff)
    kz_obl_f = get_polynomial_result(PARS['calibration2']['kz_obl' + o3_num], (r23clean / r23m))
    r12clear = kz_obl_f * r12m
    try:
        o3 = int(get_ozone_by_nomographs(r12clear, mueff, o3_num))
    except Exception as err:
        print("Ozone can't be calculated: {} (line: {})".format(err, sys.exc_info()[-1].tb_lineno))
        o3 = -1
    if 100 <= o3 <= 600:  # and correct_mu_eff_start <= mueff <= correct_mu_eff_end:
        correct = 1
    else:
        correct = 0
    return o3, correct, [round(i, 4) for i in [r12m, r23m, kz_obl_f, r23clean / r23m]]


class CalculateOnly:
    # Calculate for mesurement
    def __init__(self):

        # Calc ozone
        # self.o3 = 0
        self.prom = int(PARS['calibration2']['pix+-'] / eval(CONF_Z[1]))
        self.lat = PARS['station']['latitude']
        self.lon = PARS['station']['longitude']
        self.pelt = int(PARS['station']['timezone'])
        # Calc UV
        self.uv = 0
        self.curr_o3_dict = {'uva': [2, P1_UVA, P2_UVA],
                             'uvb': [3, P1_UVB, P2_UVB],
                             'uve': [4, P1_UVE, P2_UVE]}

    def calc_ozon(self, spectr, mu):
        """
        data['spectr'] => spectrum
        data['mu']
        """
        spectrum = spectr2zero(P_ZERO, P_LAMST, spectr)
        """Расчет озона"""
        o3 = {}
        correct = {}
        additional_data = {}
        for pair, values in LAMBDA_CONSTS.items():
            o3[pair], correct[pair], additional_data[pair] = pre_calc_o3(
                LAMBDA_CONSTS[pair],
                LAMBDA_CONSTS_PIX[pair],
                spectrum,
                self.prom,
                mu,
                pair)
        return o3, correct, additional_data

    def calc_uv(self, uv_mode, spectr, expo, sensitivity, sens_eritem):
        p1 = self.curr_o3_dict[uv_mode][1]
        p2 = self.curr_o3_dict[uv_mode][2]
        uv = 0
        spectrum = spectr2zero(P_ZERO, P_LAMST, spectr)
        try:
            if uv_mode in ['uva', 'uvb']:
                uv = sum(np.array(spectrum[p1:p2]) * np.array(sensitivity[p1:p2]))
            elif uv_mode == 'uve':
                uv = sum([float(spectrum[i]) * sens_eritem[i] * sensitivity[i] for i in range(p1, p2, 1)])
            uv *= float(eval(CONF_S[1])) * PARS['device']['graduation_expo'] / expo
        except Exception as err:
            print('procedures.calc_uv: ', err)
            uv = 0
        return int(round(uv, 1))


def sunheight(latitude, longitude, date_time, timezone):
    """
    Calculate mu, atmospheric mass (amas) and sun height.
    Args:
        latitude (float): Altitude
        longitude (float): Longitude
        date_time (datetime): Datetime object
        timezone (str | int): Timezone

    Returns:
        Ints: mu, atmospheric mass (amas) and sun height
    """
    lat, lon, timezone = float(latitude), float(longitude), int(timezone)
    # Расчёт высоты солнца всегда по UTC, поэтому "timezone=0"
    timezone = 0
    """
    altitude - широта в градусах и минутах (+-ГГ.ММ) +северная -южная
    longitude - долгота в градусах и минутах (+-ГГ.ММ) +западная -восточная
    date_time - дата+время
    timezone - часовой пояс (+-П)
    """
    lat = (lat - 0.4 * copysign(1, lat) * round(abs(lat) // 1)) * pi / 108
    lon = (lon - 0.4 * copysign(1, lon) * round(abs(lon) // 1)) / 0.6
    timer = date_time.hour * 3600 + date_time.minute * 60 + date_time.second  # Текущее время в секундах
    tim = timer - 3600 * timezone  # Гринвическое время
    day = date_time.day + 58
    month = date_time.month
    year = date_time.year
    if month < 3:
        year -= 1
    d_m = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]  # Месяцы кроме февраля
    d_d = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31]  # Количество дней в месяце
    i = 0
    while i < 11:
        if month == d_m[i]:
            break
        else:
            day += d_d[i]
        i += 1
    dd = day + 365 * year + round(year // 4) - round(year // 100) + round(year // 400) + 13 / 38
    day = (dd + tim / 3600 / 24) * pi / 182.6213
    s = 0.00686 - 0.39915 * cos(day) + 0.07432 * sin(day)
    s += -0.00693 * cos(2 * day) + 0.00114 * sin(2 * day)
    s += -0.00226 * cos(3 * day) + 0.0012 * sin(3 * day)
    ty = -0.017 - 0.43 * cos(day) + 7.35 * sin(day) + 3.35 * cos(2 * day) + 9.366 * sin(2 * day)
    r = pi * (tim / 3600 - ty / 60 - lon / 15 - 12) / 12
    q = sin(lat) * sin(s) + cos(lat) * cos(s) * cos(r)
    hp = atan(q / sqrt(1 - q ** 2))
    hg = hp * 180 / pi
    z = sin(pi / 2 - hp) ** 2
    mu = 6391.229 / sqrt(6391.229 ** 2 - 6371.223 ** 2 * z)
    z1 = 1 / cos(pi / 2 - hp)
    atmosphere_mas = 0
    if hg <= 0:
        pass
    elif 0 < hg < 20:
        atmosphere_mas = 45.022 * hg ** (-0.9137)
    else:
        atmosphere_mas = z1 - (z1 - 1) * (0.0018167 - 0.002875 * (z1 - 1) - 0.0008083 * (z1 - 1) ** 2)
    return round(mu, 3), round(atmosphere_mas, 3), round(hg, 3)


def get_time_next_start(latitude, longitude, timezone, sun_height_min):
    """Расчёт времени следующего измерения"""
    time_now = datetime.now()
    mu, amas, sh = sunheight(latitude, longitude, time_now, timezone)
    if sh < sun_height_min:
        for t in [3600, 60, 1]:
            while sh < sun_height_min:
                time_now += timedelta(0, t)
                mu, amas, sh = sunheight(latitude, longitude, time_now, timezone)
            else:
                time_now -= timedelta(0, t)
                mu, amas, sh = sunheight(latitude, longitude, time_now, timezone)
    return str(time_now).split('.')[0]


def write_final_file(chan, date_utc, sh, calc_result, add_to_name, create_new_file):
    """Ozone/UV calculation and write to final file
    PARS - settings.json
    home - home directory (Default: D:\\UFOS)
    chan - ZD or SD
    date_utc - UTC datetime from measurement
    sh - Sun height from measurement
    calc_result - ...
    add_to_name - Add text to the beginning of the filename
    create_new_file - True"""
    try:
        date = datetime.strptime(date_utc, '%Y%m%d %H:%M:%S')
        date_local = datetime.strftime(date + timedelta(hours=int(PARS["station"]["timezone"])),
                                       '%Y%m%d %H:%M:%S')  # Local Datetime
        if chan == 'ZD':
            type_of_measurement = 'Ozone'
            header = ';'.join(
                ['DatetimeUTC', 'DatetimeLocal', 'Sunheight[°]', 'OzoneP1[D.u.]', 'CorrectP1', 'OzoneP2[D.u.]',
                 'CorrectP2'])
            text_out = ';'.join([str(i) for i in
                                 [date_utc, date_local, sh, calc_result['o3_1'], calc_result['correct_1'],
                                  calc_result['o3_2'], calc_result['correct_2']]])
        elif chan == 'SD':
            type_of_measurement = 'UV'
            header = ';'.join(
                ['DatetimeUTC', 'DatetimeLocal', 'Sunheight[°]', 'UV-A[mWt/m^2]', 'UV-B[mWt/m^2]', 'UV-E[mWt/m^2]'])
            text_out = ';'.join([str(i) for i in
                                 [date_utc, date_local, sh, calc_result['uva'], calc_result['uvb'],
                                  calc_result['uve']]])
        else:
            type_of_measurement = ''
            header = ''
            text_out = ''
        if chan == 'ZD' or chan == 'SD':
            path = make_dirs(measure_month_dir(date, type_of_measurement))
            name = '{}m{}_{}_{}.txt'.format(add_to_name,
                                            PARS['device']['id'],
                                            type_of_measurement,
                                            date.strftime('%Y%m%d'))
            if not os.path.exists(os.path.join(path, name)) or create_new_file:
                with open(os.path.join(path, name), 'w') as f:
                    print(header, file=f)
            with open(os.path.join(path, name), 'a') as f:
                print(text_out, file=f)
            return os.path.join(path, name)
    except Exception as err:
        print('write_final_file: ', end='')
        text = "Error: {}, Line: {}".format(str(err), sys.exc_info()[-1].tb_lineno)
        LOGGER.error(text)


def write_analyse_file(chan, date_utc, sh, calc_result, add_to_name, create_new_file=True):
    """
    Ozone calculation for analyse and write to final file
    Args:
        chan (str): ZD or SD
        date_utc (datetime): UTC datetime from measurement
        sh (float): Sun height from measurement
        calc_result (dict): Ozone data
        add_to_name (str): Add text to the beginning of the filename
        create_new_file (bool):

    Returns:

    """
    try:
        date = datetime.strptime(date_utc, '%Y%m%d %H:%M:%S')
        date_local = datetime.strftime(date + timedelta(hours=int(PARS["station"]["timezone"])),
                                       '%Y%m%d %H:%M:%S')  # Local Datetime
        if chan == 'ZD':
            type_of_measurement = 'Ozone'
            header = ';'.join(
                ['DatetimeUTC', 'DatetimeLocal', 'Sunheight[°]',
                 'OzoneP1[D.u.]', 'R12_P1', 'R23_P1', 'kz_obl_P1', 'R23clean/R23_P1', 'CorrectP1',
                 'OzoneP2[D.u.]', 'R12_P2', 'R23_P2', 'kz_obl_P2', 'R23clean/R23_P2', 'CorrectP2'])
            text_out = ';'.join(
                [str(i) for i in [date_utc,
                                  date_local,
                                  sh,
                                  calc_result['o3_1'],
                                  *calc_result['additional_data_1'],
                                  calc_result['correct_1'],
                                  calc_result['o3_2'],
                                  *calc_result['additional_data_2'],
                                  calc_result['correct_2']]]).replace(".", ",")
            name = '{}m{}_{}_{}.csv'.format(add_to_name,
                                            PARS['device']['id'],
                                            type_of_measurement,
                                            datetime.strftime(date, '%Y%m%d'))
            path = make_dirs(measure_month_dir(date, type_of_measurement))
            if not os.path.exists(os.path.join(path, name)) or create_new_file:
                with open(os.path.join(path, name), 'w') as f:
                    print(header, file=f)
            with open(os.path.join(path, name), 'a') as f:
                print(text_out, file=f)
            return os.path.join(path, name)
    except Exception as err:
        print('write_analyse_file: ', end='')
        text = "Error: {}, Line: {}".format(str(err), sys.exc_info()[-1].tb_lineno)
        LOGGER.error(text)


CONF_Z = PARS['calibration']['nm(pix)']['Z']
CONF_S = PARS['calibration']['nm(pix)']['S']
LAMBDA_CONSTS = {pair: PARS['calibration']['points']['o3_pair_{}'.format(pair)] +
                       PARS['calibration']['points']['cloud_pair_{}'.format(pair)] for pair in ["1", "2"]}
P1_UVA, P2_UVA = nm2pix(315, CONF_S, 0), nm2pix(400, CONF_S, 0)
P1_UVB, P2_UVB = nm2pix(280, CONF_S, 0), nm2pix(315, CONF_S, 0)
P1_UVE, P2_UVE = 0, 3691
P_ZERO = {pair: nm2pix(nm, CONF_Z, 0) for pair, nm in zip(["1", "2"], [290, 295])}
P_LAMST = nm2pix(290, CONF_Z, 0)
LAMBDA_CONSTS_PIX = {pair: [nm2pix(i, CONF_Z, 0) for i in const] for pair, const in LAMBDA_CONSTS.items()}
