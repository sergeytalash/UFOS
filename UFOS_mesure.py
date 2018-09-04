# Version: 2.0
# Modified: 15.01.2018
# Author: Sergey Talash
import serial
import time
import datetime
import winreg
import os
import winsound
import sys
import json
import numpy as np
import logging
from math import *

import procedures 


if __name__ == '__main__':
    date_time = datetime.datetime.now()
    logging.basicConfig(filename='logs/ufos.log',level=logging.INFO)
##    mu,amas,hs = procedures.sunheight(59.57,-30.42,date_time,+0)
##    print('mu= {}\namas= {}\nsunheight= {}\n================'.format(mu,amas,hs))
    version = '2.0'
    procedures.check_sun_and_mesure().start()

    





