# Version: 2.0
# Modified: 12.07.2019
# Author: Sergey Talash


from lib.calculations import *
from lib.measure import *
from datetime import datetime
from lib.core import *

if __name__ == '__main__':
    mu, amas, hs = sunheight(PARS['station']['latitude'],
                             PARS['station']['longitude'],
                             datetime.now(),
                             int(PARS['station']['timezone']))
    print('Station: {}, (lat: {}, long: {})\nmu: {}\namas: {}\nsunheight: {}\n================'.format(
        PARS['station']['id'], PARS['station']['latitude'], PARS['station']['longitude'], mu, amas, hs))
    version = '2.0'
    CheckSunAndMesure().start()
