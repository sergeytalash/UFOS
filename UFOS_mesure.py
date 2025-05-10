# Version: 2.0
# Modified: 13.08.2021
# Author: Sergey Talash

try:
    from lib import calculations as calc, measure, core
except ModuleNotFoundError as err:
    import calculations as calc, measure, core

from datetime import datetime

if __name__ == '__main__':
    mu, amas, hs = calc.sunheight(core.PARS['station']['latitude'],
                                  core.PARS['station']['longitude'],
                                  datetime.now(),
                                  int(core.PARS['station']['timezone']))
    print('UFOS: {}\nStation: {}, (lat: {}, long: {})\nmu: {}\namas: {}\nsunheight: {}\n================'.format(
        core.DEVICE_ID,
        core.PARS['station']['id'],
        core.PARS['station']['latitude'],
        core.PARS['station']['longitude'], mu, amas, hs))
    measure.CheckSunAndMeasure().start()
