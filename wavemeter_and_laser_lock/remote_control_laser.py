#new wavemeter server 2020
''' 
Created on 2020

@author: B.J.Hensen

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Code to remotely control the laser_lock.


'''

import time
from datetime import datetime
import numpy as np
import Pyro4

'''
example of usage of remote control of the laser, this code can be run in other consoles or machine connected to the local network
'''

#use the IP of the machine were the laser_lock_5_0 is running, or localhost 
ctl2_lock = Pyro4.Proxy('PYRONAME:laser_lock_CTL2@192.168.1.XXX')

ctl2_wavelength =  #float, in nm
ctl2_detuning = #float, in GHz
ctl2_lock.set_wavelength_setpoint(ctl2_wavelength)
ctl2_lock.set_detuning(np.round(ctl2_detuning,4))
ctl2_lock.remote_start()