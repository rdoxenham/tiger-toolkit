#!/usr/bin/env python
# Tiger Team OpenStack Deployment Script
# Rhys Oxenham <roxenham@redhat.com>

import sys
import os
import getpass
import datetime
import subprocess

VERSION = "1.0"
COMPUTE_HOSTS = []
CONTROLLER_HOSTS = []
NETWORK_HOSTS = []
NTP_SERVERS = []
OVS_TYPE = "local"
TUNNEL_IF = "eth1"
TUNNEL_TYPE = "gre"
PASSWD = "redhat"
TUNNELING = True


def check_root():
    if not os.geteuid() == 0:
        print "FATAL: Root privileges are required."
        sys.exit(1)


def retry():
    print "INFO: Retrying previous operation...\n"
    try:
        outfile = open("/tmp/.deploy_retry")
        line = outfile.readline()
        values = line.split(',')
        deployment_type = values[0]
        filename = values[1]
    except:
        print "FATAL: No retry file to run! Please use --usage for help."
        sys.exit(1)

    if deployment_type == "packstack":
        if run_packstack(filename):
            print "\nSUCCESS: Packstack completed successfully."
            sys.exit(0)
        else:
            print "ERROR: Packstack could not be executed."
            sys.exit(1)


def ask_question(question, hidden):
    answer = None
    if not hidden:
        while answer == "" or answer is None:
            answer = raw_input(question)
    else:
        while answer is None:
            answer = getpass.getpass(question)
    return answer


def gen_packstack():
    try:
        infile = open("answers/basic.txt")
    except:
        infile = None

    if infile:
        now = datetime.datetime.now()
        outname = "answers-%s" % now.strftime("%Y%m%d-%H%M")
        outname = "/tmp/" + outname + ".txt"
        outfile = open(outname, 'w')

        COMPUTE_LIST = ",".join(COMPUTE_HOSTS)
        NTP_LIST = ",".join(NTP_SERVERS)
        replaceables = {'changeme_controller': CONTROLLER_HOSTS[0],
                        'changeme_network': NETWORK_HOSTS[0],
                        'changeme_compute': COMPUTE_LIST,
                        'changeme_ntp': NTP_LIST,
                        'changeme_passwd': PASSWD,
                        'changeme_tenant_type': OVS_TYPE,
                        'changeme_tunnel_if': TUNNEL_IF}

        for line in infile:
            for source, target in replaceables.iteritems():
                line = line.replace(source, target)
            outfile.write(line)
        infile.close()
        outfile.close()

        print "\nINFO: Successfully wrote answer file: %s\n" % outname
        return outname

    else:
        print "FATAL: No packstack answer file found! Please re-clone repository!"
        sys.exit(2)


def yesno_question(question):
    is_valid = None
    while is_valid is None:
        answer = ask_question(question, False)
        if answer.upper() == "Y" or answer.upper() == "YES":
            return True
        elif answer.upper() == "N" or answer.upper() == "NO":
            return False
        else:
            is_valid = None


def multiple_choice_question(question, possibilities):
    is_valid = None
    while is_valid is None:
        answer = ask_question(question, False)
        if answer.lower() in possibilities:
            return answer.lower()
        else:
            is_valid = None


