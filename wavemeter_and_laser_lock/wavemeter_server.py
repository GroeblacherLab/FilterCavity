#new wavemeter server 2020
''' 
Created on 2020

@author: B.J.Hensen

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Code to run a wavemeter server that allows to read in series several lasers.


"""
WS6 server to allow multiple users (lasers) to be locked to the WS6 wavelength meter
    Example connection to this server:
        laser = 'CTL2'  #connect as CTL2 laser
        nameserver = Pyro4.locateNS('127.0.0.XXX')
        uri = nameserver.lookup('ws6server')

        wlm = Pyro4.Proxy(uri)
        wlm.register_user(laser)  #optional slot_length = 2.
        wlm.query_wavelength(laser)
        wlm.deregister_user(laser)

    Users initially register, the server then handles all connections and passes
    the WLM reading to make sure errors on the user side do not affect the server.
    It is possible to request a longer slot time than the standard time set on
    the server side while registering.
    The server closes the connection to the users after self.max_inactivity_time.
"""



Needs to have:
    - qcodes enviroment (https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
	- a wavemeter 
	- a 1xN optical switch 
	both connected to the machine running the server.
	- Pyro4 (conda install Pyro4)
	- ctypes (conda install ctypes)

'''

import time
from datetime import datetime
import numpy as np
import threading
import Pyro4

from network import pyro_tools
#import the used wavemeter
from Drivers_and_tools.HighFinesse_WS6 import Wavelengthmeter
#import the optical switch used to toggle the users
from Drivers_and_tools.Sercalo_1xN_switch import SercaloSwitch

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class WS6Server:
    def __init__(self):
        #timeout after which users are automatically disconnected
        self.max_inactivity_time = 60. #s

        #save users in dict with laser name as key and the slot length in seconds as element
        self.users = {}

        #initialise the optical switch used to toggle between the lasers
        self.sw = SercaloSwitch('XXXX') ######## use the switch used in the lab, COM4 ...
        self.sw.get_product_info()
        ######### use the same name of the lasers of laser_lock_5_0
        self.switch_positions = { 'CTL1'    : 1, \
                                  'CTL2'    : 2, \
                                  'TSL550'  : 3, \
                                  'TLB2'    : 4, \
                                  'TLB1'    : 5,
                                  'CTL3'    : 6,
                                  'NV'      : 7,
                                  'TEST2'   : 8}

        self.wlm = Wavelengthmeter()

        #User that is currently allowed to read the WLM
        self.current_user = ''

        self.wavelength = 0.

        #start threads to read the WLM continuously and toggle between the active users
        threading.Thread(None, self._read_wls, None).start()
        threading.Thread(None, self._toggle_usrs, None).start()

    def register_user(self, name, slot_length = 0.5):
        #Register a new user and the required slot length
        #Note if user is already registered, allow to update slotlength for i.e. a fine scan or a longer lock

        if not name in list(self.switch_positions.keys()):
            #Unknown user..
            return -1

        self.users[name] = [slot_length, time.time(), np.NaN]

        t = datetime.now().strftime("%H:%M:%S")
        print(f"{t}: Connected to {name}")
        
        return 1
    
    def query_available_users(self):
        return [k for k in self.switch_positions.keys()]

    def deregister_user(self, name):

        if not name in self.users:
            return 0 #not there

        del self.users[name]

        t = datetime.now().strftime("%H:%M:%S")
        print(f"{t}: Disconnected {name}")

        return 1


    def query_users(self):
        #allows to check which laser is connected
        return self.users.keys()
    
    def query_last_readings(self):
        #allows to check which laser is connected
        return self.users

    def query_current_user(self):
        #check who's currently reading the WLM
        return self.current_user

    def query_wavelength(self, usr, timeout = 10.):
        #return wavelength once it is the turn of the user
        st = time.time()
        if not usr in self.users:
            return -1

        self._reset_query_time(usr) #log initial request time so the user is not kicked while waiting
        while True:
            if usr == self.current_user:
                self._reset_query_time(usr)   #log tranmittance time
                return self.wavelength

            if time.time() - st > timeout:
                return 0
            #dead time to let the switch to toggle user and not have reading of a laser associated with the wrong laser
            time.sleep(0.02) 


    def _read_wls(self):
        #looped continuously in own thread to read the wavelength
        while True:
            self.wavelength = self.wlm.getWL()
            if self.current_user in self.users:
                self.users[self.current_user][2]  = self.wavelength    
            time.sleep(0.1)

    def _reset_query_time(self, user):
        #reset the time of the last query of a given user
        self.users[user][1] = time.time()
        return

    def _kick_inactive_users(self):
        #kick users after max inactivity timeout
        delete = [key for key in self.users \
            if (time.time()-self.users[key][1]) > self.max_inactivity_time]
        for key in delete:
            print(f"Kicking {key} for inactivity")
            del self.users[key]
        return

    def _toggle_usrs(self):
        #looped continuously in own thread to handle the switching between different users
        self.slot_start = time.time()
        current_idx = 0
        while True:
            time.sleep(0.1)     #sleep to reduce CPU usage!

            #we disregard that the current_user might disconnect before we reach the time.sleep(_slot_len)
            #code could thus be more efficient
            _users = self.users

            if len(_users) > 0:

                self.current_user = ''

                #toggle though the currently registered usrs
                current_idx = (current_idx+1) % len(_users)
                #convert index to key
                _user_key = list(_users.keys())[current_idx]

                #switch (and wait a moment to let the wlm settle)
                self._switch_to_usr(_user_key)
                time.sleep(0.05) #dead time to teggle between users with 10ms integration on the wavemeter              
                
                try:
                    _slot_len = _users[_user_key][0]
                except KeyError:
                    print("Key Error again - fix this!")
                    #howdoesthishappen?
                    _slot_len = 0.1 
                    _user_key = ''

                self.current_user = _user_key



                #bit of housekeeping
                self._kick_inactive_users()

                #wait for slot length (even if we actually just kicked the curren user)
                time.sleep(_slot_len)

    def _switch_to_usr(self, name):
        #print("Switching to {name}: channel{self.switch_positions[name]}")
        switched = False
        for i in range(3): #lets try 3 times in case st goes wrong.
            if switched:
                break
            try:
                switched = self.sw.set_channel(self.switch_positions[name])
            except Exception as e:
                print(f'Error switching to {name}',e)
                self.sw.close()
                time.sleep(0.1)
                self.sw.connect()
                time.sleep(0.1)
        time.sleep(0.1)

if __name__ == '__main__':
	#run the file to have the server running on the machine with the IP = host, the machine needs to be connected to the wavemeter
    ws6 = WS6Server()

    host = '192.168.1.XXX'   ######## use the IP of the machine used in the lab
    nameserver  = True
    share_name  = 'ws6server'

    daemon = Pyro4.Daemon(host=host, port=9092)
    uri = daemon.register(ws6)

    if nameserver:
        pyro_tools.register_on_nameserver(host, share_name, uri)

    print('Starting server loop')
    daemon.requestLoop()
