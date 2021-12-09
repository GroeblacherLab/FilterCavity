''' 
created on 2020

@authors: B.J.Hensen

BSD 3-Clause License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Driver for a 1xN optical switch from Sercalo

'''

import serial
import logging
import math

WRITE_MESSAGE_PRE = b'\xEF\xEF'
READ_MESSAGE_PRE = b'\xfe\xfe'


class SercaloSwitch():
    """
    Driver for:
    Sercalo RSC Coaxial Fiber Optic 1xN Switch
    with FTDI TTL-232R-5V-WE USB to TTL UART cable
    
    Requirements: 
    - USB to serial port driver https://www.ftdichip.com/Drivers/VCP.htm
    - pyserial (conda install pyserial)

    example usage:
    
    #import logging
    #logging.getLogger().setLevel('DEBUG')
    
    from Sercalo_1xN_switch import SercaloSwitch

    sw = SercaloSwitch('COM4')
    sw.get_product_info()
    sw.get_channel()
    sw.set_channel(3)
    sw.get_channel()
    sw.reset()

    """



    def __init__(self,com_port, timeout=1, number_of_channels=8):
        self.com_port = com_port
        self.timeout=timeout
        self.number_of_channels = number_of_channels
        self.connect()
        
    def connect(self):
        logging.debug(f'Opening com port {self.com_port}')
        self.ser =  serial.Serial(self.com_port,115200, timeout=self.timeout) 

    def get_product_info(self):
        product_info_m = WRITE_MESSAGE_PRE + b'\x03\xFF\x01\xE1'
        data,_ = self._write_and_read(product_info_m)
        vendor = data[0:10].decode('ascii').strip(';')
        s_type = data[10:20].decode('ascii').strip(';')
        hw_maj = int(data[21])
        hw_min = int(data[22])
        fw_maj = int(data[23])
        fw_min = int(data[24])
        pd_YY= int(data[25])
        pd_yy= int(data[26])
        pd_MM= int(data[27])
        pd_DD= int(data[28])
        sn = data[29:].decode('ascii').strip(';')
        print(f' Vendor: {vendor},\
               \n type {s_type}, \
               \n version {hw_maj:d}.{hw_min:d},\
               \n firmware {fw_maj:d}.{fw_min:d}, \
               \n production date {pd_YY:d}{pd_yy:d}-{pd_MM:d}-{pd_DD:d}, \
               \n s/n {sn}')

    def get_channel(self):
        get_channel_m = WRITE_MESSAGE_PRE + b'\x03\xFF\x02\xE2'
        data,_ = self._write_and_read(get_channel_m)
        return int(data[0])

    def set_channel(self,channel):
        channel=int(channel)
        if channel < 1 or channel > self.number_of_channels:
            logging.error(f'Invalid channel {channel}.')
            return
        ch_m = b'\x04\xFF\x04' + bytes(channel.to_bytes(1,'big'))
        checksum = self._get_checksum(WRITE_MESSAGE_PRE+ch_m)
        set_channel_m = WRITE_MESSAGE_PRE + ch_m + bytes(checksum.to_bytes(1,'big'))
        _,error = self._write_and_read(set_channel_m)
        return (error == 0)

    def reset(self):
        reset_m = WRITE_MESSAGE_PRE + b'\x03\xFF\x03\xE3'
        _,error = self._write_and_read(reset_m)
        return (error == 0)

    def close(self):
        self.ser.close()

    def _write_and_read(self,message):
        #to send command to the switch as messages
        if self.ser.is_open:
            ser=self.ser
            logging.debug(f'Sending message {message}')
            ser.write(message)

            r=ser.read(3)
            if r[:2]==READ_MESSAGE_PRE:
                ret_size = r[2]
                ret=ser.read(ret_size)
                logging.debug(f'Reading {ret_size} bytes')
            elif r == b'':
                logging.error('Nothing returned')
                return None
            else:
                logging.error(f'Unexpected return {r} clearing buffer')
                ret = ser.readline()
                logging.debug(f'buffer content {ret}')
                return None
        else:
            logging.error('Serial port not open')

        logging.debug(f'Received message {ret}')

        address = ret[0]
        command = ret[1]
        error = ret[2]
        data = ret[3:-1]
        checksum = ret[-1]

        if self._get_checksum(r+ret[:-1]) != checksum:
            logging.error('Communication error: failed checksum')
        else:
            logging.debug('Checksum ok')

        self._check_error(error)
        return data,error


    def _check_error(self,error):
        if error == 0:
            logging.debug('No error')
        elif error == 1:
            logging.error('Device error: Invalid command')
        elif error == 2:
            logging.error('Device error: Invalid paramter')
        elif error == 3:
            logging.error('Device error: Command fail')
        elif error == 4:
            logging.error('Device error: Checksum error')

    def _get_checksum(self,m):
        sum_m = sum(m)
        min_size = int(math.log(sum_m,2))+2
        return sum_m.to_bytes(min_size,'big')[-1]

