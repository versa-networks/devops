## Purpose of the script
- access-rules-edit.py : The script will inspect every access rules on a CPE and execute one of the actions below :

1) display           : Display the rule name
2) set.log           : Set logging on the rule 
3) set.log.profile   : Set a log profile on the rule
4) set.rule.disable  : Disable the rule
5) set.rule.enable   : Enable the rule

In addition the script can execute those action for a subset of the existing rules based on a filter such as:

1) has.no.log           : Match rules with no log settings
2) has.log              : Match rules with log settings
3) has.no.log.profile   : Match rules with no log-profile settings
4) has.log.profile      : Match rules if a log-profile exist
5) is.enable            : Match enabled rules
6) is.disable           : Match disabled rules
7) none                 : Match any rules

## Installation and Dependencies
You will need python3 as well as differents python package. They can be installed locally with pip3
```
pip3 install json
pip3 install requests
pip3 install urllib3
pip3 install argparse
```

## How does it work ?
Before you get started make sure you have the following information:
1) The IP address of the Director where the CPE is managed.
2) The Director Administrator login ( Default is Administrator)
3) The Director Administrator password ( Default is versa123 )
4) The name of the CPE where the change ( or rule review ) is required.
5) The name of the organization where the CPE is managed
6) The name of the Access Policy group where the rules are located ( Default is Default-Policy )

![Screenshot](demo-access-rules-before.jpg)

Worse case execute the script with the --help flag to remind you how it works.
```
% python3 access-rules-edit.py --help
usage: access-rules-edit.py [-h] [--ip IP] [--device DEVICE] [--org ORG] [--group GROUP] [--user USER] [--password PASSWORD] [--action ACTION]

Script to change the settings of a VOS CPEs accross ALL its access policies

optional arguments:
  -h, --help           show this help message and exit
  --ip IP              IP address of Director
  --device DEVICE      Branch Device name
  --org ORG            Organization name
  --group GROUP        Policy Group Name
  --user USER          GUI username of Director
  --password PASSWORD  GUI password of Director
  --action ACTION      Action to be taken on the offending rules. Use --action help for details
  --filter FILTER      Filter to be applied to limit the scope of the action. Use --filter help for details
```
   
The example below will display every rules from the CPE BRANCH-11 where log-profile are missing.
```
sly@MacBook versa-policy % python3 access-rules-edit.py --user Administrator --password versa123 --ip 10.43.43.254 --device BRANCH-11 --org Versa --group Default-Policy --action display --filter has.no.log.profile
--> allow-web has NO log enable
--> allow-web has NO log profile
--> deny-facebook has NO log enable
--> deny-facebook has NO log profile
--> deny-youtube has NO log enable
--> deny-youtube has NO log profile
--> allow-dns has NO log enable
--> allow-dns has NO log profile
--> allow-ssh has NO log enable
--> allow-ssh has NO log profile
```

At this stage, you can confirm that you want to set the log knob on each rule where it's missing.
```
sly@MacBook versa-policy % python3 access-rules-edit.py --user Administrator --password versa123 --ip 10.43.43.254 --device BRANCH-11 --org Versa --group Default-Policy --action set.log --filter has.no.log.profile
--> setting log on rule allow-web
--> setting log on rule deny-facebook
--> setting log on rule deny-youtube
--> setting log on rule allow-dns
--> setting log on rule allow-ssh
```

And also set a the default log profile so logs get sent to Director for monitoring..
```
sly@MacBook versa-policy % python3 access-rules-edit.py --user Administrator --password versa123 --ip 10.43.43.254 --device BRANCH-11 --org Versa --group Default-Policy --action set.log.profile --filter has.no.log.profile
--> setting log profile on allow-web
--> setting log profile on deny-facebook
--> setting log profile on deny-youtube
--> setting log profile on allow-dns
--> setting log profile on allow-ssh
```

At the end you should get the following result in the Director WebUI. 
![Screenshot](demo-access-rules-after.jpg)

Congrat you just saved yourself 5 min of your precious time :)
