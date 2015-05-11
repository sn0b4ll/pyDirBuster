#!/usr/bin/env python

import argparse
import urllib2
import threading
from time import sleep
import md5
import sys
import os
import re

print """
Directory Scanner v.0.2
Orignial (0.1): Ken Eddy - files.eddy@gmail.com (https://github.com/showmehow/pypwn)
Modified (0.2): Dominik Schlecht - dominik.schlecht@hotmail.de (https://github.com/DominikSchlecht/pyDirBuster)
"""

###############################################################################
# Helper to make input urllib2-ready
###############################################################################
def aidUrl(url):
	if not re.match("^http://", url):
		url = "http://" + url
	return url
###############################################################################

###############################################################################
# Handle parameters
###############################################################################
parser = argparse.ArgumentParser()
parser.add_argument(
	"url",
	help="URL to scan"
)

parser.add_argument(
	"file",
	help="wordlist to use"
)

parser.add_argument(
	"-lp", "--landingpage",
	help="if a webserver redirects to a landingpage instead throwing a 404, this option can be used to specifiy that page"
)

parser.add_argument(
	"-t", "--threads",
	default=9,
	type=int,
	help="number of threads/parallel connections to open. Default is 9"
)

parser.add_argument(
	"-v", "--verbose",
	action="store_true",
	help="print additional information"
)

args = parser.parse_args()

# Save parameters to vars
url = aidUrl(args.url)
fileName = args.file
verbose = args.verbose
landingpage = aidUrl(args.landingpage)
numThreads=args.threads+1 # Because the programm itself is a thread...
###############################################################################

###############################################################################
# Class to check a single directory (for threading)
###############################################################################
class dir_check(threading.Thread):
	def __init__(self, uri, lpHash):
		threading.Thread.__init__(self)
		self.uri = uri
		self.lpHash = lpHash
		self.retStatus = None
		self.found = False
		
	def run(self):
		try:
			response = urllib2.urlopen(self.uri)
			if response:
				if response.getcode() == 200:
					if self.lpHash:
						# Only jump here if a landingpage was specified
						if self.lpHash != md5.new(response.read()).hexdigest():
							self.found = True
					else:
						# If not, a 200 is a 200...
						self.found = True
					
					# Found a page!
					if self.found:
						self.retStatus = "[+] FOUND %s " % (self.uri)
						print "[+] FOUND %s " % (self.uri)
						if verbose:
							print response.info()
				
		except urllib2.HTTPError, e:
			# Got an error :/
			if e.code == 401:
				self.retStatus = "[!] Authorization Required %s " % (self.uri)
			elif e.code == 403:
				self.retStatus = "[!] Forbidden %s " % (self.uri)
			elif e.code == 404:
				self.retStatus = "[-] Not Found %s " % (self.uri)
			elif e.code == 503:
				self.retStatus = "[!] Service Unavailable %s " % (self.uri)
			else:
				# Something strange
				if verbose:
					print e.code()
				self.retStatus = None
				
	def status(self):
		return self.retStatus
###############################################################################

###############################################################################
# Open and read file
###############################################################################
open_dir_list = open(fileName,'r')
dirs = open_dir_list.read().split("\n")
open_dir_list.close()
###############################################################################

###############################################################################
# Calculate md5 of landing page if wanted
###############################################################################
lpHash=None
if landingpage:
	try:
		response = urllib2.urlopen(landingpage)
		lpHash = md5.new(response.read()).hexdigest()
	except urllib2.HTTPError, e:
		print "[!] Specified Page could not be found %s " % (landingpage)
###############################################################################

###############################################################################
# Start the threads
###############################################################################
results = []
cnt = 0
cntMax = len(dirs)
for dir in dirs:
	cnt += 1
	uri = url+"/"+dir
	while numThreads < threading.activeCount():
		sleep(0.1)
	thread = dir_check(uri, lpHash)
	results.append(thread)
	print "[*] Testing dir %d of %d" % (cnt, cntMax)
	thread.start()
###############################################################################

###############################################################################
# Print the summery and join threads
###############################################################################
# Wait for all threads to finish
while threading.activeCount() != 1:
	sleep(0.1)
	
# Print the summery
print "\nSummery:"
for ret in results:
	ret.join()
	status = ret.status()
	if status and (ret.found or verbose):
		print status
	
print "\n:. FINISH :.\n"
###############################################################################