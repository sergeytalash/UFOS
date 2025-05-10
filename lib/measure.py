import base64
import json
import os
import socket
import sys
import traceback
from datetime import datetime as dtm
from datetime import timedelta
from time import sleep

import numpy as np
import serial

try:
    from lib import calculations as calc, com, core
except (ImportError, ModuleNotFoundError):
    import calculations as calc, com, core


class MeasureClass:
    def __init__(self):
        self.tries_allowed = 3
        self.tries_done = 0
        self.measure_count = 1
        self.day_changed = False
        self.last_file_o3 = ''
        self.last_file_uv = ''
        self.measure_data = {'ZD': {}, 'SD': {}}
        self.calc_result = {'ZD': {}, 'SD': {}}
        self.file2send = {}
        self.t1 = ''
        self.t2 = ''
        self.time_now = dtm.now()
        self.time_now_local = self.time_now + timedelta(
            hours=int(core.PARS["station"]["timezone"]))  # Local Datetime
        self.path = core.measure_day_dir(self.time_now_local)
        self.Dspectr = []
        self.ZDspectr = []
        self.ZS_spectr = []
        self.measured_spectrZaD = []
        self.measured_skoZaD = 0
        self.path_sending = ''
        self.name = ''
        self.all_measured_data = {}
        self.expo = core.PARS['device']['auto_expo_min']
        self.chan = ''
        self.altD_flag = 0
        self.sensitivityZ = core.read_sensitivity("Z")
        self.sensitivityS = core.read_sensitivity("S")
        self.sensitivity_eritem = core.read_sensitivity("E")

    def analyze_spectr(self, spectr):
        """
        Analyse and calculate necessary variables just after measurement is done.
        Args:
            spectr (list): Measured spectre [0..3691]

        Returns:

        """
        try:
            time_now = dtm.now()  # UTC Datetime
            time_now_local = time_now + timedelta(hours=int(core.PARS["station"]["timezone"]))  # Local Datetime
            mu, amas, sh = calc.sunheight(core.PARS["station"]["latitude"],
                                          core.PARS["station"]["longitude"],
                                          time_now,
                                          core.PARS["station"]["timezone"])
            """Header"""
            self.all_measured_data = {
                "id": {
                    "device": core.DEVICE_ID,
                    "station": core.PARS["station"]["id"]
                },
                "mesurement": {
                    "datetime": time_now.strftime('%Y%m%d %H:%M:%S'),
                    "datetime_local": time_now_local.strftime('%Y%m%d %H:%M:%S'),
                    "timezone": core.PARS["station"]["timezone"],
                    "latitude": core.PARS["station"]["latitude"],
                    "longitude": core.PARS["station"]["longitude"],
                    "exposition": self.expo,
                    "accummulate": core.PARS["device"]["accummulate"],
                    "channel": self.chan,
                    "temperature_ccd": self.t1,
                    "temperature_poly": self.t2
                },
                "calculated": {
                    "mu": round(mu, 4),
                    "amas": round(amas, 4),
                    "sunheight": round(sh, 4),
                    "sko": round(float(np.std(spectr[core.PIX_WORK_INTERVAL])), 4),
                    "mean": round(float(np.mean(spectr[core.PIX_WORK_INTERVAL])), 4),
                    "dispersia": round(float(np.var(spectr[core.PIX_WORK_INTERVAL])), 4)
                }
            }
            if self.chan in ['Z', 'S']:
                # Расчёт СКО для Спектра (-) altD (темновой до 500 пикс)
                self.measured_spectrZaD = np.array(spectr) - np.mean(spectr[100:500])
                self.measured_skoZaD = np.std(self.measured_spectrZaD[core.PIX_WORK_INTERVAL])
                self.all_measured_data["spectr"] = np.array(spectr).tolist()
            elif self.chan[0] == 'D':
                # Если 'СКО D измеренное' < 100 И 'СКО Z-aD' > 100"""
                measured_sko = self.all_measured_data["calculated"]["sko"]
                pars_sko_d = core.PARS["calibration"]["sko_D"]
                pars_sko_zad = core.PARS["calibration"]["sko_ZaD"]
                if measured_sko < pars_sko_d and self.measured_skoZaD > pars_sko_zad:
                    self.altD_flag = 0
                # Если 'СКО D измеренное' > 100 И 'СКО Z-aD' > 100"""
                elif measured_sko > pars_sko_d and self.measured_skoZaD > pars_sko_zad:
                    self.altD_flag = 1
                else:
                    self.altD_flag = 2
                self.all_measured_data["spectr"] = np.array(spectr).tolist()
            elif self.chan in ['ZD', 'SD']:
                if self.altD_flag == 0:
                    # Если всё ок
                    self.all_measured_data["spectr"] = np.array(spectr).tolist()
                    self.all_measured_data["mesurement"]["status"] = 0
                elif self.altD_flag == 1:
                    # Если плохой темновой спектр, использовать альтернативный темновой (spectr[100:500])
                    self.all_measured_data["spectr"] = np.array(self.measured_spectrZaD).tolist()
                    self.all_measured_data["mesurement"]["status"] = 1
                else:
                    self.all_measured_data["spectr"] = np.array(spectr).tolist()
                    self.all_measured_data["mesurement"]["status"] = 2
        except Exception as err:
            text = "(measure) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
            print(text)
            core.LOGGER.error(text)

    @staticmethod
    def pix2nm(pix):
        nm = 0
        deg = len(core.PARS["calibration"]["nm(pix)"]["Z"]) - 1
        for i in core.PARS["calibration"]["nm(pix)"]["Z"]:
            nm += eval(i) * pix ** deg
            deg -= 1
        return nm

    def nm2pix(self, nm):
        pix = 0
        while self.pix2nm(pix) < nm:
            pix += 1
        return pix

    def add_calculated_line_to_final_file(self, spectr, mu, expo, sensitivityZ, sensitivityS,
                                          sensitivity_eritem, print_o3_to_console):
        """

        Args:
            spectr (list):
            mu (float):
            expo (int):
            sensitivityS (list):
            sensitivity_eritem (list):
            print_o3_to_console (bool):

        Returns:

        """
        calco = calc.CalculateOnly()
        o3_dict = {}
        if self.chan == 'ZD':

            o3, correct, additional_data = calco.calc_ozon(spectr, mu)
            for pair in ["1", "2"]:
                for text, value in zip(["o3", "correct", "additional_data"],
                                       [int(o3[pair]), correct[pair], additional_data[pair]]):
                    o3_dict[text + '_' + pair] = value

            o3_1, correct1 = o3_dict['o3_1'], o3_dict['correct_1']
            o3_2, correct2 = o3_dict['o3_2'], o3_dict['correct_2']
            if print_o3_to_console:
                print('=> OZONE: P1 = {}, P2 = {}'.format(o3_1, o3_2))
        elif self.chan == 'SD':
            uva = calco.calc_uv('uva', spectr, expo, sensitivityS, sensitivity_eritem)
            uvb = calco.calc_uv('uvb', spectr, expo, sensitivityS, sensitivity_eritem)
            uve = calco.calc_uv('uve', spectr, expo, sensitivityS, sensitivity_eritem)
            o3_dict = {'uva': uva, 'uvb': uvb, 'uve': uve}
        self.calc_result[self.chan] = o3_dict
        return self.calc_result, self.chan

    def write_file(self):
        try:
            dirs_sending = core.DEVICE_DIR_L + ['Sending']
            tmp = core.measure_day_dir(self.time_now_local, deep=True)
            self.path, measure_count = core.make_dirs(tmp, reset_counter=True)
            if measure_count:
                self.measure_count = measure_count
            self.path_sending, _ = core.make_dirs(dirs_sending)
            self.name = 'm{}_{}_{}_{}.txt'.format(core.DEVICE_ID,
                                                  str(self.measure_count).zfill(3),
                                                  self.chan,
                                                  self.time_now_local.strftime('%Y%m%d%H%M'))
            with open(os.path.join(self.path, self.name), 'w') as f:
                json.dump(self.all_measured_data, f, ensure_ascii=False,
                          indent='', sort_keys=True)
                print('\n>>> {}'.format(self.name))
                core.LOGGER.info('\n>>> {}'.format(self.name))
            if self.chan in ['ZD', 'SD']:
                self.file2send[self.chan] = self.name
                self.add_calculated_line_to_final_file(self.all_measured_data['spectr'],
                                                       self.all_measured_data['calculated']['mu'],
                                                       self.all_measured_data['mesurement']['exposition'],
                                                       self.sensitivityS,
                                                       self.sensitivity_eritem,
                                                       True)
                path_file = calc.write_final_file(self.chan,
                                                  self.all_measured_data["mesurement"]["datetime"],
                                                  round(self.all_measured_data["calculated"]["sunheight"], 1),
                                                  self.calc_result[self.chan],
                                                  '',
                                                  False)

                if self.chan == 'ZD':
                    calc.write_analyse_file(self.chan,
                                            self.all_measured_data["mesurement"]["datetime"],
                                            round(self.all_measured_data["calculated"]["sunheight"], 1),
                                            self.calc_result[self.chan],
                                            'Analyse_',
                                            False)
                    self.last_file_o3 = path_file
                elif self.chan == 'SD':
                    self.last_file_uv = path_file
        except Exception as err:
            text = "(measure) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
            print(text)
            core.LOGGER.error(text)

    def change_channel(self, chan):
        core.LOGGER.debug('Переключение на канал {}.'.format(
            core.PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8')))
        data, t1, t2, text, self.tries_done = com.UfosDataToCom(
            50, core.PARS['device']['accummulate'], chan, 'N').device_ask()

    def write_file4send(self, chan, data4send):
        with open(os.path.join(self.path_sending, self.file2send[chan]), 'w') as f:
            f.write(data4send)

    def make_line(self):
        try:
            debug = 0
            encode = 0
            if debug:
                with open('test.txt', 'w') as f:
                    print(self.measure_data, file=f)  # measurement
                    print('==========================================', file=f)
                    print(core.PARS, file=f)  # Settings
                    print('==========================================', file=f)
                    print(core.CONNECT_PARS, file=f)  # connect Settings
                    print('==========================================', file=f)
                    print(self.calc_result, file=f)  # o3 + uv
            if encode:
                points2send = base64.b64encode(str(core.PARS['calibration']['points']).encode('ascii')).decode('ascii')
                pars2send = base64.b64encode(str(core.PARS).encode('ascii')).decode('ascii')
            else:
                points2send = str(core.PARS['calibration']['points']).replace("'", '"')
                pars2send = str(core.PARS).replace("'", '"')
            for chan in self.calc_result.keys():
                uva, uvb, uve = 0, 0, 0
                o3 = 0
                correct = -1
                if chan == 'ZD':
                    correct = self.calc_result[chan]['correct_1']
                    o3 = self.calc_result[chan]['o3_1']
                elif chan == 'SD':
                    uva = self.calc_result[chan]['uva']
                    uvb = self.calc_result[chan]['uvb']
                    uve = self.calc_result[chan]['uve']

                data4send = """#{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10};\
{11}@{12};{13};{14};{15};{16};{17};{18};{19};{20};\
{21};{22};{23};{24};{25};{26};{27};{28};{29};{30};{31}#""".format(self.measure_data[chan]['id']['device'],
                                                                  self.measure_data[chan]['id']['station'],
                                                                  self.measure_data[chan]['mesurement']['channel'][
                                                                                                  0] + '-' +
                                                                  self.measure_data[chan]['mesurement']['channel'][1],
                                                                  self.measure_data[chan]['mesurement']['datetime'],
                                                                  self.measure_data[chan]['mesurement']['exposition'],
                                                                  'NULL',  # gain = 0
                                                                  self.measure_data[chan]['mesurement'][
                                                                                                  'temperature_ccd'],
                                                                  o3,  # mesure
                                                                  uva,  # mesure
                                                                  uvb,  # mesure
                                                                  uve,  # mesure
                                                                  self.measure_data[chan]['spectr'],
                                                                  correct,  # gain = 0
                                                                  # ==== Additional parameters ====
                                                                  self.measure_data[chan]['mesurement'][
                                                                                                  'datetime_local'],
                                                                  self.measure_data[chan]['mesurement']['timezone'],
                                                                  core.PARS['station']['sun_height_min'],
                                                                  self.measure_data[chan]['mesurement']['accummulate'],
                                                                  'NULL',  # set_run
                                                                  self.measure_data[chan]['id']['device'],  # dev_id1
                                                                  core.PARS['station']['interval'],
                                                                  core.PARS['device']['auto_exposition'],  # repeat1
                                                                  core.PARS['device']['amplitude_max'],
                                                                  self.measure_data[chan]['mesurement']['latitude'],
                                                                  self.measure_data[chan]['mesurement']['longitude'],
                                                                  pars2send,  # pix2nm1
                                                                  'NULL',  # kz1,
                                                                  'NULL',  # kz_obl1,
                                                                  'NULL',  # omega1,
                                                                  'NULL',
                                                                  points2send,
                                                                  'NULL',  # pixels1,
                                                                  'NULL',
                                                                  'NULL')
                #                    print(data4send)

                # Write file for next sending
                ##                print(data4send)
                self.write_file4send(chan, data4send)

        except Exception as err:
            print(err, sys.exc_info()[-1].tb_lineno)
            raise err

    @staticmethod
    def ftp_send(host, port, remote_dir, user, password, file2send):
        return 'FTP method is not configured'
        # file_name = os.path.basename(file2send)
        # path = file2send.split(file_name)[0][:-1]
        # ftp = FTP()
        # #    print('Подключение к FTP...',end=' ')
        # try:
        #     ftp.connect(host=host, port=port)
        #     ftp.login(user=user, passwd=password)
        #     #        print('OK')
        #     try:
        #         dir_list = []
        #         ftp.cwd(remote_dir)
        #         #            ftp.debug(1)
        #         create_dirs(ftp, file2send)
        #         ftp.storlines('STOR ' + file_name, open(file2send, 'rb'))
        #         tex = 'OK'
        #     except Exception as err2:
        #         tex = err2
        #     finally:
        #         ftp.close()
        # except:
        #     tex = 'Ошибка подключения FTP!'
        # return (tex)

    @staticmethod
    def sock_send(ip, port, data2send):
        """

        Args:
            host (str, list):
            port (int):
            data2send (str):

        Returns:
            str: 'OK' if at least one server is available else 'ERR'
        """
        status = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        ##        print("Connection [initialized]", end='')
        try:
            sock.connect((ip, port))
            print("[connected]", end='')
            sock.send(data2send.encode(encoding='utf-8'))
            print("[data sent]", end='')
            sock.close()
            print("[closed]", end='')
            status[ip] = 'OK'
        except (TimeoutError, socket.timeout) as err:
            status[ip] = str(err)
        if 'OK' in status.values():
            return 'OK'
        else:
            print(f'No connection to server: {status}')
            return 'ERR'

    def send_file(self, file2send):
        tex = {}
        try:
            for send_type in ['socket', 'ftp']:
                if core.CONNECT_PARS[send_type + '_ip'] != '0':
                    tex[send_type] = ''
                    if send_type == 'socket':
                        with open(file2send) as f:
                            data2send = ''.join(f.readlines())
                            for ip in core.CONNECT_PARS['socket_ip'].split(','):
                                tex[send_type] = self.sock_send(ip,
                                                                int(core.CONNECT_PARS['socket_port']),
                                                                data2send)
                    elif send_type == 'ftp':
                        tex[send_type] = self.ftp_send(core.CONNECT_PARS['ftp_ip'],
                                                       int(core.CONNECT_PARS['ftp_port']),
                                                       core.CONNECT_PARS['ftp_path'],
                                                       core.CONNECT_PARS['ftp_user'],
                                                       core.CONNECT_PARS['ftp_pass'],
                                                       file2send)
                    if tex[send_type] == 'OK':
                        print('{} Отправлен {} (dev: {})'.format(file2send, send_type,
                                                                 self.all_measured_data['id']['device']))
                    else:
                        print(tex[send_type])

        except Exception as err:
            print('(measure.send_file) Error: {} Line: {}'.format(err, sys.exc_info()[2].tb_lineno))
        finally:
            return tex

    def measure(self):
        """Определение номера последнего измерения"""
        try:
            if os.path.exists(self.path):
                files = os.listdir(self.path)
                if files:
                    self.measure_count = max(set([int(i.split('_')[1]) for i in files if i.count('_') == 3]))
            else:
                self.measure_count = 1
            k = {'Z': 0, 'S': 0}
            if core.PARS['device']['auto_exposition'] == 1:
                self.measure_count += 1
                """ Z or S mesurement """
                expo_max = core.PARS['device']['auto_expo_max']
                for chan in core.PARS['device']['channel']:
                    self.expo = core.PARS['device']['auto_expo_min']
                    self.ZS_spectr = [0] * 3691
                    self.change_channel(chan)
                    while self.expo < expo_max:

                        try:
                            amp_min = core.PARS['device']['amplitude_min']
                            amp_max = core.PARS['device']['amplitude_max']
                            text = 'Канал {}. Эксп = {}'.format(
                                core.PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                                self.expo)
                            print(text, end='')
                            self.ZS_spectr, self.t1, self.t2, response, self.tries_done = com.UfosDataToCom(
                                self.expo, core.PARS['device']['accummulate'], chan, 'S').device_ask()
                            text = response
                            print(text)
                            core.LOGGER.info(text)
                            spectr_max = max(self.ZS_spectr[core.PIX_WORK_INTERVAL])
                            if amp_max > spectr_max > amp_min:
                                break
                            k[chan] = spectr_max / core.PARS['device']['amplitude_max']
                            if k[chan] != 0:
                                self.expo = int(self.expo / k[chan])

                        except Exception as err:
                            text = "(measure) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
                            print(text)
                            core.LOGGER.error(text)
                            raise err

                    else:
                        self.expo = core.PARS['device']['auto_expo_max']
                        text = 'Канал {}. Эксп = {}'.format(
                            core.PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text, end='')
                        self.ZS_spectr, self.t1, self.t2, response, self.tries_done = com.UfosDataToCom(
                            self.expo, core.PARS['device']['accummulate'], chan, 'S').device_ask()
                        # text += ' ' + response
                        text = response
                        # print('\r{}'.format(text))
                        print(text)
                        core.LOGGER.info(text)
                    self.chan = chan
                    self.analyze_spectr(self.ZS_spectr)
                    self.write_file()

                    """ D mesurement """
                    self.chan = 'D' + chan.lower()
                    self.change_channel('D')
                    text = 'Канал {}. Эксп = {}'.format(
                        core.PARS['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),
                        self.expo)
                    print(text)
                    self.Dspectr, self.t1, self.t2, response, self.tries_done = com.UfosDataToCom(
                        self.expo, core.PARS['device']['accummulate'], 'D', 'S').device_ask()
                    text += ' ' + response
                    print('\r{}'.format(text), end=' ')
                    core.LOGGER.info(text)
                    self.analyze_spectr(self.Dspectr)
                    self.write_file()

                    """ Z-D or S-D calculation """
                    self.chan = chan + 'D'
                    text = 'Расчёт спектра {}.'.format(self.chan)
                    print(text, end=' ')
                    core.LOGGER.info(text)
                    self.ZDspectr = np.array(self.ZS_spectr) - np.array(self.Dspectr)
                    self.analyze_spectr(self.ZDspectr)
                    self.write_file()
                    self.measure_data[self.chan] = self.all_measured_data

            else:
                for expo in core.PARS['device']['manual_expo']:
                    self.expo = expo
                    self.measure_count += 1
                    for chan in core.PARS['device']['channel']:
                        """ Z or S mesurement """
                        self.change_channel(chan)
                        text = 'Канал {}. Эксп = {}'.format(
                            core.PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text)
                        self.ZS_spectr, self.t1, self.t2, response, self.tries_done = com.UfosDataToCom(
                            self.expo, core.PARS['device']['accummulate'], chan, 'S').device_ask()
                        text += ' ' + response
                        print('\r{}'.format(text), end=' ')
                        core.LOGGER.info(text)
                        self.chan = chan
                        self.analyze_spectr(self.ZS_spectr)
                        self.write_file()

                        """ D mesurement """
                        self.chan = 'D' + chan.lower()
                        self.change_channel('D')
                        text = 'Канал {}. Эксп = {}'.format(
                            core.PARS['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text)
                        self.Dspectr, self.t1, self.t2, response, self.tries_done = com.UfosDataToCom(
                            self.expo, core.PARS['device']['accummulate'], 'D', 'S').device_ask()
                        text += ' ' + response
                        print('\r{}'.format(text), end=' ')
                        core.LOGGER.info(text)
                        self.analyze_spectr(self.Dspectr)
                        self.write_file()

                        """ Z-D or S-D calculation """
                        self.chan = chan + 'D'
                        text = 'Расчёт спектра {}.'.format(self.chan)
                        print(text, end=' ')
                        core.LOGGER.info(text)
                        self.ZDspectr = np.array(self.ZS_spectr) - np.array(self.Dspectr)
                        self.analyze_spectr(self.ZDspectr)
                        self.write_file()
                        self.measure_data[self.chan] = self.all_measured_data
        except TypeError:
            # print("No data from UFOS", str(err))
            pass
        except Exception as err:
            # text = "(measure) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
            # print(text)
            core.LOGGER.error(traceback.format_exc())
            raise err


class CheckSunAndMeasure:
    def __init__(self):
        self.home = os.getcwd()
        self.end_calculation = True
        self.time_now_utc = dtm.now()
        self.time_now_local = dtm.now()
        self.mu, self.amas, self.sunheight = 0, 0, 0
        self.timezone = timedelta(hours=int(core.PARS["station"]['timezone']))

    def start(self):
        while 1:
            try:
                com.UfosConnection().get_com_obj()
                self.time_now_utc = dtm.now()
                self.time_now_local = self.time_now_utc + self.timezone
                self.mu, self.amas, self.sunheight = calc.sunheight(core.PARS["station"]["latitude"],
                                                                    core.PARS["station"]["longitude"],
                                                                    self.time_now_utc,
                                                                    core.PARS["station"]["timezone"])
                main = MeasureClass()
                _, t1, t2, _, _ = com.UfosDataToCom(50, 1, 'D', 'Z').device_ask()
                if self.sunheight >= core.PARS["station"]["sun_height_min"]:
                    self.end_calculation = True
                    # Высота Солнца выше заданного параметра
                    print('=== Запуск измерения ===                      ', end='\r')
                    main.measure()

                    if main.tries_done > 0:
                        print('Кабель подключен к ПК, но не подключен к УФОС!', end='\r')
                        sleep(10)
                    else:
                        calc.calculate_final_files(main.last_file_o3, 'ZD', True, "file")
                        main.make_line()
                        print('========================')
                        next_time = self.time_now_local + timedelta(minutes=core.PARS["station"]["interval"])
                        self.mu, self.amas, self.sunheight = calc.sunheight(core.PARS["station"]["latitude"],
                                                                            core.PARS["station"]["longitude"],
                                                                            next_time,
                                                                            core.PARS["station"]["timezone"])
                        print(f"Temperature SSD: {t1} C, Polychromator: {t2} C")
                        print('Следующее измерение: {}'.format(str(next_time).split('.')[0]))

                        # Send files
                        send_ok = True
                        for file2send in os.listdir(main.path_sending):
                            if dtm.now() + self.timezone < next_time and send_ok:
                                sending_file = os.path.join(main.path_sending, file2send)
                                tex = main.send_file(sending_file)
                                core.LOGGER.debug(str(tex))
                                for status in tex.keys():
                                    if tex[status] == 'OK':
                                        os.remove(sending_file)
                                    else:
                                        send_ok = False
                            else:
                                break
                        while dtm.now() + self.timezone < next_time:
                            sleep(1)
                else:
                    # Высота Солнца менее заданного параметра
                    if self.end_calculation:
                        calc.calculate_final_files(main.last_file_o3, 'ZD', True, "file")
                        self.end_calculation = False
                    print('\rСледующее измерение: {}, '.format(
                        calc.get_time_next_start(core.PARS["station"]["latitude"],
                                                 core.PARS["station"]["longitude"],
                                                 core.PARS["station"]["timezone"],
                                                 core.PARS["station"]["sun_height_min"])) +
                          f"Temperature SSD: {t1} C, Polychromator: {t2} C", end='')
                    sleep(5)
            except (serial.serialutil.SerialException, TypeError, Exception) as err:
                text = "(measure.start SerialException) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
                print(f"\r{text}", end="")
                # print(traceback.format_exc())
                core.LOGGER.error(traceback.format_exc())
            except ValueError as err:
                if "COM" in str(err):
                    raise err
            finally:
                sleep(10)


if __name__ == "__main__":
    MeasureClass().sock_send("192.168.0.117", 80, "123")
