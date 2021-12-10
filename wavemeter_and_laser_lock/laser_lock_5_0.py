''' 
Created on 

@author: A.Wallucks

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Code to run a laser lock server that allows to lock single lasers using the reading from a external wavemeter (accessed via the wlm_server_2_3).
The laser can be controlled remotely via the laser_lock server on other consoles or machines, and via the GUI.
To lock multiple lasers in 'parallel' just run the script multiple times in separate consoles (the reading from the wavementer will be in series, so the lock of multiple lasers will be toggling between them in series continuosly).

In this code 1 example class for a TOPTICA DCL pro used in our labs, lockTopticaCTL().
Add a laser creating a class following the templateLaser().
The lasers here can be added to the locking via the lasers list in the main.

Suggest to use a .bat file, otherwise the server will use a generic name and if multiple lasers are used the remote access will be only to the last GUI opened.
    - Example of .bat file:    start "CTL2 lock" cmd.exe /k "call C:\Users\Localadmin\anaconda3\Scripts\activate.bat qcodes & call C:\Users\Localadmin\anaconda3\envs\qcodes\python.exe "C:\Users\Localadmin\Documents\scripts\GlabScripts\BlueLab\laser_control\laser_lock_5_0.py" "CTL2""
        change the path of the anaconda and location of the script accordingly

Needs to have:
    - qcodes enviroment (https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
    - PyQt5 (for the GUI, conda install PyQt5)
    - Pyro4 (conda install Pyro4)
    - to run the Toptical DLC (CTL) need the qcodes repository cloned (https://github.com/QCoDeS/Qcodes/tree/master/qcodes)

'''

import time
import sys
import visa
from PyQt5 import QtGui, QtCore
import Pyro4

from qcodes import Instrument
from Drivers_and_tools.laser_lock import laserWLMLock
from Drivers_and_tools.laser_lock_gui_5_0 import laserLockGUI, remote_lock_access
from Drivers_and_tools.TopticaDLCPro import TopticaDLCPro #needs the qcodes repository
import Drivers_and_tools.ppcl550driver as pp
from Drivers_and_tools.Tl6800control import TL6800

from network import pyro_tools,qt5_pyro_integration
Pyro4.expose(remote_lock_access)

# =============================================================================
# class templateLaser():
#     def __init__(self, params):
#         #pass all params that are necessary for the communication. Necessary params:
#         #name, ip_address, pid_p, pid_i, min_out, max_out, wl_min, wl_max, coarse_setting_accuracy
#     def connect_laser(self):
#         #establish the connection to the laser & the feedback channel (e.g. DAQ card)
#     def disconnect_laser(self, reset_feedback = True):
#         #disconnect from laser & feedback channel
#         #reset_feedback = False is used to pause the lock but maintain DC feedback
#     def set_wavelength_coarse(self, set_wavelength):
#         #Initially set the coarse wavelength (e.g. by motor)
#     def correct_wavelength_offset(self, set_wavelength, actual_wavelength):
#         #Correct for an offset between the laser wavelength setpoint and the wlm reading
#         #i.e. laser.set_wavelength_coarse(set_wavelength) produced a wlm reading of {actual_wavelength}
#     def apply_feedback(self, value):
#         #apply feedback e.g. to piezo. This is called repeatedly during the locking!
#         #{value} is the feedback value calculated by the PID
# =============================================================================

class lockTopticaCTL():
    def __init__(self, name, ip_address, pid_p = 0., pid_i = -1000., \
                 min_out = -10., max_out = 10., coarse_setting_accuracy = 500.):    
        #--------PARAMETERS----------

        self.name = name
        self.ip_address = ip_address
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.min_out = min_out
        self.max_out = max_out
        self.wl_min = 1460.
        self.wl_max = 1570.
        self.coarse_setting_accuracy = coarse_setting_accuracy  #MHz - how close the coarse setting needs to be
        self.piezo_offset = 70.

    def connect_laser(self):
        try:
             self.laser = Instrument.find_instrument(self.name)
        except KeyError:
            self.laser = TopticaDLCPro(self.name, self.ip_address)

    def disconnect_laser(self, reset_feedback = False):
        if reset_feedback:
            self.laser.piezo_voltage_setting(self.piezo_offset)
        self.laser.close()
        
    def set_wavelength_coarse(self, set_wavelength):
        self.laser.piezo_voltage_setting(self.piezo_offset)
        self.wavelength = set_wavelength
        self.laser.wavelength(self.wavelength)
        st = time.time()
        while not self.laser.get_laser_state() == '0':
            time.sleep(.1)
            if time.time() - st > 5.:
                return -1
        return 1

    def correct_wavelength_offset(self, set_wavelength, actual_wavelength):
        self.wavelength += set_wavelength - actual_wavelength
        self.set_wavelength_coarse(self.wavelength)
        return 1


    def apply_feedback(self, value):
        self.laser.piezo_voltage_setting(self.piezo_offset + value)


if __name__ == '__main__': 
    '''
    Example of usage
    '''
    app = QtGui.QApplication([])
    
    #initialise the lasers
    #ctl2 = lockTopticaCTL('CTL2', '192.168.1.XXX')
    #new_laser = Newlaserclass('NewLaser', '192.168.1.XXX')
    
    #list of lasers that can be locked
    lasers = [] #[ctl2, new_laser] 
    laser_names = [laser.name for laser in lasers]
    #to use .bat file to run the laser lock with the name of the laser in the name of the server, necessary to remote access several laser instead of only the last GUI opened
    if len(sys.argv)>1 and sys.argv[1] in laser_names:
        cur_laser = sys.argv[1]
        laser_idx = laser_names.index(cur_laser)
    else:
        cur_laser = None
    
    #use the IP of the machine running the wavementer server    
    lock = laserWLMLock(*lasers, wlm_address = 'PYRONAME:ws6server@192.168.1.XXX')
    Window = laserLockGUI(lock)
    if cur_laser is not None:
        Window.ui.comboBox.setCurrentIndex(laser_idx+1)
        Window.setWindowTitle("Laser Lock " + cur_laser)
    Window.show()
    
    def checkd():
        Window.save_exit()
        print('exit here')
    app.lastWindowClosed.connect(checkd)

    remote_access = remote_lock_access(lock,Window)
    
    #IP address of the machine where it will run, or 'localhost' to run it in the local machine
    #this server will let you have access to the remote control of the GUI (and so the laser), from other consoles or other machines in the local network
    host = 'localhost'
    daemon = Pyro4.Daemon(host=host)
    remote_access_uri = daemon.register(remote_access)

    #for the remote access with the name given by the .bat file
    if cur_laser is not None:
        pyro_tools.register_on_nameserver(host,'laser_lock_'+cur_laser, remote_access_uri, existing_name_behaviour='replace')
    else:
        pyro_tools.register_on_nameserver(host,'laser_lock', remote_access_uri, existing_name_behaviour='auto_increment')
    
    pyro_handler=qt5_pyro_integration.QtEventHandler(daemon)
    print('done')
        
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

