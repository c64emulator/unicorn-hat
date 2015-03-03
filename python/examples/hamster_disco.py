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

def CrossingBlobs(args, duration_sec=0):

	tsec=0.
	
	unicorn.rotation(0)
	while duration_sec==0 or tsec<duration_sec:
		nframes=50
		x0, y0=-4, 4
		x1, y1=12, 4
		for iframe in range(nframes):
			xc=iframe/(nframes-1.)*(x1-x0)+x0
			yc=iframe/(nframes-1.)*(y1-y0)+y0
			spot_fwhm=6.
			spot_sigma=spot_fwhm/2.35
			spot1_rgb=(255, 0, 0)
			spot2_rgb=(0, 255, 0)
			spot3_rgb=(0, 0, 255)
			spot4_rgb=(255, 0, 255)
			spot5_rgb=(255, 255, 0)
			bg=(0, 0, 0)
			set_image(spots_to_image([xc, yc, 8-xc, 8-xc, xc],
						 [yc, xc, 8-xc, xc,   8-xc  ],
						 [spot_sigma, spot_sigma, spot_sigma, spot_sigma, spot_sigma],
						 [spot1_rgb, spot2_rgb, spot3_rgb, spot4_rgb, spot5_rgb],
						 bg_rgb=bg))

			time.sleep(args.dt_sec)
			tsec+=args.dt_sec
			if duration_sec>0 and tsec>duration_sec:
				break

def Spiral(args, duration_sec=0):

	unicorn.rotation(0)

	max_ncolours=7
	min_fwhm=1.5
	rmin=1.5
	rmax=3.5
	x0=4.
	y0=4.
	bg=(0, 0, 0)
	thetastepdegmax=5.
	thetastepdegmin=7.5
	allcolours=[(255,0,0),
		    (0,255,0),
		    (0,0,255),
		    (255,255,0),
		    (255,0,255),
		    (0,255,255),
		    (255,255,255),
		    (255,180,0)]

	ncolours=min(np.random.randint(2, max_ncolours+1), len(allcolours))
	colours=[]
	for i in range(ncolours):
		while True:
			col=allcolours[np.random.randint(0, len(allcolours))]
			if not col in colours:
				colours.append(col)
				break

	# Circumference of outer radius
	circumference=2.*scipy.constants.pi*rmax

	# Maximum fwhm of spirals we can fit in circumference
	max_fwhm=min(circumference/len(colours), 3)*0.5
	#print("max_fwhm=%g" % max_fwhm)

	fwhm=np.random.random()*(max_fwhm-min_fwhm)+min_fwhm
	#print("fwhm=%g" % fwhm)

	max_ntheta=min(circumference/fwhm, 8) # Maximum number of spiral arms
	#print("max_ntheta=%d" % max_ntheta)

	# Choose ntheta as random multiple of len(colours) < max_ntheta 
	ntheta=len(colours)*(np.random.randint(0, int(np.floor(float(max_ntheta)/len(colours))))+1)
	#print("ntheta=%d" % ntheta)

	# Don't allow spirals to overlap azimuthally
	dtheta0sign=(np.random.randint(0,2)-0.5)*2
	dtheta0=2.*scipy.constants.pi/ntheta*np.random.random()*dtheta0sign
	#print("dtheta0=%g degrees" % (dtheta0/scipy.constants.pi*180))

	nr=int(np.ceil(np.sqrt((rmax-rmin)*(rmax-rmin)+(rmax*dtheta0)*(rmax*dtheta0))/fwhm+1.))
	#print("nr=%d" % nr)

	theta0=np.linspace(0, dtheta0, nr)

	thetastepsign=(np.random.randint(0,2)-0.5)*2
	thetastepdeg=(thetastepdegmin+np.random.random()*(thetastepdegmax-thetastepdegmin))*thetastepsign
	#print("thetastepdeg=%g degrees" % thetastepdeg)

	start=time.time()
	while duration_sec==0 or time.time()-start<duration_sec:

		x=[]
		y=[]
		sigma=[]
		rgb=[]

		for ir in range(nr):

			if nr==1:
				r=rmax
			else:
				r=rmin+ir*float(rmax-rmin)/(nr-1)
			
			for itheta in range(ntheta):
				theta=theta0[ir]+itheta*2.*scipy.constants.pi/ntheta

				x.append(x0+r*np.cos(theta))
				y.append(y0+r*np.sin(theta))
				sigma.append(max(0.5, fwhm*r/rmax)/2.35)
				rgb.append(colours[(itheta)%len(colours)])

			theta0[ir]+=scipy.constants.pi/180.*thetastepdeg

		set_image(spots_to_image(x, y, sigma, rgb, bg_rgb=bg, use_erf=args.use_erf))
		time.sleep(args.dt_sec)
		
def ProcessCommandLine():

	"""Create an argparse parser for the command line options."""
	import argparse

	parser = argparse.ArgumentParser(description=__doc__.strip())

	parser.add_argument('--crossing-blobs', action='store_true', default=False,
			    help='Include crossing blobs animation')
	parser.add_argument('--spiral', action='store_true', default=False,
			    help='Include spiral animation')
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

	nmodes=args.crossing_blobs+args.spiral # Count number of requested shows
	if not nmodes:
		print("Choose at least one animation!")
		exit(1)

	duration_sec=args.duration_sec

	iloop=0
	while args.n_loop==0 or iloop<args.n_loop:
		if args.crossing_blobs:
			CrossingBlobs(args, duration_sec=duration_sec)
		if args.spiral:
			Spiral(args, duration_sec=duration_sec)
		iloop+=1

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

