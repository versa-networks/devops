
Automation Script to Generate Zone/DoS traffic

```
Author Swetha Ragunath
```
```
A Vishnu Arun Chandar
```
```
Tools Used Python
```
```
Hping
```
```
Nmap
```
```
Verified by Arun Chandar
```
```
Purpose:
Traffic Generation:
DOS-Protection:
Zone Protection:
Configuration Template:
```
## Purpose:

The intention of the tool is to enable quick simulations of respective Zone-Protection and DOS test cases during
the below scenarios:

```
Customer Demos
SD-Security Zone/DoS Protection testing
Zone/DoS Protection from VSA Client
Quick Functional testing on new releases
```
The tool tries to cover all possible scenarios to demonstrate Zone-Protection & DOS related tests using
Python. There will also be a Service Template which can be cloned/exported to any environments for re-usability.

## Traffic Generation:

For Testing Zone Protection profile make sure the ingress interface belongs to a zone and respective Zone
protection profile is mapped. And for DoS Protection profiles make sure the ingress and egress interfaces belongs
to different zones or in case if both the interfaces belongs to same zone, make sure the interfaces belongs to
different subnets.

Prerequisites:

Following tools needs to be installed on Ubuntu Desktop-18.04.

```
Python
Hping3 – sudo apt-get install hping
Nmap – sudo apt-get install nmap
VSA Client(as per use-case) – versa-sase-client-7.4.2-0-x86_64.deb
```
Ubuntu VSA Client download link: https://versanetworks.app.box.com/s/nvtbn8ty27q90clhxqhzb13kny7bg3t5/folder
/

```
NOTE: Zone Protection does not work when attack traffic generated from VSA client device
```
```
Bug-id: http://bugzilla.versa-networks.com/show_bug.cgi?id=
```
```
Traffic-generation script: ZP_DoS_trafficgen.py
For generating traffic, copy the attached python file to Ubuntu-18.04 PC from where you’ll generate traffic.
Once copied, run the file from the Ubuntu Terminal using:
```
```
sudo python3 <file_name.py>
```
```
This will prompt you to choose the traffic generation profile.
```
Example scenario used for this wiki section:


### 1.

### 2.

### 3.

### 4.

### 5.

Here, for this script demonstration, we use an Ubuntu Desktop hosted in VOS Branch LAN network to simulate attack
traffic generation. The VOS gateway is configured with Zone/DoS Protection profiles. Attacks here are simulated
for SDWAN Overlay traffic, that is, anomalous packets are launched from Ubuntu machine (LAN) towards another
SDWAN-Branch LAN network as shown in topology.

( Please refer the service template attached later in this section to view the Zone/DoS Protection rules )

The purpose is to use the script to easily generate any anomalous traffic from Ubuntu machine (LAN) to verify the
Firewall rule actions configured in the VOS device.

## DOS-Protection:

```
Execute the python script & select “1” for DoSProtection traffic generation profile,
```
```
Under DoS, we have the following attack profiles:
```
```
TCP Flood
UDP Flood
ICMP Flood
SCTP Flood
Other-IP Flood
```
```
Select any of the flood profiles as required
```
```
For example:
```
```
Selecting “1” will ask for, Target/Destination IP, TCP Destination Port and the duration of flood
```

```
Enter the required details & press ENTER to begin traffic generation for the specified IP/Port/Duration,
```
NOTE: Traffic will automatically terminate after the given duration

```
DoS-Policy verification:
```
DoS rule hit-counts & the dropped TCP SYN counts on VOS device can be verified from Director GUI,

Go to the appliance & navigate to Monitor -> Services -> SFW/NGFW -> DoS Policies :

```
The same can be viewed from VOS device cli using the command,
```
"show orgs org-services <Org-Name> security dos-policies rules dos-policy-stats"


```
Similarly any of the other DoS traffic-profiles can be used,
```
```
Once done, we can either choose to EXIT from the script (or) continue with the traffic-gen
```
## Zone Protection:

