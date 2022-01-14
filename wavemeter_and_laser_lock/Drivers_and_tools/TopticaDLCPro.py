"""
Created on (2020)

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Driver implementing some useful commands for Toptical DLC Pro controllers.
using the Python builtin Telnet library and some string formatting.

Needs to have the qcodes repository cloned (https://github.com/QCoDeS/Qcodes/tree/master/qcodes)

"""

from qcodes.instrument.base import Instrument, InstrumentBase
from qcodes.logger.instrument_logger import get_instrument_logger
from qcodes.utils.validators import Numbers,Enum,MultiType

from .TelnetInstrument import TelnetInstrument


class TopticaDLCPro(TelnetInstrument):

    def __init__(self, name, address, port=1998, **kwargs):
        super().__init__(name, address, port, **kwargs)

        self.minimum_wavelength = float(self.ask('laser1:ctl:wavelength-min'))
        self.maximum_wavelength = float(self.ask('laser1:ctl:wavelength-max'))

        self.add_parameter(name='wavelength',
                         label='Laser wavelength setting',
                         unit='nm',
                         get_cmd='laser1:ctl:wavelength-act',
                         set_cmd='laser1:ctl:wavelength-set {:f}',
                         get_parser=float,
                         vals=Numbers(min_value=self.minimum_wavelength,
                                      max_value=self.maximum_wavelength))

        self.add_parameter(name='piezo_voltage_setting',
                         label='Set piezo voltage',
                         unit='V',
                         get_cmd='laser1:dl:pc:voltage-set',
                         set_cmd='laser1:dl:pc:voltage-set {:f}',
                         get_parser=float,
                         vals=Numbers(min_value=float(self.ask('laser1:dl:pc:voltage-min')),
                                      max_value=float(self.ask('laser1:dl:pc:voltage-max'))))

        self.add_parameter(name='piezo_voltage_actual',
                         label='Actual piezo voltage output',
                         unit='V',
                         get_cmd='laser1:dl:pc:voltage-act',
                         get_parser=float,
                         set_cmd=False)

        self.add_parameter(name='scan_start',
                         label='Wavelength scan start',
                         unit='nm',
                         get_cmd='laser1:ctl:scan:wavelength-begin',
                         set_cmd='laser1:ctl:scan:wavelength-begin {:f}',
                         get_parser=float,
                         vals=Numbers(min_value=self.minimum_wavelength,
                                      max_value=self.maximum_wavelength))
        self.add_parameter(name='scan_stop',
                         label='Wavelength scan stop',
                         unit='nm',
                         get_cmd='laser1:ctl:scan:wavelength-end',
                         set_cmd='laser1:ctl:scan:wavelength-end {:f}',
                         get_parser=float,
                         vals=Numbers(min_value=self.minimum_wavelength,
                                      max_value=self.maximum_wavelength))
        self.add_parameter(name='scan_speed',
                         label='Wavelength scan speed',
                         unit='nm',
                         get_cmd='laser1:ctl:scan:speed',
                         set_cmd='laser1:ctl:scan:speed {:f}',
                         get_parser=float,
                         vals=Numbers(min_value=float(self.ask('laser1:ctl:scan:speed-min')),
                                      max_value=float(self.ask('laser1:ctl:scan:speed-max'))))


    def ask_raw(self,cmd):
        cmd_raw = "(param-ref '{})".format(cmd)
        return super().ask_raw(cmd_raw)

    def write_raw(self,cmd):
        cmd_raw = "(param-set! '{})".format(cmd)
        super().write_raw(cmd_raw)

    def exec(self,cmd):
        cmd_raw = "(exec '{}".format(cmd)
        super().write_raw(cmd_raw)

    def scan_wavelength(self,start=1500,stop=1550,speed= 5.0,extra=1.0):
        self.scan_start.set(start)
        self.scan_stop.set(stop)
        self.scan_speed.set(speed)
        self.write('laser1:ctl:scan:trigger:output-enabled #t')
        self.write('laser1:ctl:scan:trigger:output-threshold {:f}'.format(self.scan_start.get() + extra))
        self.exec('laser1:ctl:scan:start')

    def get_laser_state(self):
        self.states = {'-100' : "ERROR", \
                    '-8' : "Motor referencing and FLOW initialization in progress", \
                    '-7' : "FLOW initialization in progress", \
                    '-6' : "Motor not referenced, yet", \
                    '-5' : "Motor referencing in progress", \
                    '-4' : "Motor referenced", \
                    '-3' : "Drift compensation in progress", \
                    '-2' : "FLOW optimization in progreress", \
                    '-1' : "SMILE optimization in progreress", \
                    '0'  : "Idle/Stopped", \
                    '1'  : "Target set wavelength is about to be reached", \
                    '2'  : "Starting motor scan", \
                    '3'  : "Scan in progress", \
                    '4'  : "Restarting scan", \
                    '5'  : "Paused", \
                    '6'  : "Remotely controlled"}

        msg = self.ask_raw('laser1:ctl:state')
        return msg
        

