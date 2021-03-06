#!/usr/bin/env python

# read in a fvc pos file, make regions and show in DS9
import numpy as np
import matplotlib.pyplot as plt
import sys,os,time
import subprocess

data_dir = "/data/fvc/"

posfilename =  sys.argv[1] + '.pos'
imfilename = sys.argv[1] + '.fits'

os.system("scp msdos@desifvc.kpno.noao.edu:%s ." % (data_dir+'/'+posfilename))
os.system("scp msdos@desifvc.kpno.noao.edu:%s ." % (data_dir+'/'+imfilename))

data = np.genfromtxt(posfilename)

regionfile = 'fvcpos.reg'

outf = open(regionfile, 'w')
outf.write('global color=green\n')

with open(posfilename, 'r') as fobj:
    for row in fobj:
        rowl = row.split()
        outrow = str("circle %0.2f %0.2f %0.2f\n" % (float(rowl[0]), float(rowl[1]), float(rowl[4])))
        outf.write(outrow)

fobj.close
outf.close

ds9str = 'ds9 ' + imfilename + ' -scale limits 1800 3000 -regions load ' + regionfile +' &'
subprocess.run(ds9str,shell=True)

#cleanstr = "rm " + sys.argv[1] + ".*"
#os.system(cleanstr)
#os.system("rm fvcpos.reg")


