#!/usr/bin/env python

import sys
import os
import getopt
import getpass
import time
import datetime

VERSION = "1.0"

def usage():
	print "OpenStack Tiger Deployment Tool: Version %s" % VERSION
	print "Usage: " + sys.argv[0],
	print "<option> [argument]\n"
	print "\t-h, --help\t\tPrints this usage/help menu"
	print "\t-c, --check\t\tRun a pre-install system check"
	print "\t-b, --basic\t\tDeploys basic/single-controller OpenStack environment"
	print "\t-a, --advanced\t\tDeploys highly-available multi-node OpenStack environment"
	print "\t-p, --post\t\tRun post-install configuration script"
	print "\n\tExamples: " + sys.argv[0],
	print " --check"
	print "\t\t  " + sys.argv[0],
	print " --basic"
	sys.exit(0)

def check_root():
	if not os.geteuid() == 0:
		print "FATAL: Root privileges are required."
		sys.exit(1)

def deploy_basic():
	check_root()

if __name__ == "__main__":
	usage()
