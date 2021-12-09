import time
import datetime
import numpy as np
import Pyro4
from glablibraries.lib.Tools.PID import PID


class laserWLMLock():
    def __init__(self, *available_lasers, wlm_address = 'PYRONAME:ws6server@192.168.1.245'):
        # --------CONSTANTS----------
        
        self.wlm_address = wlm_address 
        self.wlm_reconnect_tries = 5
        self.wlm_reconnect_waittime = 2
        
        self.intial_time_wait_check = 30 #seconds
        self.max_diff_consecutive_reading = 500 #MHz
        
        self.available_lasers = {}
        for l in available_lasers:
            self.available_lasers[l.name] = l
        
        # WLM        
        self.connect_wavemeter()
        
        
        self.pid = PID()
        self.speed_of_light = 299792458

    def connect_wavemeter(self):
        self.wlm = Pyro4.Proxy(self.wlm_address)
        
    def get_wavelengt(self):
        connection_failed = False
        for i in range(self.wlm_reconnect_tries):
            try: 
                if connection_failed:
                    self.connect_wavemeter()
                    self.wlm.register_user(self.laser.name)
                return self.wlm.query_wavelength(self.laser.name)
            except Exception as e: #TODO put correct exception class here 
                print(f'WARNING: could not get laser {self.laser.name} wavelength. Try {i:d}/{self.wlm_reconnect_tries:d}')
                print(e)
                time.sleep(2)
                connection_failed = True

    def get_available_lasers(self):
        return list(self.available_lasers.keys())


    def initialize_lock(self, laser_name, setpoint):

        self.laser = self.available_lasers[laser_name]
        print(f"Switched to lock for {laser_name}")
        self.laser.connect_laser()
        self.pid.change_setpoint(setpoint)
        self.pid.setKp(self.laser.pid_p)
        self.pid.setKi(self.laser.pid_i)

        self.wlm.register_user(self.laser.name)


    def set_coarse_wavelength(self, setpoint):
        act_wl = self.get_wavelengt()
        freq_diff = -(self.speed_of_light/(act_wl*1e-9) - (self.speed_of_light/(setpoint*1e-9)) )/1e6
        if np.fabs(freq_diff) < self.laser.coarse_setting_accuracy:
            #check if we are good already (e.g. we paused & restarted the lock)
            print("Coarse WL set immediately")
            return 1
        
        #Set the wavelength initially. 
        self.laser.set_wavelength_coarse(setpoint)

        #Check if there is an offset from the laser wavelength to the WLM reading
        while True:
            act_wl = self.get_wavelengt()
            print(f"Current wavelength {act_wl}")
            freq_diff = -(self.speed_of_light/(act_wl*1e-9) - (self.speed_of_light/(setpoint*1e-9)) )/1e6
            print(f"freq_diff {freq_diff}")
            if np.fabs(freq_diff) > self.laser.coarse_setting_accuracy:
                self.laser.correct_wavelength_offset(setpoint, act_wl)
            else:
                print(f"Done setting wavelength to accuracy {freq_diff:.0f} MHz")
                if hasattr(self.laser,'coarse_setting_done'):
                    self.laser.coarse_setting_done()
                    print('laser coarse done')
                break
            
            
        return 1


    def terminate_lock(self, reset_feedback = True):
        try:
            if reset_feedback:
                self.pid.clear()
            self.wlm.deregister_user(self.laser.name)
            self.laser.disconnect_laser(reset_feedback)
        except AttributeError as e:
            print(e)
            pass
        except OSError as e:
            print(e)
            pass

    def pause_lock(self):
        self.terminate_lock(reset_feedback = False)
        
    def change_pid_setpt(self, new_setpt):
        self.pid.change_setpoint(new_setpt)

    def update_piezo(self, time_diff):
        act_wl = self.get_wavelengt()
        if time_diff < self.intial_time_wait_check: #to let the laser go to the set wavelength
            feedback_val = self.pid.update(act_wl)
            self.laser.apply_feedback(feedback_val)
        else:
            try:
                freq_diff = -(self.speed_of_light/(act_wl*1e-9) - (self.speed_of_light/(self.pid.SetPoint*1e-9)) )/1e6 #in MHz, the slider updates the setpoint
                if abs(freq_diff) > self.max_diff_consecutive_reading: #needed because sometimes the reading is off (take the wavelength of another laser or switch not working ...)
                    now = datetime.datetime.now()
                    feedback_val = 0 #just to return a value for the GUI
                    print(f'Jump in wavelength! {freq_diff:.1f} MHz, {now.strftime("%H:%M:%S")}')
                else:
                    feedback_val = self.pid.update(act_wl)
                    self.laser.apply_feedback(feedback_val)
            except:
                print(f"actual wavelength measured : {act_wl:f}")
                feedback_val = 0
        #print(f"WL={act_wl}, Set={self.pid.SetPoint}, feedb={feedback_val}")
        
        return feedback_val, act_wl