def ask_details(advanced):
    happy = False
    allinone = False
    while not happy:
        if not advanced:
            aio_question = yesno_question("All-in-One Setup? [Y/N]: ")
            if aio_question:
                global TUNNELING
                TUNNELING = False
                allinone = True
                all_ip = ask_question(
                    "\nEnter single all-in-one node IP: ", False)
                all_ip = all_ip.strip()
                values = all_ip.split(',')
                if len(values) > 0:
                    CONTROLLER_HOSTS.append(values[0])
                    COMPUTE_HOSTS.append(values[0])
                    NETWORK_HOSTS.append(values[0])
            else:
                print "\nWARNING: Not using All-in-One configuration!\n"

        if not allinone:
            controller = ask_question("Enter Controller Host IP(s): ", False)
            controller = controller.strip()
            values = controller.split(',')
            if advanced:
                for value in values:
                    value = value.strip()
                    CONTROLLER_HOSTS.append(value)
            else:
                if len(values) > 0:
                    CONTROLLER_HOSTS.append(values[0])

            network = ask_question("Enter Network Host IP(s): ", False)
            network = network.strip()
            values = network.split(',')
            if advanced:
                for value in values:
                    value = value.strip()
                    NETWORK_HOSTS.append(value)
            else:
                if len(values) > 0:
                    NETWORK_HOSTS.append(values[0])

            compute = ask_question(
                "Enter Compute Host IP(s) - Comma Separated: ", False)
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

        if TUNNELING:
            global TUNNEL_IF, OVS_TYPE
            TUNNEL_IF = ask_question(
                "Enter interface used for tunnel traffic: ", False)
            OVS_TYPE = multiple_choice_question(
                "Enter tunnel type [GRE/VXLAN]: ", ["gre", "vxlan"])

        global PASSWD
        PASSWD = ask_question("Choose a password: ", False)

        if advanced:
            deployment_type = "Multi-Node w/ High Availability"
        elif allinone:
            deployment_type = "Basic All-in-One"
        else:
            deployment_type = "Single-Node w/ No High Availability"

        print "\n Field             | Value                               "
        print "-------------------+------------------------------------"
        print " Deployment Type   | %s " % deployment_type
        print " Controller Nodes  | %s " % ", ".join(CONTROLLER_HOSTS)
        print " Network Nodes     | %s " % ", ".join(NETWORK_HOSTS)
        print " Compute Nodes     | %s " % ", ".join(COMPUTE_HOSTS)
        print " NTP Servers       | %s " % ", ".join(NTP_SERVERS)
        if TUNNELING:
            print " Tunnel Type       | %s " % OVS_TYPE.upper()
            print " Private Interface | %s " % TUNNEL_IF
        print " Password          | %s \n" % PASSWD

        correct = yesno_question("Is this correct? [Y/N]: ")
        if correct:
            happy = True
        else:
            del CONTROLLER_HOSTS[:]
            del NETWORK_HOSTS[:]
            del COMPUTE_HOSTS[:]
            del NTP_SERVERS[:]
            allinone = False
            happy = False
            print "\n"


def run_packstack(filename):
    try:
        subprocess.check_call(
            ['which', 'packstack'], stdout=devnull, stderr=devnull)
    except:
        try:
            subprocess.check_call(
                ['yum', 'install', '-y', 'openstack-packstack'], stdout=devnull, stderr=devnull)
        except:
            print "FATAL: Couldn't install Packstack!"
            sys.exit(1)
    try:
        subprocess.check_call(['packstack', '--answer-file', filename])
    except:
        return False
    return True


def run_prereq():
    check_root()
    print "INFO: Running prerequisite checks...\n"

    sys.exit(0)


def deploy_basic():
    check_root()
    print "INFO: Deploying BASIC configuration...\n"
    ask_details(False)
    filename = gen_packstack()
    if yesno_question("Execute? [Y/N]: "):
        try:
            outname = "/tmp/.deploy_retry"
            outfile = open(outname, 'w')
            outfile.write("packstack," + filename)
            outfile.close()
        except:
            print "\nWARNING: Couldn't write retry file!\n"
    else:
        print "INFO: Deployment tool exiting."
        sys.exit(0)

    print "\nRunning Packstack using: %s" % filename
    if not run_packstack(filename):
        print "ERROR: Packstack failed, please check the log output!"
        sys.exit(1)
    print "SUCCESS: Packstack successfully installed!"
    sys.exit(0)


def deploy_advanced():
    check_root()
    print "INFO: Deploying ADVANCED configuration...\n"
    ask_details(True)
    sys.exit(0)


def run_post():
    raise NotImplementedError


if __name__ == "__main__":
    import argparse

    devnull = open('/dev/null', 'w')

    parser = argparse.ArgumentParser(description="OpenStack Tiger Deployment Tool %s" % VERSION)

    parser.add_argument("--check", "-c",
                      action="store_true",
                      dest="run_prereq",
                      default=False,
                      help="Run a pre-install system check")

    parser.add_argument("--basic", "-b",
                      action="store_true",
                      dest="deploy_basic",
                      default=False,
                      help="Deploys basic/single-controller OpenStack environment")

    parser.add_argument("--advanced", "-a",
                      action="store_true",
                      dest="deploy_advanced",
                      default=False,
                      help="Deploys higly-available multi-node OpenStack environment")

    parser.add_argument("--post", "-p",
                      action="store_true",
                      dest="run_post",
                      default=False,
                      help="Run post-install configuration script")

    parser.add_argument("--retry", "-r",
                      action="store_true",
                      dest="retry",
                      default=False,
                      help="Retries the previous operation after failure")

    args = parser.parse_args()
    if (args.run_prereq == False and
       args.deploy_basic == False and
       args.deploy_advanced == False and
       args.run_post == False and
       args.retry == False):
        parser.print_help()
        sys.exit(1)

    if args.run_prereq:
        run_prereq()

    if args.deploy_basic:
        deploy_basic()

    if args.deploy_advanced:
        deploy_advanced()

    if args.run_post:
        run_post()

    if args.retry:
        retry()
