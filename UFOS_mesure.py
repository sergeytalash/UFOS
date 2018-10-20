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
# from math import *

import procedures 


if __name__ == '__main__':
    date_time = datetime.datetime.now()
    if not os.path.exists('logs'):
        os.mkdir('logs')
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)
    handler = logging.RotatingFileHandler('logs/ufos.log', maxBytes=10*1024*1024, backupCount=10)
    logger.addHandler(handler)
##    mu,amas,hs = procedures.sunheight(71.35,-128.54,date_time,+9)
##    print('mu= {}\namas= {}\nsunheight= {} (Данные не из settings.py)\n================'.format(mu,amas,hs))
    version = '2.0'
    procedures.check_sun_and_mesure().start()

    





