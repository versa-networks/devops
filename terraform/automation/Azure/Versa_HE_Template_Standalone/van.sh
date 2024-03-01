#!/bin/bash
log_path="/etc/bootLog.txt"
if [ -f "$log_path" ]
then
    echo "Cloud Init script already ran earlier during first time boot.." >> $log_path
else
    touch $log_path
SSHKey="${sshkey}"
KeyDir="/home/versa/.ssh"
KeyFile="/home/versa/.ssh/authorized_keys"
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
127.0.0.1           localhost
${van_mgmt_ip}         ${hostname_van}
${dir_mgmt_ip}         ${hostname_dir}

# The following lines are desirable for IPv6 capable hosts cloudeinit
::1localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
echo -e "Modified /etc/hosts file. Refer below new hosts file content:\n`cat /etc/hosts`" >> $log_path

echo "Moditing /etc/hostname file.." >> $log_path
hostname ${hostname_van}
cp /etc/hostname /etc/hostname.bak
cat > /etc/hostname << EOF
${hostname_van}
EOF
echo "Hostname modified to : `hostname`" >> $log_path

echo -e "Injecting ssh key into versa user.\n" >> $log_path
if [ ! -d "$KeyDir" ]; then
    echo -e "Creating the .ssh directory and injecting the SSH Key.\n" >> $log_path
    sudo mkdir $KeyDir
sudo echo $SSHKey >> $KeyFile
sudo chown versa:versa $KeyDir
sudo chown versa:versa $KeyFile
sudo chmod 600 $KeyFile
elif ! grep -Fq "$SSHKey" $KeyFile; then
    echo -e "Key not found. Injecting the SSH Key.\n" >> $log_path
    sudo echo $SSHKey >> $KeyFile
    sudo chown versa:versa $KeyDir
    sudo chown versa:versa $KeyFile
    sudo chmod 600 $KeyFile
else
    echo -e "SSH Key already present in file: $KeyFile.." >> $log_path
fi

echo -e "Adding script to copy certificates from director after instance boot up." >> $log_path
cat > /etc/get_cert.sh << EOF
#!/bin/bash
sudo sshpass -p versa123 scp  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@${dir_mgmt_ip}:/var/versa/vnms/data/certs/versa_director_client.cer /opt/versa/var/van-app/certificates >> $log_path
echo -e "Installing the certificates in Analytics.\n" >> $log_path
sudo /opt/versa/scripts/van-scripts/van-vd-cert-install.sh /opt/versa/var/van-app/certificates/versa_director_client.cer ${hostname_dir} >> $log_path
EOF
sudo chmod 0755 /etc/get_cert.sh
crontab -l > /tmp/orig_crontab
echo "`date +%M --date='7 minutes'` `date +%H` `date +%d` `date +%m` * sudo bash /etc/get_cert.sh; sudo crontab -l | grep -v get_cert.sh | crontab " >>  /tmp/orig_crontab
sudo crontab /tmp/orig_crontab
fi