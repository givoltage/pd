#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import Pyro4
import sys,os,time

from DOSlib.application import Application
from DOSlib.discovery import discoverable
from DOSlib.util import dos_parser
from DOSlib.advertise import Seeker

exptime = float(sys.argv[1])
max_led = 2
max_dc = 5
flux_goal = 25000 #Number of counts that want to reach
duty_cycles = [5]
led_currents = [0.5]
data_dir = "/data/fvc/"

#Identify the Applications
role1 = 'ILLUMINATOR'
role2 = 'FVC'
role3 = 'PC0'
led = None
fvc = None
pc0 = None

s = Seeker('-dos-','DOStest')
while led == None:
    s.seek()
    if role1 in s.devices:
        led = Pyro4.Proxy(s.devices[role1]['pyro_uri'])
        print('ILLUMINATOR connected')
    else:
        print('Not connecting to the ILLUMINATOR application')
    time.sleep(1)
    
while fvc == None:
    s.seek()
    if role2 in s.devices:
        fvc = Pyro4.Proxy(s.devices[role2]['pyro_uri'])
        print('FVC connected')
    else:
        print('Not connecting to the FVC application')
    time.sleep(1)

ss = Seeker('-dos-','PetalControl')
while pc0 == None:
    ss.seek()
    if role3 in ss.devices:
        pc0 = Pyro4.Proxy(ss.devices[role3]['pyro_uri'])
        print('PC0 connected')
    else:
        print('Not connecting to the PC0 application')
    time.sleep(1)

def flux(mag):
    return 10**(-0.4*(mag-25))

def calc_mag(red_file):
    data = np.genfromtxt(red_file,usecols=(0,1,2,3,4,5))
    pinholes = []
    fibers = []
    for row in data:
        if row[4] == 3.0:
            pinholes.append(row[3])
        elif row[4] == 5.0:
            fibers.append(row[3])

    pinhole_avg = np.mean(pinholes)
    fibers_avg = np.mean(fibers)
    pinhole_std = np.std(pinholes)
    fibers_std = np.std(fibers) 
    pinhole_flux = flux(pinhole_avg)
    fibers_flux = flux(fibers_avg)
    return (pinhole_flux,pinhole_avg,pinhole_std,fibers_flux,fibers_avg,fibers_std) 

dc_red_files = {}
led_red_files = {}

fvc.set(exptime=exptime)
t = fvc.get('exptime')
led.set(channel=1)
led.set(led='off')
pc0.set_fiducial(20000,0)
print('Everything is turned off')
error = fvc.calibrate_bias(0)
if error == 'SUCCESS':
    print('Background image taken successfully')
else:
    print('Bias image was not taken')

print("Exposure time is set to %f" % float(t))
print("========Starting to cycle through fiducial duty cycles===========")
led.set(channel=1)
led.set(current=max_led)
led.set(led='on')
#Start the loop
for dc in duty_cycles:
    print("Setting duty cycle to %d" %dc)
    pc0.set_fiducial(20000,dc)
    if dc <= 50:
        pc0.set_fiducial(1114,dc*2)
    else:
        pc0.set_fiducial(1114,100)
    #FVC commands
    retcode = fvc.calibrate_image()
    if retcode == 'SUCCESS':
        print("Autotune was successful")
        measure = fvc.measure()
        if type(measure) == dict:
            file = fvc.get('image_name')
            print(file)
            filen = os.path.splitext(file)[0]+'.red'
            print("Copying over reduced file: ")
            os.system("scp msdos@desifvc.kpno.noao.edu:%s ." % (data_dir+'/'+filen))
            dc_red_files[dc] = filen
        else:
            print(measure)
    else:
        print(retcode)

print("========Starting to cycle through led current values===========")
pc0.set_fiducial(20000,max_dc)
for current in led_currents:
    print("Set led current to %d" % current)
    try:
        input("Press enter when ready to continue")
    except SyntaxError:
        pass
    #try:
    #    time.sleep(5)
    #    led.set(current=current)
    #    led.set(led='on')
    #except Exception as e:
    #    print("LED is having trouble switching current values: %s" % e)
    
    #FVC commands
    retcode = fvc.calibrate_image()
    if retcode == 'SUCCESS':
        print("Autotune was successful")
        measure = fvc.measure()
        if type(measure) == dict:
            file = fvc.get('image_name')
            print(file)
            filen = os.path.splitext(file)[0]+'.red'
            os.system("scp msdos@desifvc.kpno.noao.edu:%s ." % (data_dir+'/'+filen))
            led_red_files[current] = filen
        else:
            print(measure)
    else:
        print(retcode)

dc_fluxes = {}    
for key,value in dc_red_files.items():
    pinhole_flux,pinhole_avg,pinhole_std,fibers_flux,fibers_avg,fibers_std=calc_mag(value) 
    print("For duty cycle %d and led current %d, we are getting a pinhole flux %f and fiber flux %f" % (key,max_led,pinhole_flux,fibers_flux))
    dc_fluxes[key] = [pinhole_flux,fibers_flux]

led_fluxes = {}
for key,value in led_red_files.items():
    pinhole_flux,pinhole_avg,pinhole_std,fibers_flux,fibers_avg,fibers_std=calc_mag(value) 
    print("For duty cycle %d and led current %d, we are getting a pinhole flux %f and fiber flux %f" % (max_dc,key,pinhole_flux,fibers_flux))
    led_fluxes[key] = [pinhole_flux,fibers_flux]


def plot_fluxes(flux_dict,name,num):
    plt.figure()
    xx = []
    yy1 = []
    yy2 = []
    for key,value in flux_dict.items():
        xx.append(key)
        yy1.append(value[0])
        yy2.append(value[1])
    if num == 1:
        plt.plot(xx, yy1,'x')
    elif num ==2:
        plt.plot(xx,yy2,'x')
    plt.title('%s  vs. flux'% name)
    plt.xlabel(name)
    plt.xlim(min(xx)-10,max(xx)+10)
    plt.ylabel('Average flux')
    plt.axhline(y=flux_goal)

plot_fluxes(dc_fluxes,'Duty Cycle',1)
plot_fluxes(led_fluxes,'Led Current',2)
plt.show()

os.system("rm *.red")
