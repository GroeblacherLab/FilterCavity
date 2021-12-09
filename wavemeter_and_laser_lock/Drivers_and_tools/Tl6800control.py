'''

Created on 

@author: 

BSD 3-Clause License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

'''

import ctypes
import os
import numpy as np
import struct
import pickle
import time
import datetime
import multiprocessing
import math

import logging


class TL6800():
    ''' class used to lock the TL6800 laser, used in laser_lock_5_0s '''

    def __init__(self,P_ID = "100A", DevID = 1, wavelength_start = 1521, wavelength_stop = 1570, fwdvel = 10, bwdvel = 10, scancfg = 1):
        self.TLDLL = ctypes.CDLL("UsbDll.dll")
        self.TL6800_initialise_defaultvalues(P_ID, DevID, wavelength_start, wavelength_stop, fwdvel, bwdvel, scancfg)
        self.TL6800_startup_device()
        #self.TL6800_sweep_parameters()
    
    def TL6800_initialise_defaultvalues(self, P_ID, DevID, wavelength_start, wavelength_stop, fwdvel, bwdvel, scancfg):
        self.P_ID = P_ID 
        self.DevID = DevID
        self.wavelength_start = wavelength_start
        self.wavelength_stop = wavelength_stop
        self.fwdvel = fwdvel
        self.bwdvel = bwdvel
        self.scancfg = scancfg

    def TL6800_clear_buffer(self):
        #Sometimes the buffer needs to get rid off some output data, sometimes it doesn't, in which case it gives an OSError
        try:
            logging.info('buffer:', self.TL6800_read_ascii())
        except OSError:
            print("TL6700 reading error caught and passed")
            pass

    def TL6800_write_ascii(self, command, read = False, clear_before_read=True ):
        
        if read and clear_before_read:
            self.TL6800_clear_buffer()

        long_deviceid = ctypes.c_long(self.DevID)
        char_command = ctypes.create_string_buffer(command.encode())
        
        length = ctypes.c_ulong(len(char_command))
        self.TLDLL.newp_usb_send_ascii(long_deviceid,char_command,length)               #newp_usb_send_ascii (long DeviceID, char* Command, unsigned long Length);
       
        logging.info("Command sent to mr. TL6800: ",char_command.raw)

        #Reading the output that the laser returns is necessary not to get reading errors in second trials. For timing processes, it may not be preferred (mind to read after)
        if read:
            output = self.TL6800_read_ascii()
            return output
        else:
            self.TL6800_read_ascii(rlen=64)
        

    def TL6800_read_ascii(self, rlen=1024):
        long_deviceid = ctypes.c_long(self.DevID)
        Buffer = ctypes.create_string_buffer(rlen)                                        #ctypes.create_string_buffer(b"*IDN?",1024)
        Length = ctypes.c_ulong(len(Buffer))
        #BytesRead = 1024
        BytesRead = ctypes.create_string_buffer(1) 
        self.TLDLL.newp_usb_get_ascii(long_deviceid, Buffer, Length, BytesRead) # newp_usb_get_ascii (long DeviceID, char* Buffer, unsigned long Length, unsigned long* BytesRead);
        logging.info("Response sent by device: ",repr(Buffer.raw).split("\\x")[0][1:])
        output = repr(Buffer.raw).split("\\x")[0][1:]
        return output

    def TL6800_startup_device(self):
        try:
            self.TL6800_read_ascii()
        except OSError:
            print("TL6700 reading error caught and passed")
            pass
        self.TL6800_OpenAllDevices() 
        self.TL6800_OpenDevice()

        self.TL6800_clear_buffer()
    
        

    def TL6800_sweep_parameters(self):
        #SOURce:WAVE:START xxxx, SOURce:WAVE:STOP xxxx, SOURce:WAVE:SLEW:FORWard xx, SOURce:WAVE:SLEW:RETurn xx
        self.TL6800_sweep_wavelength_start()
        self.TL6800_sweep_wavelength_stop()
        self.TL6800_sweep_set_forwardvelocity()
        self.TL6800_sweep_set_backwardvelocity()
        
    def TL6800_sweep_start(self): #mind to put trackingmode on, prior
        self.TL6800_set_trackmode()
        command = 'OUTPut:SCAN:START'
        self.TL6800_write_ascii(command, read = read)

        
    def TL6800_sweep_wavelength_start(self):
        strwavelength_start = str(self.wavelength_start)
        command = 'SOURce:WAVE:START ' + strwavelength_start
        self.TL6800_write_ascii(command)

    def TL6800_sweep_wavelength_stop(self):
        strwavelength_stop = str(self.wavelength_stop)
        command = 'SOURce:WAVE:STOP ' + strwavelength_stop
        self.TL6800_write_ascii(command)


    def TL6800_sweep_set_forwardvelocity(self, fwdvel = None):         # [fdwvel] = nm/s
        if(fwdvel == None):  
            str_fwdvel = str(self.fwdvel)
            #print(str_fwdvel)
        else:
            str_fwdvel = str(fwdvel)
            print(str_fwdvel)
        command = 'SOURce:WAVE:SLEW:FORWard ' + str_fwdvel
        self.TL6800_write_ascii(command)

    def TL6800_sweep_set_backwardvelocity(self, bckwdvel = None):         # [fdwvel] = nm/s
        if(bckwdvel == None):  
            str_bwdvel = str(self.bwdvel)
        else:
            str_bwdvel = str(bckwdvel)
        command = 'SOURce:WAVE:SLEW:RETurn ' + str_bwdvel
        self.TL6800_write_ascii(command)

    def TL6800_set_piezo_voltage(self, piezovoltage):
        piezovolt = str(piezovoltage)
        command = 'SOURce:VOLTage:PIEZo ' + piezovolt
        self.TL6800_write_ascii(command, read=False)

    def TL6800_query_piezo_voltage(self):
        command = 'SOURce:VOLTage:PIEZo?'
        ret = self.TL6800_write_ascii(command, read=True)
        return float(ret.split(r'\r\n')[0][1:])

    def TL6800_set_brightness(self,  brightness):
        strbrightness = str(brightness)
        command ='BRIGHT ' + strbrightness               
        self.TL6800_write_ascii(command)

    def TL6800_query_wavelength(self):
        command = "SENSe:WAVElength"
        RawLambda = self.TL6800_write_ascii(command, read=True)
        #Returns lambda as "'xxxx.xxx\r\n..". Only keep the wavelength (xxxx.xxx)
        LambdaDigit = RawLambda[1:9]    
        return float(LambdaDigit)

    def TL6800_query_trackmode(self):
        command = "OUTPut:TRACk?"
        readbuffer = self.TL6800_write_ascii(command, read=True)
        trackmode = int(readbuffer[1])
        print("trackmode is: ", trackmode)
        try: 
            if trackmode == 1:
                trackbool = True
                return trackbool
            if trackmode == 0:
                trackbool = False
                return trackbool
        except:
            pass
            
    def TL6800_query_power(self):
        command = 'SENSe:POWer:DIODe'
        RawPower = self.TL6800_write_ascii(command, read=True)
        PowerDigit = RawPower[1:5]
        return PowerDigit

    def TL6800_query_current(self):
        command = 'SENSe:CURRent:DIODe'
        RawCurrent = self.TL6800_write_ascii(command, read=True)
        LaserDigit = RawCurrent[1:5]
        return LaserDigit

    def TL6800_set_wavelength(self, wavelength):
        wavelength = str(wavelength)
        command = 'SOURce:WAVElength ' + wavelength
        #toggle track mode on, otherwise actual output doesnt change
        self.TL6800_set_trackmode(onness = 1)
        self.TL6800_write_ascii(command)

    def TL6800_set_powermode(self, poweronness = 1):
        poweronness = str(poweronness)
        if poweronness == 1:
            command = 'SOURce:CPOWer ON'
        if poweronness == 0:
            command = 'SOURce:CPOWer OFF'
        self.TL6800_write_ascii(command)



    def TL6800_set_trackmode(self, onness = 1):                #Toggles Wavelength Track Mode (allows you to vary lambda).
    
        if onness == 1:
            command = 'OUTPut:TRACk ON'
        if onness == 0:
            command = 'OUTPut:TRACk OFF' 
            
        self.TL6800_write_ascii(command)
       
       
    def TL6800_set_power(self, power):  # [mW]
        command = 'SOURce:POWer:DIODe ' + str(power)    
        self.TL6800_write_ascii(command)

    def TL6800_set_current(self, current): #mA
        command = 'SOURce:CURRent:DIODe ' + str(current)
        self.TL6800_write_ascii(command)

     
    


    def TL6800_device_info(self):
        szDevInfo = ctypes.create_string_buffer(1024)
        self.TLDLL.newp_usb_get_device_info(szDevInfo)     # newp_usb_get_device_info (char* Buffer);
        #print(repr(szDevInfo.raw))
        #pretty elaborate, but this prints the device info only
        print("Made connection to: ", repr(szDevInfo.raw).split("\\x")[0][1:][3:(len(repr(szDevInfo.raw).split("\\x")[0][1:])-1)]) 
        return szDevInfo
        
    def TL6800_OpenAllDevices(self):
        self.TLDLL.newp_usb_init_system()

    def TL6800_OpenDevice(self):
        self.TLDLL.newp_usb_init_product(self.P_ID)

    def TL6800_CloseDevices(self):
        self.TL6800_clear_buffer()
        self.TLDLL.newp_usb_uninit_system()

    def TL6800_scancfg(self):         # 0 = do not reduce laser output to 0 during reverse scan, 1 = reduce laser output to 0 drs
        command = 'SOURce:WAVE:SCANCFG ' + str(self.scancfg)    
        self.TL6800_write_ascii(command)
     
    def TL6800_beep(self):
        command = 'BEEP'
        #print_response false because beep does not return anything
        self.TL6800_write_ascii(command)

    
         
def main():

    '''example of usage'''
    tl6800 = TL6800()
    lam = float(tl6800.TL6800_query_wavelength())
    newlam = 1550.0
    slptime = 2.0+1.0*abs(lam-newlam)
    
    time.sleep(.1)
    tl6800.TL6800_set_wavelength(newlam)
    time.sleep(slptime)
    lam = tl6800.TL6800_query_wavelength()
    
    time.sleep(1)
    
    tl6800.TL6800_CloseDevices()
        
if __name__ == '__main__': 
    main()
    
