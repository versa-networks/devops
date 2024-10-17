#!/bin/bash
log_path="/etc/bootLog.txt"
if [ -f "$log_path" ]
then
	echo "Cloud Init script already ran earlier during first time boot.." >> $log_path
else
	touch $log_path
SSHKey="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDvgZTNiWaCKYS0zacbiN0raJHJoOTaQ6iApXmFdTXmdxjUiipTyrzpluMFgDxI0KeHZNNaxHBXuBW3ZGjVTL9urDgj+39MZ0RS4X/59eUa7XRzHr7Ds4L/KVSOPYggOVBRTFa7eqJJxKKwq3tNsBBxvSTRxgnlC2v/D55BXCrkNZ3544LPhOMp8bkgEWccGQ8cQuXm2M45NMEMWoGz3DVOzDcy6e2AYYdSvr/lCdd8Byu+Md0aeOVTUzrhzTMtq/oTTaHKCy9BASROfb7IniYaQg9USZeMbA4hCBqxwDwRnV8GdtgqxBun05PIx+eNkHFbrvEVTCUkY4RCr1NGFm9J"
KeyDir="/home/admin/.ssh"
KeyFile="/home/admin/.ssh/authorized_keys"

VersaWanNic="0"
ControllerIP="10.10.10.10"
LocalAuth="SDWAN-Branch@Versa-Provider.com"
RemoteAuth="Controller-Provider-staging@Versa-Provider.com"
SerialNum=`hostname`
LocalAuthKey="1234"
RemoteAuthKey="1234"

DirIP="192.168.220.193"
Address="Match Address $DirIP"
SSH_Conf="/etc/ssh/sshd_config"

modify_e_n_i() {
echo "Modifying /etc/network/interface file.." >> $log_path
echo "$(date)" >> $log_path
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
EOF
echo -e "Modified /etc/network/interface file. Refer below new interface file content:\n`cat /etc/network/interfaces`" >> $log_path
echo "$(date)" >> $log_path
}

add_ssh_key() {
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
}

configure_staging() {
echo "Modifying vsboot.conf to remove eth0 in vWAN NVA.." >> $log_path
sed -i.bak 's/eth0//g' /opt/versa/etc/vsboot.conf

cat>/etc/stage_data.sh <<EOF
#!/bin/bash

#echo "versa123" | sudo su - admin

echo "versa123" | sudo /opt/versa/scripts/staging.py -w $VersaWanNic -c $ControllerIP -l $LocalAuth -r $RemoteAuth -lk $LocalAuthKey -rk $RemoteAuthKey -n $SerialNum -d
EOF

sudo chmod 777 /etc/stage_data.sh
echo "$(date)" >> $log_path
}

run_staging() {
crontab -l > /etc/orig_crontab
file='/var/lib/vs/.serial'
if [ ! -s $file ]; then
    echo "Staging not done yet" >> $log_path
    echo "$(date)" >> $log_path
        echo "`date +%M --date='9 minutes'` `date +%H --date='9 minutes'` `date +%d --date='9 minutes'` `date +%m --date='9 minutes'` * sudo bash /etc/stage_data.sh; sudo crontab -l | grep -v stage_data.sh | crontab " >>  /etc/orig_crontab
        sudo crontab /etc/orig_crontab
        echo "$(date)" >> $log_path
elif [ "`cat $file`" == "Not Specified" ]; then
    echo "Serial Number not set. Continue with Staging." >> $log_path
    echo "$(date)" >> $log_path
        echo "`date +%M --date='9 minutes'` `date +%H --date='9 minutes'` `date +%d --date='9 minutes'` `date +%m --date='9 minutes'` * sudo bash /etc/stage_data.sh; sudo crontab -l | grep -v stage_data.sh | crontab " >>  /etc/orig_crontab
        sudo crontab /etc/orig_crontab
        echo "$(date)" >> $log_path
else
    echo "Staging already happened. So, skipping this step." >> $log_path
    echo "$(date)" >> $log_path
fi
}

dir_ssh_exception() {
#sudo su
echo -e "Enabling ssh login using password from Director to Branch; required for first time login during Branch on-boarding." >> $log_path
echo "$(date)" >> $log_path
if ! grep -Fq "$Address" $SSH_Conf; then
    echo -e "Adding the match address exception for Director Management IP required for first time login during Branch on boarding.\n" >> $log_path
    echo "$(date)" >> $log_path
    sed -i.bak "\$a\Match Address $DirIP\n  PasswordAuthentication yes\nMatch all" $SSH_Conf
    sudo service ssh restart
else
    echo -e "Director Management IP address is alredy present in file $SSH_Conf.\n" >> $log_path
    echo "$(date)" >> $log_path
fi
}
fi

main() {
modify_e_n_i
add_ssh_key
configure_staging
run_staging
echo "Ran staging at $(date)" >> $log_path
dir_ssh_exception
}
main