# Version: 2.0
# Modified: 11.05.2025
# Author: Sergey Talash

from lib import calculations as calc
from lib import core
from lib import measure

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
