import datetime
import json
import os
from os.path import split as p_split
from sys import path as sys_path

import numpy as np

settings_home = p_split(p_split(os.getcwd())[0])[0]
sys_path.insert(0, settings_home)
import procedures
from procedures import Settings


class WaitItem:
    def __init__(self):
        self.vars = r"-\|/"
        self.i = 0

    def get_next(self):
        if self.i > 3:
            self.i = 0
        out = self.vars[self.i]
        self.i += 1
        return "\r{}".format(out)

    def print(self):
        print(self.get_next(), end='')


def convert_file(directory, file, new_data_example, pars):
    global mesure_count
    global current_channels
    with open(os.path.join(directory, file)) as f:
        new_data = new_data_example.copy()
        data = f.readlines()
        spectr = []
        count_pars = 0
        for line in data:
            if 'Measurement' in line:
                l = line.split(',')
                channel = l[0].split(' = ')[-1]
                new_data["mesurement"]["channel"] = change_channel(channel, file, files)
                if new_data["mesurement"]["channel"] in ['ZD', 'SD']:
                    new_data["mesurement"]["status"] = 0
                else:
                    if "status" in new_data["mesurement"].keys():
                        new_data["mesurement"].__delitem__("status")
                if new_data["mesurement"]["channel"] in current_channels and new_data["mesurement"]["channel"] == 'Z':
                    mesure_count += 1
                    current_channels = set()
                current_channels.add(new_data["mesurement"]["channel"])
                date_time = datetime.datetime.strptime(
                    l[1].split(' = ')[-1].replace('.', '') + ' ' + l[2].split(' = ')[-1][:-1], '%d%m%Y %H:%M:%S')
                date_time_local = date_time + datetime.timedelta(hours=int(pars["station"]["timezone"]))
                new_data["mesurement"]["datetime"] = datetime.datetime.strftime(date_time, '%Y%m%d %H:%M:%S')
                new_data["mesurement"]["datetime_local"] = datetime.datetime.strftime(date_time_local,
                                                                                      '%Y%m%d %H:%M:%S')
                count_pars += 1
            elif 'Exposure' in line:
                new_data["mesurement"]["exposition"] = int(line.split('=')[-1])
                count_pars += 1
            elif 'Temperature' in line:
                new_data["mesurement"]["temperature_ccd"] = 255
                new_data["mesurement"]["temperature_poly"] = float(line.split('=')[-1])
                count_pars += 1
            elif 'Accummulate' in line:
                new_data["mesurement"]["accummulate"] = int(line.split('=')[-1])
                count_pars += 1
            elif ' mu' in line:
                new_data["calculated"]["mu"] = round(float(line.split()[0]), 4)
                count_pars += 1
            elif ' hs' in line:
                new_data["calculated"]["sunheight"] = round(float(line.split()[0]), 4)
                count_pars += 1
            elif ' amas' in line:
                new_data["calculated"]["amas"] = round(float(line.split()[0]), 4)
                count_pars += 1
            elif '[Value]' in line:
                for i in data[data.index('[Value]\n') + 1:]:
                    try:
                        spectr.append(int(i))
                    except:
                        pass
                new_data["spectr"] = spectr

                if len(spectr) != 3691:
                    print('{} wrong len ({})'.format(file, len(spectr)))
                else:
                    count_pars += 1
                    text = {
                        "id": {
                            "device": pars["device"]["id"],
                            "station": pars["station"]["id"]
                            },
                        "mesurement": {
                            "timezone": pars["station"]["timezone"],
                            "latitude": pars["station"]["latitude"],
                            "longitude": pars["station"]["longitude"]
                            },
                        "calculated": {
                            "sko": round(float(np.std(spectr[300:3600])), 4),
                            "mean": round(float(np.mean(spectr[300:3600])), 4),
                            "dispersia": round(float(np.var(spectr[300:3600])), 4)
                            }
                        }
                    for key in text.keys():
                        new_data[key].update(text[key])
                    count_pars += 8
                break
        p.print()
        _next = ''
        if count_pars != 16:
            print('count_pars != 16 (= {})'.format(count_pars))
            _next = input('Continue? [n]: ')
        if _next:
            raise
        year = new_data["mesurement"]["datetime"].split()[0][:4]
        month = new_data["mesurement"]["datetime"].split()[0][4:6]
        day = new_data["mesurement"]["datetime"].split()[0][6:]
        dirs = ['Ufos_{}'.format(pars["device"]["id"]),
                'Mesurements',
                year,
                year + '-' + month,
                year + '-' + month + '-' + day]
        datetime_name = new_data["mesurement"]["datetime"][:-2].replace(':', '').replace(' ', '')
        new_file = name = 'm{}_{}_{}_{}.txt'.format(pars['device']['id'],
                                                    str(mesure_count).zfill(3),
                                                    new_data["mesurement"]["channel"],
                                                    datetime_name
                                                    )
        path = home
        for i in dirs:
            path = os.path.join(path, str(i))
            if not os.path.exists(path):
                os.mkdir(path)

        with open(os.path.join(path, new_file), 'w') as f:
            json.dump(new_data, f, ensure_ascii=False, indent='', sort_keys=True)


def change_channel(_in, file, files):
    out = {'Z': 'Z',
           'S': 'S',
           'Z-D': 'ZD',
           'S-D': 'SD',
           'D': 'D' + files[files.index(file) - 1].split('_')[0].split('.')[-1].lower()}
    return out[_in]


if __name__ == "__main__":
    p = WaitItem()
    home = p_split(p_split(os.getcwd())[0])[0]
    pars = Settings.get_device(home, Settings.get_common(home).get('device').get('id'))
    new_data_example = {
        "calculated": {
            "amas": 0,
            "dispersia": 0,
            "mean": 0,
            "mu": 0,
            "sko": 0,
            "sunheight": 0
            },
        "id": {
            "device": 0,
            "station": ""
            },
        "mesurement": {
            "accummulate": 0,
            "channel": "",
            "datetime": "",
            "datetime_local": "",
            "exposition": 0,
            "latitude": 0,
            "longitude": 0,
            "timezone": "+0",
            "temperature_poly": 0,
            "temperature_ccd": 0
            },
        "spectr": []
        }

    ch = input('Обработать даты, заданные в файле Calibration_dates.txt [1] или ВСЕ даты [2]? [1,2] ')
    if ch == '1':
        with open(os.path.join("Calibration_files", "Calibration_dates.txt")) as f:
            dates = f.readlines()
        date_find = []
        for i in dates:
            date_find.append(i.split()[0])
        for date in date_find:
            d = date.split('.')
            directory = os.path.join(*((home, "ZEN") + tuple(d)))
            print("\n" + directory)
            if os.path.isdir(directory):
                mesure_count = 1
                current_channels = set()
                files = sorted(os.listdir(directory))
                for file in files:
                    if '.txt' in file and 'm' == file[0] and '_' in file:
                        convert_file(directory, file, new_data_example, pars)

    # ====================================================================
    if ch == '2':
        for directory, a, files in os.walk(os.path.join(home, 'ZEN')):
            if directory.count('ZEN') > 0:
                d1 = directory.split('ZEN')
                current_date = d1[-1].replace(procedures.p_sep, '.')[1:]  # 2015.03.19
                if len(current_date) == 10:
                    print("\n{}".format(directory))
                    mesure_count = 1
                    current_channels = set()
                    for file in files:
                        if '.txt' in file and 'm' in file and '_' in file:
                            convert_file(directory, file, new_data_example, pars)

    print('\nDone.')
