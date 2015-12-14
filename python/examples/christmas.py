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
import os
import datetime

sqrt2=np.sqrt(2.)

t0=time.time()

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
		if xc[i]>imw+3*spot_sigma[i] or xc[i]<-3*spot_sigma[i] or yc[i]>imh+3*spot_sigma[i] or yc[i]<-3*spot_sigma[i]:
			continue
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

	brightness=0
	if maxtot>0:
		brightness=maxtotrgb/maxtot
	if brightness>1:
		brightness=1
	unicorn.brightness(brightness)
	unicorn.show()

def Spiral(args,
           duration_sec=0,
           max_ncolours=7,
           narms=None,
           rrange=None,
           fwhmrange=None,
           thetadotdeg=None,
           dtheta0deg=None,
           bg=(0, 0, 0),
           poss_rgb=[(255,0,0),
                  (0,255,0),
                  (0,0,255),
                  (255,255,0),
                  (255,0,255),
                  (0,255,255),
                  (255,180,0)]
   ):

	unicorn.rotation(0)

	min_fwhm=1.5
	#dr=2+2*np.random.random()
	#rmin=-dr+4.5*np.random.random()
	#rmax=rmin+dr
        if rrange is None:
                rmax=3.5+np.random.random()
                rmin=0.5+np.random.random()
        else:
                rmin, rmax=rrange
        x0=4.
	y0=4.

	ncolours=min(np.random.randint(2, max_ncolours+1), len(poss_rgb))
	colours=[]
	for i in range(ncolours):
		while True:
			col=poss_rgb[np.random.randint(0, len(poss_rgb))]
			if not col in colours:
				colours.append(col)
				break

	# Circumference of outer radius
	circumference=2.*scipy.constants.pi*rmax

	# Maximum fwhm of spirals we can fit in circumference
	max_fwhm=min(circumference/len(colours), 3)*0.5

	fwhm=np.random.random()*(max_fwhm-min_fwhm)+min_fwhm

        max_arms=8
	max_narms=min(circumference/fwhm, max_arms) # Maximum number of spiral arms

	# Choose narms as random multiple of len(colours) < max_narms 
	if narms is None:
                narms=len(colours)*(np.random.randint(0, int(np.floor(float(max_narms)/len(colours))))+1)

	# Don't allow spirals to overlap azimuthally
	dtheta0sign=(np.random.randint(0,2)-0.5)*2
	if dtheta0deg is None:
                dtheta0=2.*scipy.constants.pi/narms*np.random.random()*dtheta0sign
        else:
                dtheta0=dtheta0deg/180.*scipy.constants.pi

	nr=int(np.ceil(np.sqrt((rmax-rmin)*(rmax-rmin)+(rmax*dtheta0)*(rmax*dtheta0))/fwhm+1.))
	#print("nr=%d" % nr)

	theta0=np.linspace(0, dtheta0, nr)
        
        if thetadotdeg is None:
                thetadotdegmax=45./duration_sec
                thetadotdegmin=360./duration_sec
        	thetadotsign=(np.random.randint(0,2)-0.5)*2
                thetadotdeg=(thetadotdegmin+np.random.random()*(thetadotdegmax-thetadotdegmin))*thetadotsign

	tstart=time.time()
	while (duration_sec==0 or time.time()-tstart<duration_sec) and os.path.exists('/tmp/.christmas'):

		x=[]
		y=[]
		sigma=[]
		rgb=[]

		t=time.time()

		if rmax>=0:
			for ir in range(nr):

				if nr==1:
					r=rmax
				else:
					r=max(0, rmin)+ir*float(rmax-rmin)/(nr-1)

				for itheta in range(narms):
					theta=theta0[ir]+itheta*2.*scipy.constants.pi/narms

					x.append(x0+r*np.cos(theta))
					y.append(y0+r*np.sin(theta))
                                        if fwhmrange is None:
                                                sigma.append(max(0.5, fwhm*r/rmax)/2.35)
                                        else:
                                                sigma.append(fwhmrange[0]+(fwhmrange[1]-fwhmrange[0])*r/rmax)
                                        rgb.append(colours[(itheta)%len(colours)])

				theta0[ir]=scipy.constants.pi/180.*thetadotdeg*(t-t0)
		

		set_image(spots_to_image(x, y, sigma, rgb, bg_rgb=bg, use_erf=args.use_erf))
		time.sleep(args.dt_sec)

		#rmin+=0.1
		#rmax+=0.1

def Angel(duration_sec=5):
	unicorn.rotation(90)
        unicorn.set_pixels(pixels)
        unicorn.show()
        time.sleep(duration_sec)

def scale_pixels(pixels, fac):
        return map(lambda row: map(lambda rgb: (int(round(rgb[0]*fac)), int(round(rgb[1]*fac)), int(round(rgb[2]*fac))), row), pixels)


def ShowPixels(pixels, fade_in_sec=1., duration_sec=5., fade_out_sec=1., fps=20, max_brightness=0.4):
	unicorn.rotation(90)

        unicorn.set_pixels(pixels)

        tstart=time.time()
        if fade_in_sec>0:
                while time.time()-tstart<fade_in_sec and os.path.exists('/tmp/.christmas'):
                        unicorn.brightness(max_brightness*(time.time()-tstart)*1./fade_in_sec)
                        unicorn.show()
                        time.sleep(1./fps)

        unicorn.brightness(max_brightness)
        unicorn.show()
        tstart=time.time()
        while time.time()-tstart<duration_sec and os.path.exists('/tmp/.christmas'):
                time.sleep(1./fps)
                
        tstart=time.time()
        if fade_out_sec>0:
                while time.time()-tstart<fade_out_sec and os.path.exists('/tmp/.christmas'):
                        unicorn.brightness(max_brightness*(1.-(time.time()-tstart)*1./fade_out_sec))
                        unicorn.show()
                        time.sleep(1./fps)

        unicorn.clear()

                        
