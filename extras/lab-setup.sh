#!/usr/bin/env bash

for i in {1..20}
do
	userdel user$i
	rm -rf /home/user$i
	useradd user$i
	echo redhat | passwd user$i --stdin
	cp /root/keystonerc_admin /home/user$i
	chown user$i:user$i /home/user$i/keystonerc_admin
	chmod 600 /home/user$i/keystonerc_admin
done