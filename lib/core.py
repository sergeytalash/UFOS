# Version: 2.0
# Modified: 11.05.2025
# Author: Sergey Talash

import inspect
import json
import logging
import logging.handlers as handlers
import os
import string
import sys
from datetime import datetime


def print_error(err):
    print(inspect.currentframe().f_code.co_name)
    text = "(measure) Error: {}, Line: {}".format(err, sys.exc_info()[-1].tb_lineno)
    print(text)
    LOGGER.error(text)


def measure_year_dir(dt, dir_type, deep=False):
    """
    Args:
        dt (datetime):
        dir_type (str): Mesurements | Ozone | UV
        deep (bool, optional):
            If true, method is used to get the list of dirs
            else returns os.path string
    Returns:
        list | str
    """
    dirs_list = DEVICE_DIR_L + [dir_type, dt.strftime('%Y')]
    if deep:
        return dirs_list
    else:
        return os.path.join(*dirs_list)


def measure_month_dir(dt, dir_type, deep=False):
    """
    Args:
        dt (datetime):
        dir_type (str): Mesurements | Ozone | UV
        deep (bool, optional):
            If true, method is used to get the list of dirs
            else returns os.path string
    Returns:
        list | str
    """
    dirs_list = measure_year_dir(dt, dir_type, True) + [dt.strftime('%Y-%m')]
    return dirs_list
    # if deep:
    #     return dirs_list
    # else:
    #     return os.path.join(*dirs_list)


def measure_day_dir(dt, dir_type='Mesurements', deep=False):
    """
    Args:
        dt (datetime):
        dir_type (str): Mesurements | Ozone | UV
        deep (bool, optional):
            If true, method is used to get the list of dirs
            else returns os.path string
    Returns:
        list | str
    """
    dirs_list = measure_month_dir(dt, dir_type, True) + [dt.strftime('%Y-%m-%d')]
    if deep:
        return dirs_list
    else:
        return os.path.join(*dirs_list)


def get_device_id():
    """
    Get device id from common_settings.json file
    Returns:
        Int
    """
    with open(os.path.join(HOME, DEVICE_ID_FILE), 'r') as f:
        return json.load(f)['device']['id']


def get_settings():
    """
    Load settings for current device
    Returns:
        Dict
    """
    with open(os.path.join(HOME, DEVICE_SETTINGS_PATH)) as f:
        return json.load(f)


def get_default_settings():
    """
    Loads default settings
    Returns:
        Dict
    """
    with open(os.path.join(HOME, 'defaults', 'settings.json'), 'r') as f:
        return json.load(f)


def update_settings(pars):
    """
    Args:
        pars (dict): New settings

    Returns:
        None
    """
    with open(os.path.join(HOME, DEVICE_SETTINGS_PATH), 'w') as f:
        json.dump(pars, f, ensure_ascii=False, indent='  ', sort_keys=True)


def read_connect():
    with open(os.path.join(HOME, 'connect.ini')) as f:
        connection_settings = {}
        for i in f.readlines():
            if i[0] not in ['\n', ' ', '#'] and not i.startswith('п»ї#'):
                line = i.replace(' ', '').replace('\n', '').split('=')
                connection_settings[line[0]] = line[1]
        return connection_settings


def read_sensitivity(mode):
    """
    Loads sensitivity file
    Args:
        mode (str): Z - zenith | S - summ | E - erithema

    Returns:
        [float]
    """
    if mode == "Z":
        _path = SENSITIVITY_Z_PATH
    elif mode == "E":
        _path = SENSITIVITY_ERITEMA_PATH
    else:
        _path = SENSITIVITY_S_PATH
    with open(_path) as f:
        sens = f.readlines()
        out = [float(i.strip()) for i in sens if i.strip()]
        if len(out) == 3691:
            return out
        else:
            print("{}\nCheck file. There are {} lines instead of 3691".format(_path, len(out)))
            return [1] * 3691


def read_nomographs(o3_num, use_sensitivity_z):
    if o3_num == "1":
        if use_sensitivity_z:
            filename = NOMOGRAPH_NORM_1_PATH
        else:
            filename = NOMOGRAPH_1_PATH
    else:
        if use_sensitivity_z:
            filename = NOMOGRAPH_NORM_2_PATH
        else:
            filename = NOMOGRAPH_2_PATH
    ozone_list = []
    r12_list = []
    mu_effective_list = []
    if os.path.exists(filename):
        with open(filename, 'r') as fr:
            ozone_number = 0
            # mueff_number = 0
            # mueff_step = 0.05
            # TODO: Refactor nomograph file for better operations
            while True:
                line = fr.readline()
                if line.find('MuEff\t\t\t') != -1:
                    continue
                'количество линий озона'
                if line.find('Ozone\tnumber\t\t\t') != -1:
                    ozone_number = int(line.split('\t')[0])
                    continue
                if line.find('Mueff\tnumber\t\t\t') != -1:
                    mueff_number = int(line.split('\t')[0])
                    continue
                if line.find('Mueff\tstep\t\t\t') != -1:
                    mueff_step = float(line.split('\t')[0])
                    continue
                'массив со значениями озона'
                if line.find('\tOzon\tnumber\n') != -1:
                    ozone_list_str = line.split('\t')[:ozone_number]
                    ozone_list_int = [int(ozone) for ozone in ozone_list_str]
                    ozone_list.extend(list(reversed(ozone_list_int)))
                    continue
                'Текст закончился - выход'
                if line == '' or line == '\n':
                    break
                else:
                    r12_list_str = line.split('\t')[:ozone_number]
                    # print(">>>",  r12_list_str, ">>>", ozone_number)
                    r12_list_float = [float(r12) for r12 in r12_list_str]
                    # r12_list_float_reversed = list(reversed(r12_list_float))
                    r12_list.append(list(reversed(r12_list_float)))
                    mu_effective = line.split('\t')[ozone_number:ozone_number + 1:1][0]
                    mu_effective_list.append(float(mu_effective))
            return mu_effective_list, r12_list, ozone_list
    else:
        human_text = "File {} does not exist. Ozone is not calculated.".format(filename)
        print(human_text)
        # show_error_in_separate_window("", human_text)
        return [], [], []