def ProcessCommandLine():

	"""Create an argparse parser for the command line options."""
	import argparse

	parser = argparse.ArgumentParser(description=__doc__.strip())

	parser.add_argument('--spiral', action='store_true', default=False,
			    help='Include spiral animation')
	parser.add_argument('--star', action='store_true', default=False,
			    help='Include star animation')
	parser.add_argument('--angel', action='store_true', default=False,
			    help='Show angel')
        parser.add_argument('--pudding', action='store_true', default=False,
			    help='Show Christmas Pudding')
 	parser.add_argument('--duration-sec', metavar='SECONDS', type=float, default=2,
			    help='Duration of each mode before cycling')
 	parser.add_argument('--dt-sec', metavar='SECONDS', type=float, default=0.05,
			    help='Interval between each animation frame')
 	parser.add_argument('--n-loop', metavar='COUNT', type=int, default=0,
			    help='How times to show animations (0 for forever)')
	parser.add_argument('--use-erf', action='store_true', default=False,
			    help='Use more accurate error function for Gaussian calculation')
	parser.add_argument('--debug', action='store_true', default=False,
			    help='Print back trace in event of exception')


	return parser.parse_args()
        
def Run(args):

	open('/tmp/.christmas', 'w').write("1\n")

	nmodes=args.star+args.spiral+args.angel+args.pudding # Count number of requested shows
	if not nmodes:
		print("Choose at least one display!")
		exit(1)

	duration_sec=args.duration_sec

	iloop=0
	while (args.n_loop==0 or iloop<args.n_loop) and os.path.exists('/tmp/.christmas'):

                if args.spiral:
                        Spiral(args,
                               duration_sec=duration_sec,
                               max_ncolours=7,
                               bg=(0, 0, 0),
                               poss_rgb=[(255,0,0),
                                         (0,255,0),
                                         (0,0,255),
                                         (255,255,0),
                                         (255,0,255),
                                         (0,255,255),
                                         (255,180,0)])

                if args.star:
                        # Need to make it more star-like
                        Spiral(args,
                               duration_sec=duration_sec*2,
                               narms=5,
                               bg=(0, 0, 0),
                               rrange=[1.25, 3.75],
                               fwhmrange=(1.25, 0.5),
                               thetadotdeg=360./duration_sec,
                               dtheta0deg=5,
                               poss_rgb=[(255,255,0),
                                         (255,255,255),
                                         (255,180,0)])

                if args.pudding:
                        pudding=[[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 255, 0), (0, 132, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (0, 0, 0), (132, 132, 132), (0, 255, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (132, 132, 132), (132, 132, 132), (132, 132, 132), (132, 132, 132), (0, 0, 0), (0, 0, 0)], [(0, 0, 0), (132, 132, 132), (145, 120, 83), (96, 66, 20), (96, 66, 20), (145, 120, 83), (132, 132, 132), (0, 0, 0)], [(0, 0, 0), (107, 74, 25), (107, 74, 25), (107, 74, 25), (107, 74, 25), (96, 66, 20), (96, 66, 20), (0, 0, 0)], [(0, 0, 0), (96, 66, 20), (107, 74, 25), (107, 74, 25), (107, 74, 25), (96, 66, 20), (96, 66, 20), (0, 0, 0)], [(0, 0, 0), (72, 49, 15), (107, 74, 25), (107, 74, 25), (96, 66, 20), (96, 66, 20), (72, 49, 15), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (72, 49, 15), (96, 66, 20), (96, 66, 20), (72, 49, 15), (0, 0, 0), (0, 0, 0)]]
                        ShowPixels(pudding, fade_in_sec=0.5, duration_sec=duration_sec-1, fade_out_sec=0.5, fps=20)

                if args.angel:
                        angel=[[(0, 0, 0), (132, 132, 0), (0, 0, 0), (255, 255, 0), (255, 255, 0), (0, 0, 0), (132, 132, 0), (0, 0, 0)], [(132, 132, 0), (132, 132, 0), (0, 0, 0), (132, 0, 132), (132, 0, 132), (0, 0, 0), (132, 132, 0), (132, 132, 0)], [(132, 132, 0), (198, 198, 198), (132, 132, 0), (132, 0, 132), (132, 0, 132), (132, 132, 0), (198, 198, 198), (132, 132, 0)], [(132, 132, 0), (132, 132, 0), (198, 198, 198), (198, 198, 198), (198, 198, 198), (198, 198, 198), (132, 132, 0), (132, 132, 0)], [(0, 0, 0), (132, 132, 0), (132, 132, 0), (198, 198, 198), (198, 198, 198), (132, 132, 0), (132, 132, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (132, 132, 0), (198, 198, 198), (198, 198, 198), (132, 132, 0), (0, 0, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (0, 0, 0), (198, 198, 198), (198, 198, 198), (0, 0, 0), (0, 0, 0), (0, 0, 0)], [(0, 0, 0), (0, 0, 0), (198, 198, 198), (198, 198, 198), (198, 198, 198), (198, 198, 198), (0, 0, 0), (0, 0, 0)]]
                        ShowPixels(angel, fade_in_sec=0.5, duration_sec=duration_sec-1, fade_out_sec=0.5, fps=20)
                      
		iloop+=1

        unicorn.clear()
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
