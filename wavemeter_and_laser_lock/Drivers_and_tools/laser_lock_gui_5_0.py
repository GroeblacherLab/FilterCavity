''' 
Created on 

@author: A.Wallucks

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

The GUI window creation and the remote lock access to the GUI and laser lock.
Used in laser_lock_5_0

'''


import time

import pyqtgraph as pg
import numpy as np
from PyQt5 import QtCore, QtGui
from glablibraries.gui.laser_lock_gui_3_0 import Ui_Dialog


class laserLockGUI(QtGui.QDialog):
    def __init__(self, lock, parent=None):
        """
        Locking GUI for a laser
        """
        # QtGui.QDialog.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
        super(laserLockGUI, self).__init__(parent)
        self.lock = lock

        self.speed_of_light = 299792458

        # Set up the user interface from Designer.
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        #add lasers to combobox
        available_lasers = self.lock.get_available_lasers()
        self.ui.comboBox.addItems(available_lasers)

        #self.ui.lock_btn.clicked.connect(self.startstop)
        self.ui.horizontalSlider.valueChanged.connect(self.slider_update)
        self.ui.spinBox.valueChanged.connect(self.spin_box_update)
        self.ui.btn_start.clicked.connect(self.start_lock)
        self.ui.btn_pause.clicked.connect(self.pause_lock)
        self.ui.btn_stop.clicked.connect(self.stop_lock)
        
        self.ui.btn_pause.setEnabled(False)
        self.ui.btn_stop.setEnabled(False)
        
        pg.setConfigOption('background', 0.3)
        pg.setConfigOption('foreground', 'w')

        self.lock_wdg = pg.PlotWidget()
        self.lock_wdg.showAxis('bottom', show=False)
        self.ui.plot_placeholder.addWidget(self.lock_wdg, 0,0,1,1)
        self.lock_wdg.setMinimumSize(QtCore.QSize(500, 10))

        self.setpt = self.lock_wdg.plot(pen={'color': 'y', 'width': 2})
        self.lockplot = self.lock_wdg.plot(pen={'color': 'r', 'width': 2})
        self.pos_margin = self.lock_wdg.plot(pen={'color': 'w', 'width': 1})
        self.neg_margin = self.lock_wdg.plot(pen={'color': 'w', 'width': 1})

        self.lock_setpoint = 0. #nm
        self.lock_input_wavelength = 0. #nm
        self.lock_detuning = 0.
        self.lock_detuning_wo_slider = 0.
        self.slider_range = 1.
        self.ui.spinBox.setValue(self.slider_range)

        self.max_lock_track_len = 20
        self.lock_track_len = 0
        self.lock_track_t = np.array([])
        self.lock_track_wl = np.array([])

        self.enable_gui(True)
        #timer to update the lock instead of a loop (keeps the GUI responsible during locking, every timeout the timer will call the function self.update_lock)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_lock)
        self.timer.setSingleShot(True)
        
        self.is_running = False

    def spin_box_update(self):
        self.lock_detuning_wo_slider = self.lock_detuning
        self.ui.horizontalSlider.setValue(0)
        self.slider_range = float( self.ui.spinBox.value() )

    def slider_update(self):
        """
        Slider to move the lock_setpt during the locking
        to the right: higher freq. (blue detuning)
        Max range taken from box on right side
        clicking on the bar adjusts in steps of range/100
        """
        slider_val = float(self.ui.horizontalSlider.value())
        self.lock_detuning = round(self.lock_detuning_wo_slider + self.slider_range*slider_val/1000, 3)
        
        self.ui.det_lineedit.setText(str(self.lock_detuning))

        self.lock_setpoint = 1 / ((1 / self.lock_input_wavelength) + (self.lock_detuning / self.speed_of_light))  #all in GHZ & nm

        self.lock.change_pid_setpt(self.lock_setpoint)

    def enable_gui(self, ebl, clearplot = True):
        
        if clearplot:
            self.lock_track_len = 0
            self.lock_track_t = np.array([])
            self.lock_track_wl = np.array([])
            self.ui.horizontalSlider.setValue(0)
    
            self.setpt.clear()
            self.lockplot.clear()
            self.pos_margin.clear()
            self.neg_margin.clear()

        
        self.ui.btn_start.setEnabled(ebl)
        self.ui.btn_pause.setEnabled(not ebl)
        self.ui.btn_stop.setEnabled(not ebl)
        self.ui.comboBox.setEnabled(ebl)
        self.ui.wl_lineedit.setEnabled(ebl)
        self.ui.det_lineedit.setEnabled(ebl)
        self.ui.horizontalSlider.setEnabled(not ebl)
        self.ui.spinBox.setEnabled(not ebl)
        pg.QtGui.QApplication.processEvents()

    def plot_wavelength_track(self):
        self.lockplot.setData(self.lock_track_t, self.lock_track_wl)

        #Draw the setpt and the 10 MHz margins
        neg_wl_margin = (1/((1/(self.lock_setpoint*1e-9)) - (1e7/self.speed_of_light)))*1e9
        pos_wl_margin = (1 / ((1 / (self.lock_setpoint * 1e-9)) + (1e7/self.speed_of_light))) * 1e9
        self.setpt.setData(self.lock_track_t, self.lock_setpoint + np.zeros(self.lock_track_len))
        self.pos_margin.setData(self.lock_track_t, neg_wl_margin + np.zeros(self.lock_track_len))
        self.neg_margin.setData(self.lock_track_t, pos_wl_margin + np.zeros(self.lock_track_len))

    def start_lock(self):
        
        laser = self.ui.comboBox.currentText()
        if laser == '':
            print("Select laser")
            return 0

        self.lock_input_wavelength = float( self.ui.wl_lineedit.text() )
        self.lock_detuning_wo_slider = float( self.ui.det_lineedit.text() )
        self.lock_setpoint = round( 1/((1/self.lock_input_wavelength) + (self.lock_detuning_wo_slider/self.speed_of_light)) , 5)

        self.lock.initialize_lock(laser, self.lock_setpoint)

        if self.lock_setpoint < self.lock.laser.wl_min or self.lock_setpoint > self.lock.laser.wl_max:
            print("Check wavelength")
            return 0

        print(f"Starting Lock for {laser} with setpt {self.lock_setpoint} nm")
        self.enable_gui(False, clearplot = True)
        
        self.lock.set_coarse_wavelength(self.lock_setpoint)

        #coarse wavelength sucessfully set
        self.start_time = time.time()
        self.timer.setInterval(int(float(self.ui.update_lineedit.text())*1000))  # in millisec
        self.timer.start() 
        print('timer started')
        
        self.is_running = True
        
        return 1

    def update_lock(self):

        feedback_val, wl = self.lock.update_piezo((time.time()-self.start_time))
        
        self.timer.start() #because of the singleShot
        self.ui.out_label.setText(f"Out: {feedback_val:.1f} V")
        self.lock_track_wl = np.append(self.lock_track_wl, wl)
        self.lock_track_t = np.append(self.lock_track_t, time.time() - self.start_time)

        if self.lock_track_len > self.max_lock_track_len:
            self.lock_track_t = np.delete(self.lock_track_t, 0)
            self.lock_track_wl = np.delete(self.lock_track_wl, 0)
        else:
            self.lock_track_len += 1

        self.plot_wavelength_track()
        


    def stop_lock(self):
        self.timer.stop()
        self.lock.terminate_lock()
        print('timer stopped')
        self.ui.out_label.setText(f"Out: 0 V")
        self.enable_gui(True, clearplot = True)
        
        self.is_running = False

    def pause_lock(self):
        self.timer.stop()
        self.lock.pause_lock()
        print('timer stopped')

        self.enable_gui(True, clearplot = False)
        
        self.is_running = False
    
    def get_is_runnning_console(self):
        return self.is_running
    
