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
DirIP="${dir_mgmt_ip}"
Address="Match Address $DirIP"
SSH_Conf="/etc/ssh/sshd_config"
UBUNTU_RELEASE="$(lsb_release -cs)"
echo "Starting cloud init script..." > $log_path

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

# The third network interface
auto eth2
iface eth2 inet dhcp
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

# The third network interface
auto eth2
iface eth2 inet dhcp
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

echo -e "Enanbling ssh login using password from Director to Controller required to onboard controller." >> $log_path
if [[ $DirIP == "" ]]; then
    echo -e "Director IP is not provided, skipping this step."
elif ! grep -Fq "$Address" $SSH_Conf; then
    echo -e "Adding the match address exception for Director Management IP required to onboard controller via passwrod based authentication.\n" >> $log_path
    sed -i.bak "\$a\Match Address $DirIP\n  PasswordAuthentication yes\nMatch all" $SSH_Conf
    sudo service ssh restart
else
    echo -e "Director Management IP address is alredy present in file $SSH_Conf.\n" >> $log_path
fi
fi