Under ZoneProtection, we have the below categorized traffic-gen profiles for the different types of attack
/anomalous traffic that will be detected by VOS Zone Protection module

```
Scan Flood Packet-based Attack (TCP/UDP/IP/ICMP)
```
```
TCP Scan
```
```
UDP Scan
```
```
Host-Sweep
```
```
TCP SYN Flood
```
```
UDP Flood
```
```
ICMP Flood
```
```
SCTP Flood
```
```
Other-IP Flood
```
```
ICMP Fragmentation
```
```
ICMP Ping Zero ID
```
```
Non-SYN TCP
```
```
IP Spoofing
```
```
IP Fragmentation
```
```
Record-Route
```
```
Strict-source Routing
```
```
Loose-source Routing
```
```
Timestamp
```
Below are few examples to demonstrate how to use the python script on a LAN device for traffic generation

```
ICMP Ping Zero ID
Host-Sweep Scan
Strict-source Routing
```
```
ICMP Ping Zero ID
```
```
Run the script using python3 & enter " 2 " to view Zone Protection traffic profiles
```

```
Input the value " 10 " for Ping Zero ID ICMP traffic & type the Target IP address & time duration (in
seconds) in the prompt, press ENTER to initiate traffic-gen
```
NOTE: Traffic is automatically terminated after the specified duration & takes us back to the list of ZP
traffic profiles.

```
Once done, we can either choose to EXIT from the script as shown below (or) continue with the
traffic-gen
```
```
Verification:
```

Use the below command on VOS device to check the number of anomalous data packets detected and dropped by
the configured Zone Protection profile

"show orgs org-services <org-name> security profiles zone-protection zone-protection-statistics"

The same can be verified from Director GUI, go to the appliance & navigate to Monitor -> Services -> SFW
/NGFW -> Zone Protection as shown:

Host-Sweep Scan

```
As above, run the script using python3, enter " 2 " to get into Zone Protection traffic profiles
Type " 3 " & press ENTER for Host-Sweep Scan. In the prompt, input the Target Subnet x.x.x.x/x to be scanned,
the scan duration (in sec) & press ENTER to begin traffic-gen
```

NOTE: Scan is automatically terminated by the script after the specified time

```
Verification:
```
Use the below command on VOS device to check the number of anomalous data packets detected and dropped by
the configured Zone Protection profile

"show orgs org-services <org-name> security profiles zone-protection zone-protection-statistics"

Additionally, the Scan & Flood attack traffic detected by VOS can also be verified from the Versa Analytics
Dashboard under 'Threat Detection' as shown below (provided LEF is configured)


Strict-source Routing

```
Follow same procedure to enter into ZoneProtection section of the script & choose " 15 " from the list of
Zone Protection traffic profiles as shown below
Type the Destination IP address & time duration for which traffic is to be forwarded & press ENTER to begin
traffic-gen
```
Verification:

Use the below command on VOS device to check the number of anomalous data packets detected and dropped by
the configured Zone Protection profile

"show orgs org-services <org-name> security profiles zone-protection zone-protection-statistics"


```
(OR) From Director GUI, got to the appliance & navigate to Monitor -> Services -> SFW/NGFW -> Zone
Protection :
```
NOTE: Please feel free to try other available options and share feedback for any improvements.

## Configuration Template:

You can use this template as reference or import this predefined service template into your test environment &
modify as necessary

Service template (Type - Stateful) with Zone Protection & DOS Protection policies - SFW_Zone_and_DoS.cfg

NOTE:

```
Zone Protection: Map the predefined profile to your respective zones as necessary
DoS Protection: Map either the predefined 'Aggregate' or 'Classified' DoS profiles to the DoS policy
rule based on use-case (by default, classified profile is configured)
Map the Profiles matching your environment like mapping Zone Protection profiles to a desired Zone of your
choice as per use-case. Similarly when using DOS profile, make sure to configure DoS rule match conditions
as per your use-case.
```



