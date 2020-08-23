# Version: 2.0
# Modified: 12.07.2019
# Author: Sergey Talash


from lib import calculations as calc
from lib import measure
from datetime import datetime as d_t
from lib import core

if __name__ == '__main__':
    mu, amas, hs = calc.sunheight(core.PARS['station']['latitude'],
                             core.PARS['station']['longitude'],
                             d_t.now(),
                             int(core.PARS['station']['timezone']))
    print('Station: {}, (lat: {}, long: {})\nmu: {}\namas: {}\nsunheight: {}\n================'.format(
        core.PARS['station']['id'],
        core.PARS['station']['latitude'],
        core.PARS['station']['longitude'], mu, amas, hs))
    version = '2.0'
    measure.CheckSunAndMesure().start()
