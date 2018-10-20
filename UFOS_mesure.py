# Version: 2.0
# Modified: 15.01.2018
# Author: Sergey Talash
# import serial
# import time
import os
import datetime
# import winreg
# import os
# import winsound
# import sys
# import json
# import numpy as np
import logging
import logging.handlers as handlers
# from math import *

import procedures 


if __name__ == '__main__':
    date_time = datetime.datetime.now()
    if not os.path.exists('logs'):
        os.mkdir('logs')
    common_pars = procedures.Settings.get(os.getcwd())
    settings = procedures.Settings.get_device(os.getcwd(), common_pars['device']['id'])
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)
    handler = handlers.RotatingFileHandler('logs\\ufos_{}.log'.format(settings['device']['id']), maxBytes=10*1024*1024, backupCount=10)
    logger.addHandler(handler)
    mu, amas, hs = procedures.sunheight(settings['station']['latitude'], settings['station']['longitude'], date_time, int(settings['station']['timezone']))
    print('Station: {}, (lat: {}, long: {})\nmu: {}\namas: {}\nsunheight: {}\n================'.format(settings['station']['id'], settings['station']['latitude'], settings['station']['longitude'], mu, amas, hs))
    version = '2.0'
    procedures.check_sun_and_mesure(logger).start()

    





