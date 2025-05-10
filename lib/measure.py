import base64
import socket
import sys

import numpy as np

from lib.calculations import *
from lib.com import *
from lib.core import *


class MeasureClass:
    def __init__(self):
        self.tries_allowed = 3
        self.tries_done = 0
        self.measure_count = 0
        self.last_file_o3 = ''
        self.last_file_uv = ''
        self.mesure_data = {'ZD': {}, 'SD': {}}
        self.calc_result = {'ZD': {}, 'SD': {}}
        self.file2send = {}
        self.t1 = ''
        self.t2 = ''
        self.time_now = datetime.now()
        self.time_now_local = self.time_now + timedelta(
            hours=int(PARS["station"]["timezone"]))  # Local Datetime
        self.path = measure_day_dir(self.time_now)
        self.Dspectr = []
        self.ZDspectr = []
        self.ZS_spectr = []
        self.measured_spectrZaD = []
        self.measured_skoZaD = 0
        self.path_sending = ''
        self.name = ''
        self.all_measured_data = {}
        self.expo = PARS['device']['auto_expo_min']
        self.chan = ''
        self.altD_flag = 0
        self.sensitivityZ = read_sensitivity("Z")
        self.sensitivityS = read_sensitivity("S")
        self.sensitivity_eritem = read_sensitivity("E")

    def analyze_spectr(self, spectr):
        """
        Analyse and calculate necessary variables just after measurement is done.
        Args:
            spectr (list): Measured spectre [0..3691]

        Returns:

        """
        try:
            time_now = datetime.now()  # UTC Datetime
            time_now_local = time_now + timedelta(hours=int(PARS["station"]["timezone"]))  # Local Datetime
            mu, amas, sh = sunheight(PARS["station"]["latitude"],
                                     PARS["station"]["longitude"],
                                     time_now,
                                     PARS["station"]["timezone"])
            """Header"""
            self.all_measured_data = {
                "id": {
                    "device": DEVICE_ID,
                    "station": PARS["station"]["id"]
                    },
                "mesurement": {
                    "datetime": time_now.strftime('%Y%m%d %H:%M:%S'),
                    "datetime_local": time_now_local.strftime('%Y%m%d %H:%M:%S'),
                    "timezone": PARS["station"]["timezone"],
                    "latitude": PARS["station"]["latitude"],
                    "longitude": PARS["station"]["longitude"],
                    "exposition": self.expo,
                    "accummulate": PARS["device"]["accummulate"],
                    "channel": self.chan,
                    "temperature_ccd": self.t1,
                    "temperature_poly": self.t2
                    },
                "calculated": {
                    "mu": round(mu, 4),
                    "amas": round(amas, 4),
                    "sunheight": round(sh, 4),
                    "sko": round(float(np.std(spectr[PIX_WORK_INTERVAL])), 4),
                    "mean": round(float(np.mean(spectr[PIX_WORK_INTERVAL])), 4),
                    "dispersia": round(float(np.var(spectr[PIX_WORK_INTERVAL])), 4)
                    }
                }
            if self.chan in ['Z', 'S']:
                # Расчёт СКО для Спектра (-) altD (темновой до 500 пикс)
                self.measured_spectrZaD = np.array(spectr) - np.mean(spectr[100:500])
                self.measured_skoZaD = np.std(self.measured_spectrZaD[PIX_WORK_INTERVAL])
                self.all_measured_data["spectr"] = np.array(spectr).tolist()
            elif self.chan[0] == 'D':
                # Если 'СКО D измеренное' < 100 И 'СКО Z-aD' > 100"""
                measured_sko = self.all_measured_data["calculated"]["sko"]
                pars_sko_d = PARS["calibration"]["sko_D"]
                pars_sko_zad = PARS["calibration"]["sko_ZaD"]
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
            text = "analyze_spectr: {} Line: {}".format(str(err), sys.exc_info()[-1].tb_lineno)
            print(text)
            LOGGER.error(text)

    @staticmethod
    def pix2nm(pix):
        nm = 0
        deg = len(PARS["calibration"]["nm(pix)"]["Z"]) - 1
        for i in PARS["calibration"]["nm(pix)"]["Z"]:
            nm += eval(i) * pix ** deg
            deg -= 1
        return nm

    def nm2pix(self, nm):
        pix = 0
        while self.pix2nm(pix) < nm:
            pix += 1
        return pix

    def add_calculated_line_to_final_file(self, spectr, mu, expo, sensitivityS,
                                          sensitivity_eritem, print_o3_to_console):
        calco = CalculateOnly()
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
            dirs_sending = DEVICE_DIR_L + ['Sending']
            self.path, self.measure_count = make_dirs(measure_day_dir(self.time_now_local),
                                                      reset_counter=True)
            self.path_sending = make_dirs(dirs_sending)

            self.name = 'm{}_{}_{}_{}.txt'.format(DEVICE_ID,
                                                  str(self.measure_count).zfill(3),
                                                  self.chan,
                                                  self.time_now_local.strftime('%Y%m%d%H%M'))

            with open(os.path.join(self.path, self.name), 'w') as f:
                json.dump(self.all_measured_data, f, ensure_ascii=False,
                          indent='', sort_keys=True)
                print('>>> {}'.format(self.name))
                LOGGER.info('>>> {}'.format(self.name))
            if self.chan in ['ZD', 'SD']:
                self.file2send[self.chan] = self.name
                self.add_calculated_line_to_final_file(self.all_measured_data['spectr'],
                                                       self.all_measured_data['calculated']['mu'],
                                                       self.all_measured_data['mesurement']['exposition'],
                                                       self.sensitivityS,
                                                       self.sensitivity_eritem,
                                                       True)
                path_file = write_final_file(self.chan,
                                             self.all_measured_data["mesurement"]["datetime"],
                                             round(self.all_measured_data["calculated"]["sunheight"], 1),
                                             self.calc_result[self.chan],
                                             '',
                                             False)

                if self.chan == 'ZD':
                    write_analyse_file(self.chan,
                                       self.all_measured_data["mesurement"]["datetime"],
                                       round(self.all_measured_data["calculated"]["sunheight"], 1),
                                       self.calc_result[self.chan],
                                       'Analyse_',
                                       False)
                    self.last_file_o3 = path_file
                elif self.chan == 'SD':
                    self.last_file_uv = path_file
        except Exception as err:
            print('write_file (spectr): ', end='')
            print(err, sys.exc_info()[-1].tb_lineno)
            LOGGER.error(str(err))

    def change_channel(self, chan):
        # print("Changing channel to {}... ".format(chan))
        LOGGER.debug('Переключение на канал {}.'.format(
            PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8')))
        data, t1, t2, text, self.tries_done = UfosDataToCom(
            50, PARS['device']['accummulate'], chan, 'N').device_ask()
        # print("Channel changed to {} (try: {})".format(chan, self.tries_done))

    def write_file4send(self, chan, data4send):
        with open(os.path.join(self.path_sending, self.file2send[chan]), 'w') as f:
            f.write(data4send)

    def make_line(self):
        try:
            debug = 0
            encode = 0
            if debug:
                with open('test.txt', 'w') as f:
                    print(self.mesure_data, file=f)  # mesurement
                    print('==========================================', file=f)
                    print(PARS, file=f)  # Settings
                    print('==========================================', file=f)
                    print(CONNECT_PARS, file=f)  # connect Settings
                    print('==========================================', file=f)
                    print(self.calc_result, file=f)  # o3 + uv
            if encode:
                points2send = base64.b64encode(str(PARS['calibration']['points']).encode('ascii')).decode('ascii')
                pars2send = base64.b64encode(str(PARS).encode('ascii')).decode('ascii')
            else:
                points2send = str(PARS['calibration']['points']).replace("'", '"')
                pars2send = str(PARS).replace("'", '"')
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
{21};{22};{23};{24};{25};{26};{27};{28};{29};{30};{31}#""".format(self.mesure_data[chan]['id']['device'],
                                                                  self.mesure_data[chan]['id']['station'],
                                                                  self.mesure_data[chan]['mesurement']['channel'][
                                                                                                  0] + '-' +
                                                                  self.mesure_data[chan]['mesurement']['channel'][1],
                                                                  self.mesure_data[chan]['mesurement']['datetime'],
                                                                  self.mesure_data[chan]['mesurement']['exposition'],
                                                                  'NULL',  # gain = 0
                                                                  self.mesure_data[chan]['mesurement'][
                                                                                                  'temperature_ccd'],
                                                                  o3,  # mesure
                                                                  uva,  # mesure
                                                                  uvb,  # mesure
                                                                  uve,  # mesure
                                                                  self.mesure_data[chan]['spectr'],
                                                                  correct,  # gain = 0
                                                                  # ==== Additional parameters ====
                                                                  self.mesure_data[chan]['mesurement'][
                                                                                                  'datetime_local'],
                                                                  self.mesure_data[chan]['mesurement']['timezone'],
                                                                  PARS['station']['sun_height_min'],
                                                                  self.mesure_data[chan]['mesurement']['accummulate'],
                                                                  'NULL',  # set_run
                                                                  self.mesure_data[chan]['id']['device'],  # dev_id1
                                                                  PARS['station']['interval'],
                                                                  PARS['device']['auto_exposition'],  # repeat1
                                                                  PARS['device']['amplitude_max'],
                                                                  self.mesure_data[chan]['mesurement']['latitude'],
                                                                  self.mesure_data[chan]['mesurement']['longitude'],
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
                self.write_file4send(chan, data4send)

        except Exception as err:
            print(err, sys.exc_info()[-1].tb_lineno)

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
    def sock_send(host, port, data2send):
        t = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for ip in host.split(','):
            try:
                sock.connect((ip, port))
                sock.send(data2send.encode(encoding='utf-8'))
                sock.close()
                t.append('OK')
            except:
                t.append('ERR')
                continue
        if 'OK' in t:
            return 'OK'
        else:
            print('No connection to server')
            return 'ERR'

    def send_file(self, file2send):
        tex = {}
        try:
            for send_type in ['socket', 'ftp']:
                if CONNECT_PARS[send_type + '_ip'] != '0':
                    tex[send_type] = ''
                    if send_type == 'socket':
                        with open(file2send) as f:
                            data2send = ''.join(f.readlines())
                            tex[send_type] = self.sock_send(CONNECT_PARS['socket_ip'],
                                                            int(CONNECT_PARS['socket_port']),
                                                            data2send)
                    elif send_type == 'ftp':
                        tex[send_type] = self.ftp_send(CONNECT_PARS['ftp_ip'],
                                                       int(CONNECT_PARS['ftp_port']),
                                                       CONNECT_PARS['ftp_path'],
                                                       CONNECT_PARS['ftp_user'],
                                                       CONNECT_PARS['ftp_pass'],
                                                       file2send)
                    if tex[send_type] == 'OK':
                        print('{} Отправлен {} (dev: {})'.format(file2send, send_type,
                                                                 self.all_measured_data['id']['device']))
                    else:
                        print(tex[send_type])

        except Exception as err:
            print('procedures.send_file(): {} - line {}'.format(err, sys.exc_info()[2].tb_lineno))
        finally:
            return tex

    def measure(self):
        """Определение номера последнего измерения"""
        try:
            files = os.listdir(self.path)
            if files:
                self.measure_count = max(set([int(i.split('_')[1]) for i in files if i.count('_') == 3]))
            else:
                self.measure_count = 1
        except:
            pass
        try:
            k = {'Z': 0, 'S': 0}
            if PARS['device']['auto_exposition'] == 1:
                self.measure_count += 1
                """ Z or S mesurement """
                for chan in PARS['device']['channel']:
                    self.expo = PARS['device']['auto_expo_min']
                    self.ZS_spectr = [0] * 3691
                    self.change_channel(chan)
                    while self.expo < PARS['device']['auto_expo_max'] \
                        and max(self.ZS_spectr[PIX_WORK_INTERVAL]) < PARS['device']['amplitude_max']:
                        try:
                            text = 'Канал {}. Эксп = {}'.format(
                                PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                                self.expo)
                            print(text, end='')
                            self.ZS_spectr, self.t1, self.t2, text2, self.tries_done = UfosDataToCom(
                                self.expo, PARS['device']['accummulate'], chan, 'S').device_ask()
                            text += ' ' + text2
                            print('\r{}'.format(text))
                            LOGGER.info(text)
                            if max(self.ZS_spectr[PIX_WORK_INTERVAL]) > PARS['device']['amplitude_min']:
                                break
                            k[chan] = max(self.ZS_spectr[PIX_WORK_INTERVAL]) / PARS['device']['amplitude_max']
                            if k[chan] != 0:
                                self.expo = int(self.expo / k[chan])

                        except Exception as err:
                            print('mesure:', end='')
                            print(err, sys.exc_info()[-1].tb_lineno)
                            LOGGER.error(str(err))
                            break

                    else:
                        self.expo = PARS['device']['auto_expo_max']
                        text = 'Канал {}. Эксп = {}'.format(
                            PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text)
                        self.ZS_spectr, self.t1, self.t2, text2, self.tries_done = UfosDataToCom(
                            self.expo, PARS['device']['accummulate'], chan, 'S').device_ask()
                        text += ' ' + text2
                        print('\r{}'.format(text), end=' ')
                        LOGGER.info(text)
                    self.chan = chan
                    self.analyze_spectr(self.ZS_spectr)
                    self.write_file()

                    """ D mesurement """
                    self.chan = 'D' + chan.lower()
                    self.change_channel('D')
                    text = 'Канал {}. Эксп = {}'.format(
                        PARS['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),
                        self.expo)
                    print(text)
                    self.Dspectr, self.t1, self.t2, text2, self.tries_done = UfosDataToCom(
                        self.expo, PARS['device']['accummulate'], 'D', 'S').device_ask()
                    text += ' ' + text2
                    print('\r{}'.format(text), end=' ')
                    LOGGER.info(text)
                    self.analyze_spectr(self.Dspectr)
                    self.write_file()

                    """ Z-D or S-D calculation """
                    self.chan = chan + 'D'
                    text = 'Расчёт спектра {}.'.format(self.chan)
                    print(text, end=' ')
                    LOGGER.info(text)
                    self.ZDspectr = np.array(self.ZS_spectr) - np.array(self.Dspectr)
                    self.analyze_spectr(self.ZDspectr)
                    self.write_file()
                    self.mesure_data[self.chan] = self.all_measured_data

            else:
                for expo in PARS['device']['manual_expo']:
                    self.expo = expo
                    self.measure_count += 1
                    for chan in PARS['device']['channel']:
                        """ Z or S mesurement """
                        self.change_channel(chan)
                        text = 'Канал {}. Эксп = {}'.format(
                            PARS['channel_names'][chan].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text)
                        self.ZS_spectr, self.t1, self.t2, text2, self.tries_done = UfosDataToCom(
                            self.expo, PARS['device']['accummulate'], chan, 'S').device_ask()
                        text += ' ' + text2
                        print('\r{}'.format(text), end=' ')
                        LOGGER.info(text)
                        self.chan = chan
                        self.analyze_spectr(self.ZS_spectr)
                        self.write_file()

                        """ D mesurement """
                        self.chan = 'D' + chan.lower()
                        self.change_channel('D')
                        text = 'Канал {}. Эксп = {}'.format(
                            PARS['channel_names']['D'].encode(encoding='cp1251').decode(encoding='utf-8'),
                            self.expo)
                        print(text)
                        self.Dspectr, self.t1, self.t2, text2, self.tries_done = UfosDataToCom(
                            self.expo, PARS['device']['accummulate'], 'D', 'S').device_ask()
                        text += ' ' + text2
                        print('\r{}'.format(text), end=' ')
                        LOGGER.info(text)
                        self.analyze_spectr(self.Dspectr)
                        self.write_file()

                        """ Z-D or S-D calculation """
                        self.chan = chan + 'D'
                        text = 'Расчёт спектра {}.'.format(self.chan)
                        print(text, end=' ')
                        LOGGER.info(text)
                        self.ZDspectr = np.array(self.ZS_spectr) - np.array(self.Dspectr)
                        self.analyze_spectr(self.ZDspectr)
                        self.write_file()
                        self.mesure_data[self.chan] = self.all_measured_data
        except TypeError:
            #            print("No data from UFOS")
            pass
        except Exception as err:
            print("procedures.Main.mesure:", end='')
            print(err, sys.exc_info()[-1].tb_lineno)


class CheckSunAndMesure:
    def __init__(self):
        self.home = os.getcwd()
        self.end_calculation = True
        self.time_now_utc = datetime.now()
        self.time_now_local = datetime.now()
        self.mu, self.amas, self.sunheight = 0, 0, 0
        self.timezone = timedelta(hours=int(PARS["station"]['timezone']))

    def start(self):
        while 1:
            try:
                UfosConnection().get_com()
                self.time_now_utc = datetime.now()
                self.time_now_local = self.time_now_utc + self.timezone
                self.mu, self.amas, self.sunheight = sunheight(PARS["station"]["latitude"],
                                                               PARS["station"]["longitude"],
                                                               self.time_now_utc,
                                                               PARS["station"]["timezone"])
                main = MeasureClass()
                if self.sunheight >= PARS["station"]["sun_height_min"]:
                    self.end_calculation = True
                    # Высота Солнца выше заданного параметра
                    print('=== Запуск измерения ===                      ', end='\r')
                    main.measure()

                    if main.tries_done > 0:
                        print('Кабель подключен к ПК, но не подключен к УФОС!', end='\r')
                        sleep(10)
                    else:
                        calculate_final_files(main.last_file_o3, 'ZD', True, "file")
                        main.make_line()
                        print('========================')
                        next_time = self.time_now_local + timedelta(minutes=PARS["station"]["interval"])
                        self.mu, self.amas, self.sunheight = sunheight(PARS["station"]["latitude"],
                                                                       PARS["station"]["longitude"],
                                                                       next_time,
                                                                       PARS["station"]["timezone"])

                        print('Следующее измерение: {}'.format(str(next_time).split('.')[0]))

                        # Send files
                        send_ok = True
                        for file2send in os.listdir(main.path_sending):
                            if datetime.now() + self.timezone < next_time and send_ok:
                                sending_file = os.path.join(main.path_sending, file2send)
                                tex = main.send_file(sending_file)
                                LOGGER.debug(str(tex))
                                for status in tex.keys():
                                    if tex[status] == 'OK':
                                        os.remove(sending_file)
                                    else:
                                        send_ok = False
                            else:
                                break
                        while datetime.now() + self.timezone < next_time:
                            sleep(1)
                else:
                    # Высота Солнца менее заданного параметра
                    if self.end_calculation:
                        calculate_final_files(main.last_file_o3, 'ZD', True, "file")
                        self.end_calculation = False
                    print('\rСледующее измерение: {}'.format(
                        get_time_next_start(PARS["station"]["latitude"],
                                            PARS["station"]["longitude"],
                                            PARS["station"]["timezone"],
                                            PARS["station"]["sun_height_min"])), end='')
                    sleep(5)
            except serial.serialutil.SerialException as err:
                print(err)
            except TypeError as err:
                print(err, sys.exc_info()[-1].tb_lineno)
                sleep(10)
            except ValueError as err:
                if "COM" in str(err):
                    raise err
            except Exception as err:
                print(err, sys.exc_info()[-1].tb_lineno)
                sleep(10)
