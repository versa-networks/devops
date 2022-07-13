#!/bin/bash
log_path="/var/tmp/vos_log.txt"
sudo -S < <(echo 'versa123') hostnamectl set-hostname versa-flexvnf
sudo -S < <(echo 'versa123') hostname versa-flexvnf
if [ -f "$log_path" ]
then
    echo "vos Init script already ran earlier during first time boot.." >> $log_path
else
    touch $log_path
echo -e "vsh service check" >> $log_path    
source /etc/profile.d/versa-profile.sh
result=$(vsh status)
echo "$result" >> $log_path
echo "$result" | egrep -qi 'failed|Stopped|not'
until [ "$?" -ne 0 ]
do
    echo "Versa services not running.." >> $log_path
    sleep 20
    result=$(vsh status)
    echo "$result" | egrep -qi 'failed|Stopped|not'
done
fi
