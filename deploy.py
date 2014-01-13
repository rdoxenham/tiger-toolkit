#!/usr/bin/env python

import sys
import os
import getopt
import getpass
import time
import datetime
import string

VERSION = "1.0"
TUNNEL_TYPE = "gre"

COMPUTE_HOSTS = []
CONTROLLER_HOSTS = []
NETWORK_HOSTS = []
NTP_SERVERS = []
OVS_TYPE = "local"
TUNNEL_IF = "eth1"
PASSWD = "redhat"

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

def ask_question(question, hidden):
        answer = None
        if not hidden:
                while answer == "" or answer == None:
                        answer = raw_input(question)
        else:
                while answer == None:
                        answer = getpass.getpass(question)
        return answer

def gen_packstack():
	try:
		infile = open("answers/basic.txt")
	except: infile = None

	if infile:
		now = datetime.datetime.now()
		outname = "answers-%s" % now.strftime("%Y%m%d-%H%M")
		outname = "/tmp/" + outname + ".txt"
		outfile = open(outname, 'w')

		COMPUTE_LIST = ",".join(COMPUTE_HOSTS)
		NTP_LIST = ",".join(NTP_SERVERS)
		replaceables = {'changeme_controller':CONTROLLER_HOSTS[0], \
						'changeme_network':NETWORK_HOSTS[0], \
						'changeme_compute':COMPUTE_LIST, \
						'changeme_ntp':NTP_LIST, \
						'changeme_passwd':PASSWD, \
						'local':OVS_TYPE, \
						'eth1':TUNNEL_IF}

		for line in infile:
			for source, target in replaceables.iteritems():
				line = line.replace(source, target)
			outfile.write(line)
		infile.close()
		outfile.close()

		print "\nINFO: Successfully wrote answer file: %s" % outname
		return outname

	else:
		print "FATAL: No packstack answer file found! Please re-clone repository!"
		sys.exit(2)

def ask_details(advanced):
	happy = False
	while not happy:
		controller = ask_question("Enter Controller Host IP(s): ", False)
		controller = controller.strip()
		values = controller.split(',')
		if advanced:
			for value in values:
				value = value.strip()
				CONTROLLER_HOSTS.append(value)
		else:
			if len(values) > 0: CONTROLLER_HOSTS.append(values[0])

		network = ask_question("Enter Network Host IP(s): ", False)
		network = network.strip()
		values = network.split(',')
		if advanced:
			for value in values:
				value = value.strip()
				NETWORK_HOSTS.append(value)
		else:
			if len(values) > 0: NETWORK_HOSTS.append(values[0])

		compute = ask_question("Enter Compute Host IP(s): ", False)
		compute = compute.strip()
		values = compute.split(',')
		for value in values:
			value = value.strip()
			COMPUTE_HOSTS.append(value)

		ntp = ask_question("Enter NTP Server IP(s): ", False)
		ntp = ntp.strip()
		values = ntp.split(',')
		for value in values:
			value = value.strip()
			NTP_SERVERS.append(value)

		if len(COMPUTE_HOSTS) > 1:
			global TUNNEL_IF, OVS_TYPE
			TUNNEL_IF = ask_question("Enter interface used for tunnel traffic: ", False)
			OVS_TYPE = TUNNEL_TYPE

		PASSWD = ask_question("Choose a password: ", False)

		print "\n Field             | Value                               "
		print "-------------------+------------------------------------"
		print " Controller Nodes  | %s " % ", ".join(CONTROLLER_HOSTS)
		print " Network Nodes     | %s " % ", ".join(NETWORK_HOSTS)
		print " Compute Nodes     | %s " % ", ".join(COMPUTE_HOSTS)
		print " NTP Servers       | %s " % ", ".join(NTP_SERVERS)
		if len(COMPUTE_HOSTS) > 1:
			print " Private Interface | %s " % TUNNEL_IF
		print " Password          | %s \n" % PASSWD

		answer = ask_question("Is this correct? [Y/N]: ", False)
		if answer.upper() == "Y" or answer.upper() == "YES":
			happy = True
		elif answer.upper() == "N" or answer.upper() == "NO":
			del CONTROLLER_HOSTS[:]
			del NETWORK_HOSTS[:]
			del COMPUTE_HOSTS[:]
			del NTP_SERVERS[:]
			happy = False
			print "\n"
		else:
			print "INFO: Exiting deployment tool."
			sys.exit(0)

def run_prereq():
	check_root()
	print "INFO: Running prerequisite checks...\n"

	sys.exit(0)

def deploy_basic():
	check_root()
	print "INFO: Deploying BASIC configuration...\n"
	ask_details(False)
	filename = gen_packstack()

	sys.exit(0)

def deploy_advanced():
	check_root()
	print "INFO: Deploying ADVANCED configuration...\n"
	ask_details(True)
	sys.exit(0)

if __name__ == "__main__":
	try:
		options, other = getopt.getopt(sys.argv[1:], 'hcbap;', ['help','check','basic','advanced','post',])

	except:
		print "FATAL: Unknown options specified. Use --help for usage information."
		sys.exit(1)

	for opt, arg in options:
		if opt in ('-h', '--help'): usage()
		if opt in ('-c', '--check'): run_prereq()
		if opt in ('-b', '--basic'): deploy_basic()
		if opt in ('-a', '--advanced'): deploy_advanced()
		if opt in ('-p', '--post'): run_post()

	print "FATAL: No options specified. Use --help for usage"
	sys.exit(2)