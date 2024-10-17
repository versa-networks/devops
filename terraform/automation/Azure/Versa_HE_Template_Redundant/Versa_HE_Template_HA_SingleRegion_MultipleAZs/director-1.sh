#!/bin/bash
log_path="/etc/bootLog.txt"
if [ -f "$log_path" ]
then
    echo "Cloud Init script already ran earlier during first time boot.." >> $log_path
else
    touch $log_path
SSHKey="${sshkey}"
KeyDir="/home/Administrator/.ssh"
KeyFile="/home/Administrator/.ssh/authorized_keys"
Van1IP="${van_1_mgmt_ip}"
Van2IP="${van_2_mgmt_ip}"
Van3IP="${van_3_mgmt_ip}"
Van4IP="${van_4_mgmt_ip}"
Address="Match Address $Van1IP,$Van2IP,$Van3IP,$Van4IP"
SSH_Conf="/etc/ssh/sshd_config"
UBUNTU_RELEASE="$(lsb_release -cs)"
echo "Starting cloud init script...." > $log_path

echo "Modifying /etc/network/interface file.." >> $log_path
cp /etc/network/interfaces /etc/network/interfaces.bak
if [[ $UBUNTU_RELEASE == "trusty" ]]; then
cat > /etc/network/interfaces << EOF
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto eth0
iface eth0 inet dhcp

# The secondary network interface
auto eth1
iface eth1 inet dhcp
EOF
else
cat > /etc/network/interfaces << EOF
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback
# The primary network interface
auto eth0
iface eth0 inet dhcp
    offload-gro off

# The secondary network interface
auto eth1
iface eth1 inet dhcp
    offload-gro off
EOF
fi

echo -e "Modified /etc/network/interface file. Refer below new interface file content:\n`cat /etc/network/interfaces`" >> $log_path

echo "Restart Network services.." >> $log_path
if [[ $UBUNTU_RELEASE == "trusty" ]]; then
    /etc/init.d/networking restart >> /dev/null 2>&1
else
    systemctl restart networking >> /dev/null 2>&1
fi

echo "Modifying /etc/hosts file.." >> $log_path
cp /etc/hosts /etc/hosts.bak
cat > /etc/hosts << EOF
127.0.0.1			localhost
${dir_master_mgmt_ip}			${hostname_dir_master}
${dir_slave_mgmt_ip}			${hostname_dir_slave}
${van_1_mgmt_ip}			${hostname_van_1}
${van_2_mgmt_ip}			${hostname_van_2}
${van_3_mgmt_ip}                        ${hostname_van_3}
${van_4_mgmt_ip}                        ${hostname_van_4}

# The following lines are desirable for IPv6 capable hosts cloudeinit
::1localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
echo -e "Modified /etc/hosts file. Refer below new hosts file content:\n`cat /etc/hosts`" >> $log_path

echo "Moditing /etc/hostname file.." >> $log_path
hostname ${hostname_dir_master}
cp /etc/hostname /etc/hostname.bak
cat > /etc/hostname << EOF
${hostname_dir_master}
EOF

if [[ $UBUNTU_RELEASE == "bionic" ]]; then
    sudo hostnamectl set-hostname ${hostname_dir_master}
fi

echo "Hostname modified to : `hostname`" >> $log_path

echo -e "Injecting ssh key into Administrator user.\n" >> $log_path
if [ ! -d "$KeyDir" ]; then
	echo -e "Creating the .ssh directory and injecting the SSH Key.\n" >> $log_path
	sudo mkdir $KeyDir
	sudo echo $SSHKey >> $KeyFile
	sudo chown Administrator:versa $KeyDir
	sudo chown Administrator:versa $KeyFile
	sudo chmod 600 $KeyFile
elif ! grep -Fq "$SSHKey" $KeyFile; then
	echo -e "Key not found. Injecting the SSH Key.\n" >> $log_path
	sudo echo $SSHKey >> $KeyFile
	sudo chown Administrator:versa $KeyDir
	sudo chown Administrator:versa $KeyFile
	sudo chmod 600 $KeyFile
else
	echo -e "SSH Key already present in file: $KeyFile.." >> $log_path
fi

echo -e "Enanbling ssh login using password." >> $log_path
if ! grep -Fq "$Address" $SSH_Conf; then
	echo -e "Adding the match address exception for Analytics Management IP to install certificate.\n" >> $log_path
	sed -i.bak "\$a\Match Address $Van1IP,$Van2IP,$Van3IP,$Van4IP\n  PasswordAuthentication yes\nMatch all" $SSH_Conf
	sudo service ssh restart
else
	echo -e "Analytics Management IP address is alredy present in file $SSH_Conf.\n" >> $log_path
fi

echo -e "Generating director self signed certififcates. Refer detail below:\n" >> $log_path
sudo rm -rf /var/versa/vnms/data/certs/
sudo -u versa /opt/versa/vnms/scripts/vnms-certgen.sh --cn ${hostname_dir_master} --san ${hostname_dir_slave} --storepass versa123 >> $log_path
sudo chown -R versa:versa /var/versa/vnms/data/certs/

echo "Adding north bond and south bond interface in setup.json file.." >> $log_path
cat > /opt/versa/etc/setup.json << EOF
{
	"input":{
		"version": "1.0",
		"south-bound-interface":[
		  "eth1"
		],
		"hostname": "${hostname_dir_master}"
	 }
}
EOF
echo -e "Got below data from setup.json file:\n `cat /opt/versa/etc/setup.json`" >> $log_path
echo "Executing the startup script in non interactive mode.." >> $log_path
sudo -u Administrator /opt/versa/vnms/scripts/vnms-startup.sh --non-interactive
fi
