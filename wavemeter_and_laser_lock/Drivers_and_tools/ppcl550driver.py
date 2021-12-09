#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 11:08:06 2019

@author: ufilippozzi

BSD 3-Clause License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

"""
import serial
import numpy as np
import math
import time
import pandas as pd
from os import path
import os
import nidaqmx  # for the DAC card

import glablibraries.drivers.PP_library as pp # methods provided by Pure Photonics

class PPCL550(object):
    '''#Driver for PPCL550 laser 
    
    The coding of this driver is based on the document OIF-ITLA-MSA-01.3.pdf, 
    in the code I will referre to the pages of this file. 
    
    
    #implemented functionalities:
    __init__:                   Define the instance of the class PPCL550, 
                                   the address of the serial communication port 
                                   can be updated after initialization
    initialize:                 Opens the communication with the laser.
    close:                      Closes the communication with the laser.
    on/ off:                    Self-explanatory
    power (get/set):            Takes the input power in dBm or sets it if its compatible with 
                                   the device limitations.
    frequency(get/set)              Gives back the frequency of the laser in THz accounting for 
                                    all the contributions (central frequency, fine tuning and channel...)
                                    When set this command controls the central_frequency registers (see pag 68)
                                    while setting FTF to 0 and chananel to 1.
    Configuration (get)         Method that reads all the relevant parameters and gives back the setting of 
                                    of the laser, may be useful when saving traces TO BE IMPLEMENTED.
    grid(GET/SET)               Method to get or set the grid spacing: takes values in GHz
    channel(get/set)            Sets the value of the 16-bit register which defines the frequency 
                                    of the output (see pag 68). Changing the value during operation will 
                                    cause the module to turn off automatically and turn on when the laser
                                    is locked again.
    FTF (set/get)               Fine tuning of the output frequency with a resolution of 1MHz and a range
                                    of 30GHz. This command allows for in-operation adjustment of the 
                                    laser frequency. Does not accept negative values!
    ftf()                       Takes a value in MHz and sums it to the current value of the register FTF
    
    
    
    
    
    

    
    FREQUENCY_JUMP(ON/OFF)
    FREQUENCY_JUMP_SET(GET7SET)
    FREQUENCY_STEPPING
    FREQUENCY_STEPPING_SET
    FREQUENCY_SWEEP(ON/OFF)
    FREQUENCY_SWEEP_SET(GET/SET)

    '''
   
    
    
   
    def __init__(self, port_address, trigger=True):
        self.port=port_address#string containing the addres of the USB port
        self.path='PPCL550_Calibration_Files\\'
        
        baudrate= 9600
        self.handle=pp.ITLAConnect(self.port,baudrate)
        if self.handle == pp.ITLA_ERROR_SERPORT:
            print("Connection not established: port not found")
        elif self.handle==pp.ITLA_ERROR_SERBAUD:
            print("Error: connection not established")
        else:
            print("Connection established")
            print("Port:      ", self.port)
            print("Baudrate:  ", self.handle.baudrate)
            #return(self.handle)
        
        # upload calibration files
        chk=self.upload_cal_files()
        self.CalibrationRequired=False
        if chk==0:
            self.CalibrationRequired=True
        
        # initialize DAC port for trigge
        if trigger:
            self.daq_channel='Dev1/ao1'
            self.min_out=0
            self.max_out=6
            self.idle_time=0.5 # width of the trigger signal
            self.trig_delay_CS=0.1# delatu time between trigger event and sweep.
            self.trig_delay_CJ=0.# delay time between trigger event and jump
            self.trig= nidaqmx.task.Task()
            self.trig.ao_channels.add_ao_voltage_chan(self.daq_channel, min_val = self.min_out, max_val = self.max_out)
        
       
    def close(self, switch_off = True):
        if switch_off:
            if self.is_on():
                self.off()
                print('laser off')
            
        self.handle.close()
        if self.handle.isOpen():
            return ('Port still open.')
        else:
            return ('Port closed.')
    
    def NOP(self):
        out=pp.ITLA(self.handle,0x00, 0,0) # reads the NOP register (page 39)
        #print (bin(int(hex(out),16))[2:].zfill(16))
        if out==16: #no operation pending, no errors
            return(True)
        else: #some operations are still pending, or some erro occurred
            return(False)
            
    def wait4NOP(self):
        print('Waiting for NOP')
        while not self.NOP():
            time.sleep(0.5)
    
    def MRDY(self): # returns True if the module is ready for its output to be turned on
        out=pp.ITLA(self.handle,0x00, 0,0) # reads the NOP register (page 39)
        b=bin(int(hex(out),16))[2:].zfill(16)
        mrdy=b[11]
        if mrdy=='1': #module ready
            return(True)
        else:   
            return(False)

    def is_on(self):
        out= pp.ITLA(self.handle, pp.REG_Resena,0,0)
        #print(out)
        if out==0:
            flag=False
        elif out==8:
            flag=True
        else:
            flag='troubles'
               
        return(flag)
    
    def on(self):
        if self.is_on():
            return("Laser on")
            return(0)
            
        #set the module to Dither Mode for a faster locking 
        if self.LN==2:
            flag=1
            self.LN=0
        elif self.LN==0:
            flag=0
        else:
            print('unknown response')
        
        print('Waiting for the module to be ready')
        while not self.MRDY():
            print('waiting')
            time.sleep(0.25)
                
        pp.ITLA(self.handle, pp.REG_Resena, 8, 1)#turn on the laser
        self.wait4NOP()
        self.LN=flag# restore the laser to previous mode
        self.wait4NOP()
        if self.is_on():
            print("Laser on")
            return(1)
        else:
            print("Laser off")
            return(0)
    
        
        
    def off(self):
        if not self.is_on():
            return("Laser off")
        
        pp.ITLA(self.handle, pp.REG_Resena, 0, 1)#turn off the laser
        if self.is_on():
            return("Laser on")
        else:
            return("Laser off")
    
    @property
    def LN(self):
        out1=pp.ITLA(self.handle, 0x90, 0,0)
        if out1==0:
            print('Dither mode')
        elif out1==2:
            print('LowNoise mode')
        else:
            print('Unknown response')
        return(out1)
        #return(out1)
        
    @LN.setter   
    def LN(self, flag):
        test=self.LN
        print('########')
        if flag==0:
            pp.ITLA(self.handle,0x90 , 0,1)
        elif flag==1:
            pp.ITLA(self.handle,0x90 , 1,1)  
        else:
            print('Unknown input')
        test=self.LN
        return(test)

   
    @property
    def frequency(self):
        outp1= pp.ITLA(self.handle, pp.REG_Fcf1, 0, 0)#returns THz part of frequewncy
        outp2= pp.ITLA(self.handle, pp.REG_Fcf2, 0, 0)# returns GHz part *10
        outp3= pp.ITLA(self.handle, 0x69, 0, 0)# returns MHZ
        channel=self.channel
        grid_spacing=self.grid
        ftf=pp.ITLA(self.handle,0x62, 0,0)
        freq=(outp1+outp2/10000+(outp3+ftf)/1000000)+(channel-1)*grid_spacing/1000
        wv=self.f2w(freq)
        print('fcf1:         ', outp1)
        print('fcf2:         ', outp2)
        print('grid:         ', grid_spacing)
        print('channel:      ', channel)
        print('FTF:          ', ftf)
        #print('Laser Frequency[THz]: ',freq)
        return([freq,wv])
       
    @frequency.setter
    def frequency(self, freq): # frequency to be given in THz, returns set frequency
        #print('setting frequency...')
        bound=self.frequency_lim
        if self.is_on():
            #print(self.is_on())
            print("Turn off the laser first, or use a different command")
        elif bound[0]<=freq and freq<=bound[1]:
            THzf=math.floor(freq)
            GHzf=math.floor((freq-THzf)*10000)
            print('THz:       ', THzf)
            print('GHz*10:    ', GHzf)
            outp1= pp.ITLA(self.handle, pp.REG_Fcf1, THzf, 1)
            outp2= pp.ITLA(self.handle, pp.REG_Fcf2, GHzf, 1)
            # sets FTF to 0 and channel to 1
            self.FTF=0
            self.channel=1
            
            freq=outp1+outp2/10000
            print('Laser Frequency set to: ', self.frequency)
            return(freq)
        else:
            print('Frequency exceedes device''s capabilities')
            return(0)
    
    @property
    def wavelength(self):
        outp1= pp.ITLA(self.handle, pp.REG_Fcf1, 0, 0)#returns THz part of frequewncy
        outp2= pp.ITLA(self.handle, pp.REG_Fcf2, 0, 0)# returns GHz part *10
        channel=self.channel
        grid_spacing=self.grid
        ftf=pp.ITLA(self.handle,0x62, 0,0)
        freq=(outp1+outp2/10000+(ftf)/1000000)+(channel-1)*grid_spacing/1000
        wv=self.f2w(freq)
        #print('Laser Frequency[THz]: ',freq)
        return(wv)
       
    @wavelength.setter
    def wavelength(self, wv): # frequency to be given in THz, returns set frequency
        #print('setting frequency...')
        freq=self.w2f(wv)
        print(freq)
        self.frequency=freq
        
    @property
    def wavelength_lim(self):
        f_lim=self.frequency_lim
        w_llim=self.f2w(f_lim[1])
        w_hlim=self.f2w(f_lim[0])
        return([w_llim,w_hlim])
        

       
    @property
    def frequency_lim(self):
        lfthz=pp.ITLA(self.handle, pp.REG_Lfl1, 0,0)
        lfghz=pp.ITLA(self.handle, pp.REG_Lfl2, 0,0)
        hfthz=pp.ITLA(self.handle, pp.REG_Lfh1, 0,0)
        hfghz=pp.ITLA(self.handle, pp.REG_Lfh2, 0,0)
        f_min=lfthz+lfghz*0.00001
        f_max=hfthz+hfghz*0.00001
        return ([f_min, f_max])
   
    @property
    def power_lim(self): # gives back the maximum power range in dBm
        low_p= pp.ITLA(self.handle, pp.REG_Opsl, 0, 0)
        high_p= pp.ITLA(self.handle, pp.REG_Opsh, 0, 0)
        return([low_p*0.01, high_p*0.01])
          
    @property
    def power(self): #gives back the estimated value of power output in dBm
        if self.is_on():
            out=pp.ITLA(self.handle, pp.REG_Oop, 0, 0)
            pw=out*0.01
        else:
            try:
                print("Laser is off: returning previously set value")
                pw=self.pw_set
            except:
                print("Laser is off:")
                pw=0
        pw_mw=10**(pw/10)  
        return([pw, pw_mw])
        
        
    @power.setter # power can be set only with the laser off
    def power(self, pw): #takes power setpoints in dBm and gives back the set value in dBm
        bound=self.power_lim
        
        if self.is_on():
            flag=True
            print('Shutting down the laser')
            self.off()
            
        if bound[0]<=pw and pw<=bound[1]:
            print('Setting power ...')
            self.pw_set=pw
            value=pw/0.01
            out=pp.ITLA(self.handle, pp.REG_Power, value, 1)
            pw=out*0.01
        elif pw<bound[0]:
            print('Power exceedes device''s capabilites')
            pw=bound[0]
        elif pw>bound[1]:
            print('Power exceedes device''s capabilites')
            pw=bound[1]
        
        if flag:
            print('Turning laser on')
            self.on()
        return(pw)
   
    @property
    def grid_lim(self):#returns the minimum frequency grating possible
        out1=pp.ITLA(self.handle,0x56 , 0,0)#get 10*GHz part
        out2=pp.ITLA(self.handle,0x6B , 0,0)# get MHz part
        f_grid_min= out1/10+out2/1000
        return(f_grid_min)
    
    
    @property 
    def grid(self):
        out1=pp.ITLA(self.handle,0x34 , 0,0)#get 10*GHz part
        out2=pp.ITLA(self.handle,0x66 , 0,0)# get MHz part
        f_grid= out1/10+out2/1000
        return(f_grid)
        
    @grid.setter
    def grid(self, value): #takes the grid spacing frequency in GHz
        fGHz=math.floor(value*10)
        fMHz=math.floor((value-fGHz/10)*1000)
        bound=self.grid_lim
        if self.is_on():
            print('Grid spacing can be modified only if laser output is disenabled')
            return(0)
        elif bound > value:
            print('Grid spacing is too small')
        else:
            out1=pp.ITLA(self.handle,0x34 , fGHz,1)#set 10*GHz part
            out2=pp.ITLA(self.handle,0x66 , fMHz,1)# set MHz part
            f_grid= out1/10+out2/1000
            return(f_grid)
    
    @property
    def channel(self):#reads the 32bit number associated with the channel.
        out1=pp.ITLA(self.handle,0x30, 0,0)
        out2=pp.ITLA(self.handle,0x65, 0,0)
        #print(bin(int(hex(out1),16))[2:].zfill(16))
        #print(bin(int(hex(out2),16))[2:].zfill(16))
        channel=out1+out2*2**(16)
        return(channel)
        
    @channel.setter
    def channel(self,channel): #takes channel and maps into 32bit register.
        if 0<channel and channel <4294967296:
            ch2=math.floor(channel/(2**16))
            ch1=math.floor(channel-ch2*2**16)
            print(ch1)
            print(ch2)
            out2=pp.ITLA(self.handle,0x65, ch2,1)
            out1=pp.ITLA(self.handle,0x30, ch1,1)
            print('#########')
            print(out1)
            print(out2)
            channel_set=out1+out2*2**(16)
            return(channel_set)
        else:
            print('given value can not be represeted on 32-bit register')
    
    @property
    def FTF_lim(self): # gets the fine-tune frequency-range in MHz
        ftf_lim=pp.ITLA(self.handle, 0x4F, 0,0)
        return(ftf_lim)
    
    @property
    def FTF(self): #gets the fine-tune frequency settin in MHz
        ftf=pp.ITLA(self.handle,0x62, 0,0)
        return(ftf)
        
    @FTF.setter
    def FTF(self, ftf): #sets fine tune frequency in MHz 
        bound=self.FTF_lim
        if abs(ftf)<bound:
            ftf=pp.ITLA(self.handle, 0x62, ftf, 1)
        else:
            ftf=pp.ITLA(self.handle, 0x62, bound, 1)
            print('Given value exceeds FTF maximum value')
        return(ftf)
            
    
    def ftf(self, jump): # allows to make positive and negative jumps in the value of the FTF register.
        # first read the FTF register
        old_FTF=self.FTF
        # and set the updated one
        new_FTF=old_FTF+jump
        if new_FTF<0:
            new_FTF=0
        
        print('New FTF:  ', new_FTF)
        self.FTF=new_FTF

        
            
    '''########################''' 
    #Clean Frequency sweep suite
    @property
    def CSRange(self):
        CsRange=pp.ITLA(self.handle, 0xe4, 0,0)# gets the frequency sweep in units of GHz
        return(CsRange)
    
    @CSRange.setter
    def CSRange(self, rang): # takes sweep range in GHz
        if rang>250000:
            print('Range is too big for devices capabilities')
            return(0)
        elif 150000<rang and rang<250000:
            out = pp.ITLA(self.handle, 0xE4, rang, 1)
            print('Extended Sweep mode required: provide calibration files')
            return(out)
        elif 0<rang and rang<150000:
            out = pp.ITLA(self.handle, 0xE4, rang, 1)
            return(out)
        else:
            print('Range value non compatible')
            return(0)
            
            
    @property
    def CSFreq_Offset(self):
        offset=pp.ITLA(self.handle, 0xE6,0,0)#read offset in units of 100MHz
        return(offset)
        
    @property
    def CSSpeed(self):
        csspeed=pp.ITLA(self.handle, 0xF1, 0,0)#useless: this is a write-only register
        try:
            csspeed=self.set_csspeed
        except:
            print('CS speed not set yet...')
            csspeed=0
            
        return(csspeed)
        
        
    @CSSpeed.setter
    def CSSpeed(self, speed): # takes speed in GHz/s
        if 0<speed*1000 and speed*1000<2**16-1:
            csspeed=pp.ITLA(self.handle, 0xF1, speed*1000, 1)
            self.set_csspeed=csspeed
        else:
            print('given speed exceeds device''s capabilities: max =65GHZ/s')
            csspeed=pp.ITLA(self.handle, 0xF1, 2**16-1 , 1)
            self.set_csspeed=csspeed
        return(csspeed)
        
    def CleanSweep(self, string , SweepSpeed, SweepRange, trigger=True):
        
        if string=='on':
            self.CSSpeed=SweepSpeed
            self.CSRange=SweepRange
            #self.frequency=CentralFrequency # set central frequency
            self.on()
            self.LN=1
            self.wait4NOP()
            time.sleep(0.5)#recommended
            pp.ITLA(self.handle, 0xE5, 1,1)#enable sweep mode
            
            if trigger==True:
                time.sleep(1.5*SweepRange/SweepSpeed+self.trig_delay_CS)
                self.trig.write(5.)
                time.sleep(self.idle_time)
                self.trig.write(0.)
            
            print('Sweep mode on:\n  Sweep rate [GHz/s]:       ', self.CSSpeed)
            print('Central Frequency[THz]:                     ', self.frequency)
            print('Frequency range[+-GHz]:                     ', self.CSRange )
            return(0)
            
        elif string=='off':
            
            # wait for the wavelength to be close to the central frequency
            while abs( pp.ITLA(self.handle, 0xE6, 0,0))>20:
                print(pp.ITLA(self.handle, 0xE6, 0,0))
                time.sleep(0.1)
                
            pp.ITLA(self.handle, 0xE5, 0, 1)# disenable sweep mode
            self.wait4NOP()
            self.LN=0# lock the laser
            self.wait4NOP()
            print('Sweep mode off')
            return(0)
        else:
            print("Unknown input string")
            return(0)
            
            
    #Clean Frequency Jump Suite
    def upload_cal_files(self):  
        
        # check if calibration files are present
        self.serial_number=pp.ITLA(self.handle, 0x04, 0,0)[0:10]
        extentions=['_700_9_15_37_4_map.csv','_1000_9_15_37_4_map.csv', '_1350_9_15_37_4_map.csv', '_csmap.csv', '_current2.csv', '_9_15_38_41_li.csv', '_9_15_40_23_sled.csv' ]
        self.filenames=[self.path+self.serial_number+ext for ext in extentions]
        print(self.filenames)
        self.filenumber=len(self.filenames)
        self.CalibrationFiles=[]
        jj=1
        for filename in self.filenames:
            
            print('filename: '+ filename)
            if os.path.exists(filename):
                df=pd.read_csv(filename)
                self.CalibrationFiles.append(df)
            else:
                print('Calibration Files missing')
                print(filename+'  not found') 
                print('If .csv file not present close the connection with the laser and\n run Convert_Calibration_Files.py')
                jj=jj*0
        
        return(jj)

    @property
    def next_frequency(self):
        try:
            self.NextFrequency+=0
            #print('Next frequency[THz]: ', self.NextFrequency)
        except:
            print('NextFrequency not set yet...') 
            self.NextFrequency=0
        return(self.NextFrequency)
    
    @next_frequency.setter    
    def next_frequency(self, new_f): # sets the next frequency in THz
        bound=self.frequency_lim
        # check if new frequency is valid
        if bound[0]>new_f:
            self.NextFrequency= bound[0]
            print('Frequency exceedes device''s capabilities')
        elif bound[1]<new_f:
            self.NextFrequency= bound[1]
            print('Frequency exceedes device''s capabilities')
        else:
            self.NextFrequency=new_f
        
        THzf=math.floor(new_f)
        GHzf=math.floor((new_f-THzf)*10000)
        outp1= pp.ITLA(self.handle, 0xEA, THzf, 1) # write only registers wtf
        outp2= pp.ITLA(self.handle, 0xEB, GHzf, 1)
        
        freq=outp1+outp2/10000
        #print('Next frequency[THz]: ', freq)
        return(freq)
    
    
    def frequency_jump(self, jump): # sets the next frequency given the jump in THz.
        #the mew frewuemcy is taken as the sum of the currently set frequency (fcf + FTF) with the jump
        # get current frequency
        old_f= self.frequency
        # set new frequency
        new_f= old_f[0]+jump
        self.next_frequency=new_f
        #print('Next frequency[THz]: ', freq)
        return(new_f)
        
    def current(self): # calculates the setpoint for the current to be sent to the module
        pw= self.power
        bound=self.power_lim
        print('power: ', pw)
        
        if not self.is_on():
            print('this metod can be applied only if the laser is enabled')
            return(0)
        
        # use the right map file accroding to the power set.
        if bound[0]<= pw[0]<=10:
            print('using map700 and map 1000')
            map_low=self.CalibrationFiles[0]
            map_high=self.CalibrationFiles[1]
            pw_low=bound[0]
            pw_high=10
            
        elif 10< pw[0] <=bound[1]:
            print('using map 1000 and .map 1350')
            map_low=self.CalibrationFiles[1]
            map_high=self.CalibrationFiles[2]
            pw_low=10
            pw_high=bound[1]
            
        # looking for the  closest lower frequency and the closest higher frequency
        #array=map_low['freq'].to_numpy()
        [idx_low1, idx_low2]=self.find_nearest2(map_low['freq'].to_numpy(), self.next_frequency)
        [idx_high1, idx_high2]=self.find_nearest2(map_high['freq'].to_numpy(), self.next_frequency)
        
        # interpolate the current between the two closest frequency setpoints
        current_low=self.interpolate(map_low['freq'].to_numpy()[idx_low1], map_low['freq'].to_numpy()[idx_low2], map_low['current'].to_numpy()[idx_low1], map_low['current'].to_numpy()[idx_low2], self.next_frequency)
        current_high=self.interpolate(map_high['freq'].to_numpy()[idx_high1], map_high['freq'].to_numpy()[idx_high2], map_high['current'].to_numpy()[idx_high1], map_high['current'].to_numpy()[idx_high2], self.next_frequency)
        #interpolate the two current values between the two power setpoints
        #print('current low:  ', current_low)
        #print('current high: ', current_high)
        #print('power_low:    ', pw_low)
        #print('power high    ', pw_high)
        #print('power:        ', pw[0])
        current= self.interpolate(pw_low, pw_high, current_low, current_high, pw[0])
        print('Drive Current:        ', current)
        return(current)
        
    def sled_temperature(self):
        #find the sled temperature intermpolating from teh closest grid setpoint (in frequency)
        pw= self.power
        bound=self.power_lim
        if not self.is_on():
            print('this metod can be applied only if the laser is enabled')
            return(0)
        
        # use the right map file accroding to the power set.
        if bound[0]<= pw[0]<=10:
            print('using map700 and map 1000')
            map_low=self.CalibrationFiles[0]
            map_high=self.CalibrationFiles[1]
            pw_low=bound[0]
            pw_high=10
            
        elif 10< pw[0] <=bound[1]:
            print('using map 1000 and .map 1350')
            map_low=self.CalibrationFiles[1]
            map_high=self.CalibrationFiles[2]
            pw_low=10
            pw_high=bound[1]
            
        # looking for the  closest frequency
        idx_low=self.find_nearest1(map_low['freq'].to_numpy(), self.next_frequency)
        idx_high=self.find_nearest1(map_high['freq'].to_numpy(), self.next_frequency)
        
        #print('low index: ', idx_low)
        #print('high index:', idx_high)
        
        #extrapolate the right sled temperature using the slope [C/GHz] provided by teh module
        slope=-pp.ITLA(self.handle, 0xE8, 0, 0)/10000# hoping this is not a write only...
        #print('Slope[C/GHz]: ', slope)
        sled_temp_low= map_low['sled'].to_numpy()[idx_low]+ slope*(self.next_frequency-map_low['freq'].to_numpy()[idx_low])*1000
        sled_temp_high= map_high['sled'].to_numpy()[idx_high]+ slope*(self.next_frequency-map_high['freq'].to_numpy()[idx_high])*1000
        # interpolate between the two power grid values
        #print('Low temperature:      ', sled_temp_low)
        #print('High temperature:     ', sled_temp_high)
        #print('Low power:            ', pw_low)
        #print('High power:           ', pw_high)
        #print('Power:                ', pw)
        
        sled_temp=self.interpolate(pw_low, pw_high, sled_temp_low, sled_temp_high, pw[0])
        print('Sled Temperature:      ', sled_temp)
        return(sled_temp)
        
    def sled_temperature2(self):
        #find the sled temperature intermpolating from teh closest grid setpoint (in frequency)
        pw= self.power
        bound=self.power_lim
        if not self.is_on():
            print('this metod can be applied only if the laser is enabled')
            return(0)
        
        # use the right map file accroding to the power set.
        if bound[0]<= pw[0]<=10:
            print('using map700 and map 1000')
            map_low=self.CalibrationFiles[0]
            map_high=self.CalibrationFiles[1]
            pw_low=bound[0]
            pw_high=10
            
        elif 10< pw[0] <=bound[1]:
            print('using map 1000 and .map 1350')
            map_low=self.CalibrationFiles[1]
            map_high=self.CalibrationFiles[2]
            pw_low=10
            pw_high=bound[1]
            
        [idx_low1, idx_low2]=self.find_nearest2(map_low['freq'].to_numpy(), self.next_frequency)
        [idx_high1, idx_high2]=self.find_nearest2(map_high['freq'].to_numpy(), self.next_frequency)
        
        # interpolate the current between the two closest frequency setpoints
        sled_temp_low=self.interpolate(map_low['freq'].to_numpy()[idx_low1], map_low['freq'].to_numpy()[idx_low2], map_low['sled'].to_numpy()[idx_low1], map_low['sled'].to_numpy()[idx_low2], self.next_frequency)
        sled_temp_high=self.interpolate(map_high['freq'].to_numpy()[idx_high1], map_high['freq'].to_numpy()[idx_high2], map_high['sled'].to_numpy()[idx_high1], map_high['sled'].to_numpy()[idx_high2], self.next_frequency)
        #interpolate the two current values between the two power setpoints
        # interpolate between the two power grid values
        #print('Low temperature:      ', sled_temp_low)
        #print('High temperature:     ', sled_temp_high)
        #print('Low power:            ', pw_low)
        #print('High power:           ', pw_high)
        #print('Power:                ', pw)
        
        sled_temp=self.interpolate(pw_low, pw_high, sled_temp_low, sled_temp_high, pw[0])
        print('Sled Temperature:      ', sled_temp)
        return(sled_temp)
        
    def is_filt_cont(self, idx1, idx2, dtf): # check if there is discontinuity of the filter fucntions
        # between two frequnecy grid setpoints.
        # idx1 and idx2 are suppoosed to be the indexes of the frequnecy setpoints in the .map file:
        # idx1 refers to the lower frequency
        # dtf is the dataframe which contains the calibration file
        # returns True if the function is supposed to be continuous
        
        #extract the filter1 and filter2 arrays from the dtf:
        filter1=dtf['f1'].to_numpy()
        filter2=dtf['f2'].to_numpy()
        #check condition
        out= ((filter1[idx2]<filter1[idx1])and (filter2[idx2]<filter2[idx1]))
        return(out)
        
    def filters(self): # function to calcualte the filters' temperatures
        
        pw= self.power
        bound=self.power_lim
        if not self.is_on():
            print('this metod can be applied only if the laser is enabled')
            return(0)
        
        # use the right map file accroding to the power set.
        if bound[0]<= pw[0]<=10:
            #print('using map700 and map 1000')
            map_low=self.CalibrationFiles[0]
            map_high=self.CalibrationFiles[1]
            pw_low=bound[0]
            pw_high=10
            
        elif 10< pw[0] <=bound[1]:
            #print('using map 1000 and .map 1350')
            map_low=self.CalibrationFiles[1]
            map_high=self.CalibrationFiles[2]
            pw_low=10
            pw_high=bound[1]
            
        # looking for the  closest lower frequency and the closest higher frequency
        #array=map_low['freq'].to_numpy()
        [idx_low1, idx_low2]=self.find_nearest2(map_low['freq'].to_numpy(), self.next_frequency)
        [idx_high1, idx_high2]=self.find_nearest2(map_high['freq'].to_numpy(), self.next_frequency)
        
        # calculate filters for lower power
        if self.is_filt_cont(idx_low1, idx_low2, map_low):
            #print('filter functions are continuous')
            filt1_low= self.interpolate(map_low['freq'].to_numpy()[idx_low1], map_low['freq'].to_numpy()[idx_low2], map_low['f1'].to_numpy()[idx_low1], map_low['f1'].to_numpy()[idx_low2], self.next_frequency)
            filt2_low= self.interpolate(map_low['freq'].to_numpy()[idx_low1], map_low['freq'].to_numpy()[idx_low2], map_low['f2'].to_numpy()[idx_low1], map_low['f2'].to_numpy()[idx_low2], self.next_frequency)
        
        elif self.is_filt_cont(idx_low1-1, idx_low1, map_low) and self.is_filt_cont(idx_low2, idx_low2+1, map_low):
            #print('filter functions are discontinuous')
            FILT1_low=[0,0]
            FILT2_low=[0,0]
            #fitting from below the setpoint
            FILT1_low[0]= self.interpolate(map_low['freq'].to_numpy()[idx_low1-1], map_low['freq'].to_numpy()[idx_low1], map_low['f1'].to_numpy()[idx_low1-1], map_low['f1'].to_numpy()[idx_low1], self.next_frequency)
            # fitting from above the setpoint
            FILT1_low[1]= self.interpolate(map_low['freq'].to_numpy()[idx_low2], map_low['freq'].to_numpy()[idx_low2+1], map_low['f1'].to_numpy()[idx_low2], map_low['f1'].to_numpy()[idx_low2+1], self.next_frequency)
            # keep the closest to 69 C
            filt1_low=FILT1_low[self.find_nearest1(FILT1_low, 69)]
            #print('predicted setpoints for filter 1 at low power:       ', FILT1_low)
            # now do the same for the second filter
            #fitting from below the setpoint
            FILT2_low[0]= self.interpolate(map_low['freq'].to_numpy()[idx_low1-1], map_low['freq'].to_numpy()[idx_low1], map_low['f2'].to_numpy()[idx_low1-1], map_low['f2'].to_numpy()[idx_low1], self.next_frequency)
            # fitting from above the setpoint
            FILT2_low[1]= self.interpolate(map_low['freq'].to_numpy()[idx_low2], map_low['freq'].to_numpy()[idx_low2+1], map_low['f2'].to_numpy()[idx_low2], map_low['f2'].to_numpy()[idx_low2+1], self.next_frequency)
            # keep the closest to 69 C
            filt2_low=FILT2_low[self.find_nearest1(FILT2_low, 69)]
            #print('predicted setpoints for filter 2 at low power:       ', FILT1_low)
            
        else:
            print('Don''t know what to do: the functions are discontinuous everywhere... ')
            filt1_low=0
            filt2_low=0
        
        # calculate filters for higher power
        if self.is_filt_cont(idx_high1, idx_high2, map_high):
            #print('filter functions are continuous')
            filt1_high= self.interpolate(map_high['freq'].to_numpy()[idx_high1], map_high['freq'].to_numpy()[idx_high2], map_high['f1'].to_numpy()[idx_high1], map_high['f1'].to_numpy()[idx_high2], self.next_frequency)
            filt2_high= self.interpolate(map_high['freq'].to_numpy()[idx_high1], map_high['freq'].to_numpy()[idx_high2], map_high['f2'].to_numpy()[idx_high1], map_high['f2'].to_numpy()[idx_high2], self.next_frequency)
        
        elif self.is_filt_cont(idx_high1-1, idx_high1, map_high) and self.is_filt_cont(idx_high2, idx_high2+1, map_high):
            #print('filter functions are discontinuous')
            FILT1_high=[0,0]
            FILT2_high=[0,0]
            #fitting from below the setpoint
            FILT1_high[0]= self.interpolate(map_high['freq'].to_numpy()[idx_high1-1], map_high['freq'].to_numpy()[idx_high1], map_high['f1'].to_numpy()[idx_high1-1], map_high['f1'].to_numpy()[idx_high1], self.next_frequency)
            # fitting from above the setpoint
            FILT1_high[1]= self.interpolate(map_high['freq'].to_numpy()[idx_high2], map_high['freq'].to_numpy()[idx_high2+1], map_high['f1'].to_numpy()[idx_high2], map_high['f1'].to_numpy()[idx_high2+1], self.next_frequency)
            # keep the closest to 69 C
            filt1_high=FILT1_high[self.find_nearest1(FILT1_high, 69)]
            #print('predicted setpoints for filter 1 at high power:      ', FILT1_high)
            
            #now do the same for filter 2
            #fitting from below the setpoint
            FILT2_high[0]= self.interpolate(map_high['freq'].to_numpy()[idx_high1-1], map_high['freq'].to_numpy()[idx_high1], map_high['f2'].to_numpy()[idx_high1-1], map_high['f2'].to_numpy()[idx_high1], self.next_frequency)
            # fitting from above the setpoint
            FILT2_high[1]= self.interpolate(map_high['freq'].to_numpy()[idx_high2], map_high['freq'].to_numpy()[idx_high2+1], map_high['f2'].to_numpy()[idx_high2], map_high['f2'].to_numpy()[idx_high2+1], self.next_frequency)
            # keep the closest to 69 C
            filt2_high=FILT2_high[self.find_nearest1(FILT2_high, 69)]
            #print('predicted setpoints for filter 2 at high power:      ', FILT1_high)
            
        else:
            print('Don''t know what to do: the functions are discontinuous everywhere... ')
            filt1_high=0
            filt2_high=0
        
        # now interpolate the value of the filter at the desired power setpoint.
        filt1=self.interpolate(pw_low, pw_high, filt1_low, filt1_high, pw[0])
        filt2=self.interpolate(pw_low, pw_high, filt2_low, filt2_high, pw[0])
        #print('Filter1 low temperature setpoint:   ', filt1_low)
        #print('Filter1 high temperature setpoint:  ', filt1_high)
        print('Filter1 temperature setpoint:       ', filt1)
        #print('Filter2 low temperature setpoint:   ', filt2_low)
        #print('Filter2 high temperature setpoint:  ', filt2_high)
        print('Filter2 temperature setpoint:       ', filt2)
        
        return([filt1, filt2])
        
        
    def find_nearest2(self, array, value):
        #array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        if array[idx]>value:
            idx1=idx-1
            idx2=idx
        elif array[idx]<value:
            idx1=idx
            idx2=idx+1
        else: 
            print('grid matching')
            idx1=-1
            idx2=-1
        
        return ([idx1, idx2])
    
    def find_nearest1(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return (idx)
    
    def interpolate(self, x1, x2, y1, y2, x):
        y= y1+(x-x1)*((y2-y1)/(x2-x1))
        return(y)
        
    def CleanJump(self, jump, trigger=True):
        
        if not self.is_on():
            print('turn laser on...')
            self.on()
        self.LN=1
        self.wait4NOP()
        # set next frequnecy
        self.frequency_jump(jump)
        # calculate next sled_temperature and drive current and write in the appropriate registers
        
        current=pp.ITLA(self.handle, 0xE9, self.current()*10, 1)
        sled_temp=pp.ITLA(self.handle, 0xEC, self.sled_temperature2()*100, 1)
        filters=self.filters() 
        # upload next setpoints to memory
        pp.ITLA(self.handle, 0xED, 1, 1)
        #self.wait4NOP()
        #calculate filter 1
        pp.ITLA(self.handle, 0xED, 1, 1)
        #self.wait4NOP()
        #calcualte filter 2
        pp.ITLA(self.handle, 0xED, 1, 1)
        #self.wait4NOP()
        #execute jump!
        pp.ITLA(self.handle, 0xED, 1, 1)
        
        if trigger==True:
            self.trig.write(5.)
            time.sleep(self.idle_time)
            self.trig.write(0.)
            
    
    
        
    def f2w(self, f):# takes frequency in THz and gives back nm
        w=math.floor((299792458/f)*100)/100000# fancy way to keep only 9 digits
        print(w,f)
        return(w)
        
    def w2f(self, w):# takes wv in nm and gives back frequency in THz
        f=math.floor((299792458/w)*100)/100000# fancy way to keep only 9 digits
        print(w,f)
        return(f)
    
    
    
    
    
   
        
        
    
        
    
            
    
       
       

    
    
    
    
            
           
    def status(self):
        status= pp.ITLA(self.handle, pp.REG_Dlstatus, 0,0)
        return(status)
       
    
    
       
   
   