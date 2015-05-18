#!/usr/bin/env python

import argparse
import threading
from time import sleep
import urllib2
import md5
import sys
import os
import re

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
parser = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="Directory Scanner v. 0.3",
	epilog="""
v. 0.1: Ken Eddy - files.eddy@gmail.com (https://github.com/showmehow/pypwn)
v. 0.2: Dominik Schlecht - dominik.schlecht@hotmail.de (https://github.com/DominikSchlecht/pyDirBuster)
	* Multithreading
	* Landing-Page-Option
v. 0.3: Dominik Schlecht
	* Implemented TOR-Support

Use this tool only agains your own sites or with allowance of the websites owner!
Use only if allowed by your local law!

This software is published under the MIT License.
""")

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

parser.add_argument(
	"--tor",
	action="store_true",
	help="use tor"
)

parser.add_argument(
	"--tor-port",
	type=int,
	default=9050,
	help="if you have configured tor to use a different port than 9050, you can define it here"
)

parser.add_argument(
	"--testip",
	action="store_true",
	help="see what external ip you get (to test tor, icanhazip.com is used.)"
)

args = parser.parse_args()

# Save parameters to vars
url = aidUrl(args.url)
fileName = args.file
verbose = args.verbose
if args.landingpage:
	landingpage = aidUrl(args.landingpage)
else:
	landingpage = None
numThreads=args.threads+1 # Because the programm itself is a thread...
###############################################################################

###############################################################################
# Init TOR if desired
###############################################################################
if args.tor:
	print "[*] Using TOR"
	proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
	opener = urllib2.build_opener(proxy_support)
	urllib2.install_opener(opener)
###############################################################################

###############################################################################
# Test IP (must be after the TOR init)
###############################################################################
if args.testip:
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	headers={'User-Agent':user_agent}	
	request=urllib2.Request("http://icanhazip.com", None, headers)
	print urllib2.urlopen(request).read()
	sys.exit(0)
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
