#!/usr/bin/env python

"""
Pfeiffer DPG 109 Display controller for digital vacuum gauges
"""
#import sys
#import time
import serial
import devices.pfeiffer_vacuum_protocol as pvp

from lib.tip_config import config

def driver(name):
    drv  =  Pfeiffer_DPG109(name)
    drv.setup_device(serial_dev = config[name]['address'])
    return drv

class Pfeiffer_DPG109(object):
    
    def __init__(self,name):
        self.channel = 0
    
    def setup_device(self,serial_dev = "/dev/ttyUSB0"):
        self.con = serial.Serial(serial_dev, timeout=1)
    
    def get_idn(self):
        return( "" )

    def set_channel(self,channel):
        self.channel = channel

    def get_pressure(self):
        try:
            p = pvp.read_pressure(self.con, self.channel)
            # print(f'Pressure {p:.3e} mbar')
            
            # sometimes the gauges return an underrange value = 0
            if p == 0: 
                return None
            else:
                return p
            
        except ValueError:
            # value is e.g. raised when no gauge is connected
            # this way we can still ask vor a value and then live with a None response
            return None

    def get_gauge_type(self,channel):
        return pvp.read_gauge_type(self.con,channel)

    def close(self):
        pass

if __name__ == "__main__":
    
    dpg=Pfeiffer_DPG109("DPG109")
    dpg.setup_device()
    for a in range(0,9): 
        print(a)
        try:
            dpg.set_channel(a)
            p = dpg.get_pressure()
            print(f"type {dpg.get_gauge_type(a)}")
        except ValueError:
            # no response from the gauge -> probably nothing connected
            pass
    
