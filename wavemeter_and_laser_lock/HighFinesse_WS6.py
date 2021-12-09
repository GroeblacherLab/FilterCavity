# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 14:52:54 2016

@author: awallucks
"""
from ctypes import *

import time
import sys

from glablibraries.drivers.wlm_constants import *


class WLMError(Exception):
    def __init__(self, messsage):
        Exception(self, message)
                
class Wavelengthmeter:
    """API for the HighFinesse WS6 wavelengthmeter"""
    
    def __init__(self):
        #load the .dll file
        self.dll = windll.wlmData
            
    def StartWLM(self):
        """Make connection to wavemeter"""
        res = self.dll.ControlWLMEx(cCtrlWLMHide+cCtrlWLMWait, 0, 0, 10000, 1)       #cCtrlWLMHide+

        if res>flServerStarted:
            print('WM not found')
        if res<=flServerStarted:
            print('Started successfully')

    def CheckForWLM(self):        
        Inst = self.dll.Instantiate(cInstCheckForWLM, 0, 0, 0)
        print(Inst)        
        if Inst == 0:
            print('WLM not found')
        if Inst < 0:
            print('Success')
        
        
    def CloseWLM(self):
        ck = self.dll.ControlWLMEx(cCtrlWLMExit, 0, 0, 0, 0)
        print(ck)


    def ResetWaitEvent(self):
        ck = self.dll.Instantiate(cInstNotification, cNotifyRemoveWaitEvent, 0, 0)
        print(ck)
         
    def InstReturn(self):
        ck = self.dll.Instantiate(cInstReturnMode, 1, 0, 0)
        print(ck)
    
    
    #WaitForWLM Event - NOT WORKING YET
    def InstWait(self):
        ck = self.dll.Instantiate(cInstNotification, cNotifyInstallWaitEvent, 5000, 0)
        print(ck)

    def WaitForWLM(self):
         """Wait until new measurement is ready. Also see WaitForWLM_new"""
         a = c_double()
         b = c_float()
         
         Mode = c_int(42)   #cmigetwavelength1 = 42
         
         chk = self.dll.WaitForWLMEvent(byref(Mode), byref(a), byref(b))

         #print (ctypes.cast(ctypes.addressof(a), ctypes.py_object).value)
         return chk

    def WaitForWLM_new(self):
         """self.dll.WaitForWLMEvent should save the wavelength in DblVal. This does not work currently. 
         No idea how to get it. Have to call getWL after WaitForWLM_new to read the value"""
         Mode = c_long(42)   #cmigetwavelength1 = 42
         IntVal = c_long()
         DblVal = c_double()
  
         for r in range(0, 50):
             chk = self.dll.WaitForWLMEvent(addressof(Mode), byref(IntVal), byref(DblVal))
             print(DblVal.value)
         #print (ctypes.cast(ctypes.addressof(b), ctypes.py_object).value)
         return chk


#Start Measurement        
    def GetOp(self):
        Op = self.dll.GetOperationState()
        return Op
        
    def StartOp(self):
        Op = self.dll.Operation(cCtrlStartMeasurement)
        return Op
        
    def StopOp(self):
        Op = self.dll.Operation(cCtrlStopAll)
        return Op
                        
    def getWL(self):
        #Ctypes assumes output values of the called funtions to be c_int.
        #Set to c_double with .restype if double output is expected (e.g. wavelength, frequency etc)
        
        GetWavelength = self.dll.GetWavelength
        GetWavelength.restype = c_double
        WL = GetWavelength(0)
        return WL
                
    def getFreq(self):
        GetFrequency = self.dll.GetFrequency
        GetFrequency.restype = c_double
        Freq = GetFrequency(0)
        return Freq

        
if __name__ == '__main__': 
    """Usage example"""
    w = Wavelengthmeter()
    w.StartWLM()
    #w.InstWait()
    #w.InstReturn()
    #w.StartOp()
    time.sleep(0.5)

    print(w.getWL())
    #time.sleep(0.5)
    #w.StopOp()
    