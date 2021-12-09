import time
import sys
import visa
# import nidaqmx
from PyQt5 import QtGui, QtCore
import Pyro4

from qcodes import Instrument
from glablibraries.lib.laser_control.laser_lock import laserWLMLock
from glablibraries.lib.laser_control.laser_lock_gui_5_0 import laserLockGUI, remote_lock_access
from glablibraries.drivers.qcodes_instruments.TopticaDLCPro import TopticaDLCPro
import glablibraries.drivers.ppcl550driver as pp
from glablibraries.drivers.Tl6800control import TL6800

from glablibraries.lib.network import pyro_tools,qt5_pyro_integration
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




class lockTL6800():
    def __init__(self, name, pid_p = 0., pid_i = 2000.,  \
				 min_out = -15., max_out = 15., coarse_setting_accuracy = 600.):    
		#--------PARAMETERS----------
        self.name = name
        # self.daq_chan = daq_chan
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.min_out = min_out
        self.max_out = max_out
        self.wl_min = 1520.
        self.wl_max = 1580.
        self.coarse_setting_accuracy = coarse_setting_accuracy #MHz - how close the coarse setting needs to be
        
        self.piezo_offset = 50.

			
    def connect_laser(self):
        self.laser = TL6800()
        time.sleep(0.1)
			
        # self.output_task = nidaqmx.task.Task()
        # self.output_task.ao_channels.add_ao_voltage_chan(self.daq_chan, min_val=self.min_out, max_val=self.max_out)
        # self.output_task.write(0.0)
			
    def disconnect_laser(self, reset_feedback = False):
        if reset_feedback:
            self.laser.TL6800_set_piezo_voltage(self.piezo_offset)
            time.sleep(0.1)
        # self.output_task.close()
        print('laser close')
        self.laser.TL6800_CloseDevices()	

    def set_wavelength_coarse(self, set_wavelength):
        self.laser.TL6800_set_piezo_voltage(self.piezo_offset)
        self.wavelength = set_wavelength
        self.curlam = float(self.laser.TL6800_query_wavelength())        # First we figure out how far away we are to set the (maybe long) wait time.
        time.sleep(0.1)
        self.sleeptime = 2.5+1.0*abs(self.wavelength-self.curlam) # Based on a 1-s per nm scan speed we saw on 15-04-2020
        self.laser.TL6800_set_wavelength(set_wavelength)
        time.sleep(self.sleeptime)          
        return 1
    
    def coarse_setting_done(self):
        self.laser.TL6800_set_trackmode(0)
		
    def correct_wavelength_offset(self, set_wavelength, current_wavelength):
        self.wavelength += set_wavelength - current_wavelength
        self.set_wavelength_coarse(self.wavelength)
        return 1
    
    def apply_feedback(self, value):
        value = min(self.max_out, value)
        value = max(self.min_out, value)        
        self.laser.TL6800_set_piezo_voltage(self.piezo_offset + value)
        time.sleep(0.1)

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


class lockPPCL550():
    def __init__(self, name, com_port, daq_channel, pid_p = 1000., pid_i = 20000., \
                 min_out = 0., max_out = 6., defaultAO = 3., defaultFTF = 15000e-6, \
                 FM_default = 50e-6, coarse_setting_accuracy = 10.):    
        #--------PARAMETERS----------

        self.name = name
        self.com_port = com_port
        self.daq_channel = daq_channel
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.min_out = min_out
        self.max_out = max_out
        self.defaultAO = defaultAO # sets the default analog output of the DAc to {} V.
        self.defaultFTF = defaultFTF # sets the default of the Fine TuNIng Frequency register of the laser to {} GHz
        self.FM_default = FM_default # frequreency modulation  corresponding to the default analog output of the DAC
        self.wl_min = 1520.
        self.wl_max = 1570.
        self.coarse_setting_accuracy = coarse_setting_accuracy  #MHz - how close the coarse setting needs to be

    def connect_laser(self):
        self.laser=pp.PPCL550(self.com_port)
        if self.laser.is_on():
            self.laser.off()        #make sure laser is off
        time.sleep(0.5)
        
        self.output_task= nidaqmx.task.Task()
        self.output_task.ao_channels.add_ao_voltage_chan(self.daq_channel, min_val = self.min_out, max_val = self.max_out)
        
        
    def disconnect_laser(self, reset_feedback = True):
        if not reset_feedback:
            self.laser.close(switch_off = False)
            self.output_task.write(3.)              #get ready to start the beatlocking next
        else:
            self.laser.close(switch_off = True)
            self.output_task.write(0.)
        self.output_task.close()

    def set_wavelength_coarse(self, set_wavelength):
        #subtract the offsets
        adj_set_wavelength = self.laser.f2w(self.laser.w2f(set_wavelength) - self.defaultFTF - self.FM_default)
        self.laser.wavelength = adj_set_wavelength    #laser needs to be off here!
        
        print("Switching laser on")
        self.laser.on()
        while not self.laser.NOP():
            time.sleep(0.5)
            
        print('Setting FTF and DAC output to default initial values')
        self.laser.FTF= self.defaultFTF*1e6
        self.output_task.write(self.defaultAO)
        
        while not self.laser.NOP():
            time.sleep(0.5)
        self.laser.LN = 1 # make sure laser is in LowNoise mode

        print('Waiting for the wavelength to set...')
        time.sleep(2.)        
        return 1

    def correct_wavelength_offset(self, set_wavelength, current_wavelength):
        p = 0.5
        freq_diff = -(299792458/(current_wavelength*1e-9) - (299792458/(set_wavelength*1e-9)) )/1e6
        ftf_jump = p * freq_diff
        self.laser.ftf(ftf_jump)
        time.sleep(3.5)
        return 1


    def apply_feedback(self, value):
        voltage = self.defaultAO + value
        voltage = min(voltage, self.max_out)
        voltage = max(voltage, self.min_out)
        self.output_task.write(voltage)


if __name__ == '__main__': 
    
    app = QtGui.QApplication([])
    
    ctl1 = lockTopticaCTL('CTL1', '192.168.1.229')
    ctl2 = lockTopticaCTL('CTL2', '192.168.1.228')
    #ppcl = lockPPCL550('PPCL550', 'COM3', 'cDAQ1Mod3/ao0')
    tl6700 = lockTL6800('TLB1')
    
    lasers = [ctl1, ctl2, tl6700]
    laser_names = [laser.name for laser in lasers]
    if len(sys.argv)>1 and sys.argv[1] in laser_names:
        cur_laser = sys.argv[1]
        laser_idx = laser_names.index(cur_laser)
    else:
        cur_laser = None
        
    lock = laserWLMLock(*lasers)
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
    
    host = 'localhost'
    daemon = Pyro4.Daemon(host=host)
    remote_access_uri = daemon.register(remote_access)

    if cur_laser is not None:
        pyro_tools.register_on_nameserver(host,'laser_lock_'+cur_laser, remote_access_uri, existing_name_behaviour='replace')
    else:
        pyro_tools.register_on_nameserver(host,'laser_lock', remote_access_uri, existing_name_behaviour='auto_increment')
    
    pyro_handler=qt5_pyro_integration.QtEventHandler(daemon)
    print('done')
        
    # %%
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    #app.exec_()
    
    
    ##### to check what servers are running on the localhost
    #nameserver=Pyro4.locateNS("localhost")
    #nameserver.list()
