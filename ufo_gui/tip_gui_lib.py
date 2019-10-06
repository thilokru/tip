# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:59:44 2015

@author: hrotzing
"""
from threading import Thread
from time import sleep

from cPickle import loads
import numpy as np

import socket
#import argparse
#import ConfigParser
from PyQt4.QtCore import QObject, pyqtSignal

class DATA(object):
    REMOTEHOST = "129.13.93.74"
    REMOTEPORT = 9999
    UpdateInterval = 1
    DEBUG = False
    wants_abort = True


def logstr(logstring):
    #if data.DEBUG:
    print(str(logstring))
    
class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class remote_client(object):
    def __init__(self,DATA):
        self.data = DATA
        host = DATA.REMOTEHOST
        port = DATA.REMOTEPORT
        self.setup(host,port)
        
    def setup(self,HOST,PORT):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to server and send data
            self.sock.connect((HOST, PORT))
            if self.data.DEBUG:
                logstr("connected to %s port %d\n"%(HOST,PORT))
        except:
            raise

    def send(self,send_cmd):
        self.sock.send(send_cmd + "\n")
        
    def recv(self):
        # Receive data from the server and shut down
        rdata = self.sock.recv(819200)
        string = rdata
        #arr= pickle.loads(string)
        #logstr(string)
        return string
    
    def close(self):
        self.sock.close()
        
class AcquisitionThread(Thread,QObject):
    """ Acquisition loop. This is the worker thread that retrieves info ...
    """
    update_sig = pyqtSignal()
    
    def __init__(self,DATA):
        Thread.__init__(self)
        QObject.__init__(self)
        DATA.wants_abort = False
        self.data = DATA

        
    def setup_acquire_from_remote(self):
        self.rc=remote_client(self.data)
        
    def acquire_from_remote(self,cmd,delay=0):
        self.rc.send(cmd)
        sleep(delay)
        return self.rc.recv()

    def update_remote(self,cmd):
        self.rc.send(str("set "+cmd))

    def stop_remote(self):
        self.rc.send("EXIT\n")
        self.rc.close()
    def process(self, image):
        """ Spawns the processing job.
        """
        try:
            if self.processing_job.isAlive():
                self.display("Processing to slow")
                return
        except AttributeError:
            pass
        self.processing_job.start()
    def display(self,message):
        print message

    def run(self):
        """ Runs the acquisition loop.
        """

        self.setup_acquire_from_remote()

        #self.T_arr[:]=float(self.acquire_from_remote("T"))*1000
        #self.Heat_arr[:]=float(self.acquire_from_remote("HEAT"))*1e6
        #self.pidE_arr[:]=float(self.acquire_from_remote("PIDE"))*1e6

        self.display('Start')
        
        #axnames = loads(self.acquire_from_remote("get/therm/names"),delay=.4)
        
                
        while not self.data.wants_abort:
            # get state
            try:
                newT = loads(self.acquire_from_remote("get/therm/:/temp/hist",delay=1.8))
                newtimes = loads(self.acquire_from_remote("get/therm/:/time/hist",delay=1.8))
                for i in range(len(self.data.times)):
                    self.data.T[i] = np.append(self.data.T[i],newT[i])
                    self.data.times[i] = np.append(self.data.times[i],newtimes[i])
                    self.data.T[i]= self.data.T[i][np.unique(self.data.times[i],return_index=True)[1]]
                    self.data.times[i] = self.data.times[i][np.unique(self.data.times[i],return_index=True)[1]]
                    self.data.T[i]= self.data.T[i][np.where(self.data.times[i]!=0)]
                    self.data.times[i] = self.data.times[i][np.where(self.data.times[i]!=0)]
                    
                self.update_sig.emit()
                
                sleep(self.data.UpdateInterval)
            except pickle.UnpicklingError:
                pass
            
        #self.stop_remote()
        self.display('Connection stopped')
        
"""
###
###
# not sure ...
class Bridge(object):
    " Object to display on the conifiguration
    "
    Bridge = Str("AVS 47",label="Resistance Bridge")
    #Delay = Float()
    Channel = Enum("0","1","2","3","4","5","6","7",)
    Excitation = Enum("NONE", "3uV", "10uV", "30uV", "100uV", "300uV", "1mV", "3mV")
    Range = Enum("2R","20R","200R","2K","20K","200K","2M")
    AutoRange = Bool()
    Update = Button("Update")
    
    view = View(Group(
        Item('Bridge',style='readonly'),
        #Item('Delay',label="Delay"),
        Item('Channel',label="Channel"),
        Item('Range',label="Range"),
        Item('Excitation',label="Excitation"),
        Item('AutoRange',label="Autorange")
    ),
        Item("Update",label="Update all")
        )

    def _Update_fired(self):
        " Callback of the update button.
        "
        range_map_r= {0:'NONE', 1:'2R', 2:'20R', 3:'200R', 4:'2K', 5:'20K', 6:'200K', 7:'2M'}
        exc_map_r=  {0:"NONE", 1:"3uV", 2:"10uV", 3:"30uV", 4:"100uV", 5:"300uV", 6:"1mV", 7:"3mV"}
        channel_map_r= {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7"}
        
        rc = remote_client()
        rc.send("get Bridge Range")
        self.Range=range_map_r.get(int(rc.recv()))
        
        rc.send("get Bridge excitation")
        self.Excitation=exc_map_r.get(int(rc.recv()))
        
        rc.send("get Bridge channel")
        self.Channel = channel_map_r.get(int(rc.recv()))
        rc.close()
        
    def _AutoRange_changed(self):
        #range_map= {'NONE':0, '2R':1, '20R':2, '200R':3, '2K':4, '20K':5, '200K':6, '2M':7}
        rc = remote_client()  
        #rc.send("set BRange "+str(range_map.get(self.Range)))
        if AutoRange:
            rc.send("set Bridge Range "+str(10))
        else:
            # for now AutoRange is not really implemented ;-)
            rc.send("set Bridge Range "+str(10))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()
        
    def _Range_changed(self):
        range_map= {'NONE':0, '2R':1, '20R':2, '200R':3, '2K':4, '20K':5, '200K':6, '2M':7}
        rc = remote_client()  
        #rc.send("set BRange "+str(range_map.get(self.Range)))
        rc.send("set Bridge Range "+str(range_map.get(self.Range)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()

    def _Excitation_changed(self):
        exc_map= {"NONE":0, "3uV":1, "10uV":2, "30uV":3, "100uV":4, "300uV":5, "1mV":6, "3mV":7}
        rc = remote_client()  
        rc.send("set Bridge excitation "+str(exc_map.get(self.Excitation)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()

    def _Channel_changed(self):
        channel_map= {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7}
        rc = remote_client()  
        rc.send("set Bridge channel "+str(channel_map.get(self.Channel)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()
"""