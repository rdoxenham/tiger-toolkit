#!/bin/bash
# Basic - All in One Post-Configuration

cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-br-ex
DEVICE=br-ex
BOOTPROTO=static
NM_CONTROLLED=no
ONBOOT=yes
TYPE=Ethernet
IPADDR=172.16.0.1
NETMASK=255.255.255.0
EOF

ovs-vsctl --may-exist add-br br-ex
ifconfig br-ex 172.16.0.1 netmask 255.255.255.0

source ~/keystonerc_admin
SERVICES=$(keystone tenant-list | grep services | awk '{print $2;}')
neutron net-create --tenant-id $SERVICES ext --router:external=True
neutron subnet-create --tenant-id $SERVICES ext 172.16.0.0/24 --enable_dhcp=False --gateway-ip 172.16.0.1 --allocation-pool start=172.16.0.101,end=172.16.0.160

keystone tenant-create --name demo
keystone user-create --name demo --pass redhat
keystone user-role-add --user demo --role Member --tenant demo  

cat >> ~/keystonerc_demo <<EOF
export OS_USERNAME=demo
export OS_TENANT_NAME=demo
export OS_PASSWORD=redhat
export OS_AUTH_URL=http://localhost:5000/v2.0/
export PS1='[\u@\h \W(keystone_demo)]\$ '
EOF

source ~/keystonerc_demo
neutron net-create private
neutron subnet-create private 10.0.0.0/24 --name priv_subnet
neutron router-create router1
EXTNET=$(neutron net-list | grep ext | awk '{print $2;}')
MYROUTER=$(neutron router-list | grep router1 | awk '{print $2;}')
neutron router-gateway-set $MYROUTER $EXTNET
PRIVNET=$(neutron subnet-list | grep priv_subnet | awk '{print $2;}')
neutron router-interface-add $MYROUTER $PRIVNET
sysctl -w net.ipv4.ip_forward=1
iptables -I FORWARD -i br-ex -j ACCEPT
iptables -I FORWARD -o br-ex -j ACCEPT
iptables -t nat -A POSTROUTING -s 172.16.0.0/24 -o eth0 -m comment --comment "000 nat" -j MASQUERADE

wget http://download.cirros-cloud.net/0.3.1/cirros-0.3.1-x86_64-disk.img
glance image-create --name "Cirros 0.3.1" --is-public true --disk-format qcow2 --container-format bare --file cirros-0.3.1-x86_64-disk.img