def last_used_path(home, path, mode):
    """Чтение файла last_path"""
    last_path = os.path.join(home, 'last_path.txt')
    if mode == 'r' and os.path.exists(last_path):
        with open(last_path, 'r') as fr:
            out = fr.readline()
        return out.strip()
    else:
        with open(last_path, 'w') as fw:
            fw.write(path)
        return path.strip()


def make_dirs(dirs, reset_counter=False):
    path = HOME
    out = False
    # dirs = ['1','2','2'] > home\1\2\3
    for i in dirs:
        path = os.path.join(path, str(i))
        if not os.path.exists(path):
            os.mkdir(path)
            if reset_counter:
                out = True
    if out:
        return path, 1
    else:
        return path, None


def make_list():
    if not WINDOWS_OS:
        disks = '/'
    else:
        alp = string.ascii_uppercase
        disks = []
        for i in alp:
            try:
                os.chdir(i + ':\\')
                disks.append(os.getcwd()[:1])
            except OSError:
                pass
    return tuple(disks)


def get_home():
    current = os.getcwd()
    path_list = current.split(SEP)
    if "UFOS" in path_list:
        i = path_list.index("UFOS")
        current = SEP.join(path_list[:i + 1])
    for d in [".", "UFOS", "..", f"..{SEP}.."]:
        path = os.path.join(current, d)
        if DEVICE_ID_FILE in os.listdir(path):
            return os.path.normpath(path)
    else:
        raise OSError("Can't find UFOS root directory.")


# class Profiler(object):
#     def __enter__(self):
#         self._startTime = time.time()
#         logger.debug('Timer started.')
#
#     def __exit__(self, type, value, traceback):
#         logger.debug("Timer stopped. Elapsed time: {:.3f} seconds".format(time.time() - self._startTime))
if os.name == 'posix':
    WINDOWS_OS = False
    SEP = '/'
else:
    WINDOWS_OS = True
    SEP = '\\'

DEVICE_ID_FILE = 'common_settings.json'
# os.chdir("../UFOS")
HOME = get_home()
PATH = HOME
LAST_DIR = []
DEVICE_ID = get_device_id()
SETTINGS_DIR = os.path.join(HOME, 'Ufos_{}'.format(DEVICE_ID), 'Settings')
DEVICE_SETTINGS_PATH = os.path.join(SETTINGS_DIR, 'settings.json')
SENSITIVITY_Z_PATH = os.path.join(SETTINGS_DIR, 'sensitivityZ{}.txt'.format(DEVICE_ID))
SENSITIVITY_S_PATH = os.path.join(SETTINGS_DIR, 'sensitivityS{}.txt'.format(DEVICE_ID))
SENSITIVITY_ERITEMA_PATH = os.path.join(SETTINGS_DIR, 'senseritem{}.txt'.format(DEVICE_ID))
NOMOGRAPH_1_PATH = os.path.join(SETTINGS_DIR, 'nomograph{}_1.txt'.format(DEVICE_ID))
NOMOGRAPH_2_PATH = os.path.join(SETTINGS_DIR, 'nomograph{}_2.txt'.format(DEVICE_ID))
NOMOGRAPH_NORM_1_PATH = os.path.join(SETTINGS_DIR, 'nomograph_norm{}_1.txt'.format(DEVICE_ID))
NOMOGRAPH_NORM_2_PATH = os.path.join(SETTINGS_DIR, 'nomograph_norm{}_2.txt'.format(DEVICE_ID))

PARS = get_settings()
CONNECT_PARS = read_connect()

DEVICE_DIR_L = [HOME, 'Ufos_{}'.format(DEVICE_ID)]
MEASUREMENTS_DIR_L = DEVICE_DIR_L + ['Mesurements']
OZONE_DIR_L = DEVICE_DIR_L + ['Ozone']
UV_DIR_L = DEVICE_DIR_L + ['UV']

LOGS_DIR = os.path.join(HOME, 'logs')
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

LOGGER = logging.getLogger("Rotating Log")
LOGGER.setLevel(logging.INFO)
handler = handlers.RotatingFileHandler(
    os.path.join(LOGS_DIR, 'ufos_{}.log'.format(DEVICE_ID)),
    maxBytes=1 * 1024 * 1024,
    backupCount=10)
LOGGER.addHandler(handler)

PIX_WORK_INTERVAL = slice(*PARS["device"]["pix_work_interval"])
