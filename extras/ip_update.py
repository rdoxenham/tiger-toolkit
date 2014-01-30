#!/usr/bin/env python
# IP Address Update for All-in-One Configurations
# Rhys Oxenham <roxenham@redhat.com>

import subprocess
import sys
import MySQLdb
import urlparse

def ask_question(question, hidden):
        answer = None
        if not hidden:
                while answer == "" or answer == None:
                        answer = raw_input(question)
        else:
                while answer == None:
                        answer = getpass.getpass(question)
        return answer

def yesno_question(question):
	is_valid = None
	while is_valid == None:
		answer = ask_question(question, False)
		if answer.upper() == "Y" or answer.upper() == "YES":
				return True
		elif answer.upper() == "N" or answer.upper() == "NO":
				return False
		else: is_valid = None

def show_current_ip():
	try:
		ipaddress_ps = subprocess.Popen(['/usr/bin/facter', 'ipaddress_eth0'], stdout=subprocess.PIPE)
		current_ip, err = ipaddress_ps.communicate()
		netmask_ps = subprocess.Popen(['/usr/bin/facter', 'netmask_eth0'], stdout=subprocess.PIPE)
		current_netmask, err = netmask_ps.communicate()
		print "Current IP Address: %s (%s)\n" % (current_ip.strip(), current_netmask.strip())
		return current_ip
	except:
		print "ERROR: Couldn't find current IP address!"

def run_ip_update(new_ip, new_netmask, new_gateway, current_ip):
	devnull = open('/dev/null', 'w')
	try:
		subprocess.call(['/bin/sed', '-i', 's/IPADDR=.*/IPADDR=' + new_ip + '/g', '/etc/sysconfig/network-scripts/ifcfg-eth0'], stdout=devnull, stderr=devnull)
		subprocess.call(['/bin/sed', '-i', 's/NETMASK=.*/NETMASK=' + new_netmask + '/g', '/etc/sysconfig/network-scripts/ifcfg-eth0'], stdout=devnull, stderr=devnull)
		subprocess.call(['/bin/sed', '-i', 's/GATEWAY=.*/GATEWAY=' + new_gateway + '/g', '/etc/sysconfig/network-scripts/ifcfg-eth0'], stdout=devnull, stderr=devnull)
	except:
		print "ERROR: Couldn't make changes to network adapter configuration file"
		sys.exit(1)

	try:
		db = MySQLdb.connect(host="localhost", user="root", passwd="redhat", db="keystone")
		cur = db.cursor()
		cur.execute("select id, url from endpoint")

		for row in cur.fetchall():
	       	 	url = str(row[1])
		        endpoint_id = str(row[0])
		        try:
       		     		u = urlparse.urlparse(url)
            			urlstring = "%s://%s:%s%s" % (u.scheme, new_ip, u.port,u.path)
	       		        cur.execute("""UPDATE endpoint
                                SET url=%s
                         	WHERE id=%s
                            	""", (urlstring, endpoint_id))

	        	except Exception as e:
	       	     		print "Could not parse URL, giving up: %s (%s)" % (url, e)
				cur.close()
				db.close()
		                sys.exit(1)
	    	db.commit()
    		cur.close()
    		db.close()
	except:
		print "ERROR: Couldn't make changes to the database!"
		sys.exit(1)

	file_list = ['/etc/nagios/keystonerc_admin', \
		'/etc/nagios/nagios_host.cfg', \
		'/etc/nagios/nrpe.cfg', \
		'/etc/nagios/nagios_service.cfg', \
		'/etc/cinder/api-paste.ini', \
		'/etc/cinder/cinder.conf', \
		'/etc/glance/glance-api.conf', \
		'/etc/glance/glance-registry.conf', \
		'/etc/heat/heat.conf', \
		'/etc/neutron/metadata_agent.ini', \
		'/etc/neutron/api-paste.ini', \
		'/etc/neutron/neutron.conf', \
		'/etc/nova/nova.conf', \
		'/etc/openstack-dashboard/local_settings', \
		'/etc/ceilometer/ceilometer.conf', \
		'/etc/sysconfig/iptables', \
		'/etc/keystone/keystone.conf', \
		'/root/keystonerc_admin', \
		'/root/keystonerc_demo']

	try:
		for file in file_list:
			subprocess.call(['/bin/sed', '-i', 's/' + current_ip.strip() + '/' + new_ip.strip() + '/g', file])
	except:
		print "ERROR: Unable to update OpenStack configuration files!"
		sys.exit(1)

	print "SUCCESS: Successfully migrated from %s to %s. PLEASE REBOOT!" % (current_ip.strip(), new_ip.strip())
	sys.exit(0)

if __name__ == "__main__":
	current_ip = show_current_ip()
	new_ip = ask_question("Enter NEW IP Address: ", False)
	new_netmask = ask_question("Enter NEW Subnet Mask: ", False)
	new_gateway = ask_question("Enter NEW Gateway IP: ", False)
	print "\n"
	if yesno_question("Execute changes? [Y/N]: "):
		run_ip_update(new_ip, new_netmask, new_gateway, current_ip)
	else:
		print "INFO: No changes made."
		sys.exit(0)