class remote_lock_access:
    """
    remote access to the laser lock
    Here most of the function mimic a click on the mouse to the GUI, so the laser lock need to running with the GUI open

    """
    
    def __init__(self,laser_lock,laser_lock_gui):
        self.laser_lock = laser_lock
        self.laser_lock_gui = laser_lock_gui

    def set_wavelength_setpoint(self,wavelength_nm):
        self.laser_lock_gui.ui.wl_lineedit.setText(str(wavelength_nm))
        
    def remote_start(self):
        self.laser_lock_gui.ui.btn_start.clicked.emit()

    def remote_stop(self):
        self.laser_lock_gui.ui.btn_stop.clicked.emit()
        
    def get_is_running(self):
        return self.laser_lock_gui.ui.btn_stop.isEnabled()
        
    def remote_pause(self):
        self.laser_lock_gui.ui.btn_pause.clicked.emit()
        
    def get_wavelength_setpoint(self):
        return float(self.laser_lock_gui.ui.wl_lineedit.text())
    
    def set_detuning(self,detuning_GHz):
        """
        Use to set the detuning prior to starting the lock
        """
        self.laser_lock_gui.ui.det_lineedit.setText(str(detuning_GHz))
        
    def get_detuning(self):
        return float(self.laser_lock_gui.ui.det_lineedit.text())
    
    def change_detuning(self,detuning):
        """
        Use to set the detuning while laser lock is already running (limited range!)
        """
        self.laser_lock_gui.lock_detuning = detuning
        
        self.laser_lock_gui.ui.det_lineedit.setText(str(self.laser_lock_gui.lock_detuning))

        self.laser_lock_gui.lock_setpoint = 1 / ((1 / self.laser_lock_gui.lock_input_wavelength) + (self.laser_lock_gui.lock_detuning / self.laser_lock_gui.speed_of_light))  #all in GHZ & nm

        self.laser_lock.change_pid_setpt(self.laser_lock_gui.lock_setpoint)
        
        
        
    def get_wavelength(self):
        if len(self.laser_lock_gui.lock_track_wl)==0:
            return None
        return self.laser_lock_gui.lock_track_wl[-1]    

    def snapshot(self):
        snapshot = {}
        snapshot['current_wavelength'] = self.get_wavelength()
        snapshot['wavelength_setpoint'] = self.get_wavelength_setpoint()
        snapshot['detuning'] = self.get_detuning()
        snapshot['running'] = self.get_is_running()
        return snapshot
    
    def get_is_running_remote(self):
        return self.laser_lock_gui.get_is_runnning_console()