#!/usr/bin/env python

'''
Requires numpy, scipy

Licensed under Creative Commons Attribution-Noncommercial-Share Alike 3.0 Unported License.
'''

import unicornhat as unicorn
import time, scipy.constants, scipy.special
import numpy as np
import sys
import traceback
import datetime

sqrt2=np.sqrt(2.)

def gaussian_spot_psf_1d(x0, x1, mu, recsig):
        return 0.5*(scipy.special.erf((x1-mu)*recsig) - scipy.special.erf((x0-mu)*recsig) );

def gaussian_spot_psf_2d(x0, x1, mux, sigmax, y0, y1, muy, sigmay):
        recsigx=1./(sigmax*sqrt2)
        recsigy=1./(sigmay*sqrt2)
        return gaussian_spot_psf_1d(x0, x1, mux, recsigx)*gaussian_spot_psf_1d(y0, y1, muy, recsigy)

def spots_to_image(xc, yc, spot_sigma, spot_rgb, imw=8, imh=8, bg_rgb=(0,0,0), use_erf=False):
	
	y, x=np.mgrid[0:imh, 0:imw]
	x=x+0.5
	y=y+0.5

	r=np.zeros((imh, imw))+bg_rgb[0]
	g=np.zeros((imh, imw))+bg_rgb[1]
	b=np.zeros((imh, imw))+bg_rgb[2]

	for i in range(len(xc)):
		if use_erf:
			profile=gaussian_spot_psf_2d(x-0.5, x+0.5, xc[i], spot_sigma[i], y-0.5, y+0.5, yc[i], spot_sigma[i])*2*scipy.constants.pi*spot_sigma[i]*spot_sigma[i]
		else:
			profile=np.exp(-(x-xc[i])*(x-xc[i])/(2*spot_sigma[i]*spot_sigma[i])-(y-yc[i])*(y-yc[i])/(2*spot_sigma[i]*spot_sigma[i]))
		r+=spot_rgb[i][0]*profile
		g+=spot_rgb[i][1]*profile
		b+=spot_rgb[i][2]*profile

	maxrgb=max(r.max(), g.max(), b.max())
	if maxrgb>255:
		r=r*255/maxrgb
		g=g*255/maxrgb
		b=b*255/maxrgb

	return r, g, b

def set_image((r, g, b), maxtotrgb=80):
	maxtot=0
	imh, imw=r.shape

	for ix in range(imw):
		for iy in range(imh):
			maxtot=max(maxtot, r[ix, iy]+g[ix, iy]+b[ix, iy])
			unicorn.set_pixel(ix, iy, int(r[ix, iy]), int(g[ix, iy]), int(b[ix, iy]))

	brightness=maxtotrgb/maxtot
	if brightness>1:
		brightness=1
	unicorn.brightness(brightness)
	unicorn.show()


def Clock(args):

	unicorn.rotation(0)

	bg=(0,0,0)

	xc=4.
	yc=4.

	h_rgb=(255,255,0)
	m_rgb=(0,255,255)
	s_rgb=(255,0,255)

	h_theta=0.
	m_theta=0.
	s_theta=0.

	h_r=2.5
	m_r=3.0
	s_r=3.5

	start=time.time()
	while args.duration_sec==0 or time.time()-start<args.duration_sec:

		t=datetime.datetime.now()
		
		x=[]
		y=[]
		sigma=[]
		rgb=[]

		h_theta=(t.hour*args.speed_up)%12*2.*scipy.constants.pi/12.
		x.append(xc+h_r*np.sin(h_theta))
		y.append(yc+h_r*np.cos(h_theta))
		sigma.append(args.fwhm/2.35)
		rgb.append(h_rgb)

		m_theta=(t.minute*args.speed_up)%60*2.*scipy.constants.pi/60.
		x.append(xc+m_r*np.sin(m_theta))
		y.append(yc+m_r*np.cos(m_theta))
		sigma.append(args.fwhm/2.35)
		rgb.append(m_rgb)

		s_theta=(t.second*args.speed_up)%60*2.*scipy.constants.pi/60.
		x.append(xc+s_r*np.sin(s_theta))
		y.append(yc+s_r*np.cos(s_theta))
		sigma.append(args.fwhm/2.35)
		rgb.append(s_rgb)

		set_image(spots_to_image(x, y, sigma, rgb, bg_rgb=bg, use_erf=args.use_erf))
		#time.sleep(args.dt_sec)
		
def ProcessCommandLine():

	"""Create an argparse parser for the command line options."""
	import argparse

	parser = argparse.ArgumentParser(description=__doc__.strip())

 	parser.add_argument('--duration-sec', metavar='SECONDS', type=float, default=0,
			    help='Duration of each mode before cycling')
 	parser.add_argument('--dt-sec', metavar='SECONDS', type=float, default=0.05,
			    help='Interval between each animation frame')
 	parser.add_argument('--fwhm', metavar='PIXELS', type=float, default=2.,
			    help='FWHM of spots')
 	parser.add_argument('--speed-up', metavar='FACTOR', type=float, default=1.,
			    help='Mess with time')
	parser.add_argument('--use-erf', action='store_true', default=False,
			    help='Use more accurate error function for Gaussian calculation')
	parser.add_argument('--debug', action='store_true', default=False,
			    help='Print back trace in event of exception')


	return parser.parse_args()

def Run(args):

	Clock(args)

if __name__ == "__main__":

	args=ProcessCommandLine()

	try:

		Run(args)

	except Exception, err:

		print("Fatal error: "+str(err))
		if args.debug:
			print "\n--- Failure -------------------------------------"
			traceback.print_exc(file=sys.stdout)
			print "-------------------------------------------------------"

