#!/bin/bash
log_path="/etc/bootLog.txt"
if [ -f "$log_path" ]
then
    echo "Cloud Init script already ran earlier during first time boot.." >> $log_path
else
    touch $log_path
SSHKey="${sshkey}"
KeyDir="/home/admin/.ssh"
KeyFile="/home/admin/.ssh/authorized_keys"
Hostname_Concerto_1="${hostname_concerto_1}"
Hostname_Concerto_2="${hostname_concerto_2}"
Hostname_Concerto_3="${hostname_concerto_3}"
Concerto_1_mgmt_ip="${concerto_1_mgmt_ip}"
Concerto_2_mgmt_ip="${concerto_2_mgmt_ip}"
Concerto_3_mgmt_ip="${concerto_3_mgmt_ip}"
Address1="Match Address $Concerto_1_mgmt_ip"
Address2="Match Address $Concerto_2_mgmt_ip"
Address3="Match Address $Concerto_3_mgmt_ip"
SSH_Conf="/etc/ssh/sshd_config"
MGMT_GW="${mgmt_gw}"
echo "Starting cloud init script...." > $log_path

echo "Modifying /etc/network/interface file.." >> $log_path
cp /etc/network/interfaces /etc/network/interfaces.bak
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
    up route add -net 0.0.0.0/0 gw $MGMT_GW dev eth0

# The secondary network interface
auto eth1
iface eth1 inet dhcp
    offload-gro off
EOF

echo -e "Modified /etc/network/interface file. Refer below new interface file content:\n`cat /etc/network/interfaces`" >> $log_path

echo "Restart Network services.." >> $log_path
systemctl restart networking >> $log_path 2>&1

echo "Modifying /etc/hosts file.." >> $log_path
cp /etc/hosts /etc/hosts.bak
cat > /etc/hosts << EOF
127.0.0.1			localhost
$Concerto_1_mgmt_ip		$Hostname_Concerto_1
$Concerto_2_mgmt_ip          $Hostname_Concerto_2
$Concerto_3_mgmt_ip          $Hostname_Concerto_3

# The following lines are desirable for IPv6 capable hosts cloudeinit
::1localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
echo -e "Modified /etc/hosts file. Refer below new hosts file content:\n`cat /etc/hosts`" >> $log_path

echo "Moditing /etc/hostname file.." >> $log_path
hostnamectl set-hostname $Hostname_Concerto_2 >> $log_path 2>&1
hostname $Hostname_Concerto_2 >> $log_path 2>&1
cp /etc/hostname /etc/hostname.bak
cat > /etc/hostname << EOF
$Hostname_Concerto_2
EOF
echo "Hostname modified to : `hostname`" >> $log_path

echo -e "Injecting ssh key into admin user.\n" >> $log_path
if [ ! -d "$KeyDir" ]; then
    echo -e "Creating the .ssh directory and injecting the SSH Key.\n" >> $log_path
    sudo mkdir $KeyDir
    sudo echo $SSHKey >> $KeyFile
    sudo chown admin:versa $KeyDir
    sudo chown admin:versa $KeyFile
    sudo chmod 600 $KeyFile
elif ! grep -Fq "$SSHKey" $KeyFile; then
    echo -e "Key not found. Injecting the SSH Key.\n" >> $log_path
    sudo echo $SSHKey >> $KeyFile
    sudo chown admin:versa $KeyDir
    sudo chown admin:versa $KeyFile
    sudo chmod 600 $KeyFile
else
    echo -e "SSH Key already present in file: $KeyFile.." >> $log_path
fi

echo -e "Enanbling ssh login using password." >> $log_path
if ! grep -Fq "$Address1" $SSH_Conf; then
    echo -e "Adding the match address exception for Concerto Nodes Management IP for password based communication between clusters.\n" >> $log_path
    sed -i.bak "\$a\Match Address 127.0.0.1,$Concerto_1_mgmt_ip,$Concerto_2_mgmt_ip,$Concerto_3_mgmt_ip\n  PasswordAuthentication yes\nMatch all" $SSH_Conf
    sudo service ssh restart >> $log_path 2>&1
else
    echo -e "Concerto Management IP address for all nodes is alredy present in file $SSH_Conf.\n" >> $log_path
fi

echo -e "Adding script to load docker images in concerto nodes." >> $log_path
cat > /etc/concerto-cloud-init.sh << EOF
echo "Load docker images" >> $log_path
sudo /opt/versa/ecp/scripts/swarm/setup.sh --load >> $log_path 2>&1
echo "$(date) FIN"
EOF
sudo chown versa:versa /etc/concerto-cloud-init.sh
sudo chmod 0755 /etc/concerto-cloud-init.sh

echo -e "Creating cronjob entry to load the docker images after 5 mins from boot." >> $log_path
at now +5 min -f /etc/concerto-cloud-init.sh >> $log_path 2>&1

fi
