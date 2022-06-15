#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:30:19 2022

@author: arunchandar, swetha, vishnu
"""
#!/usr/bin/env python
import os
import subprocess
import signal
import time
TestProfile=1

while (TestProfile!="3"):
 print("\n Please choose the feature to be tested :\n")
 TestProfile=input(" \t \t 1.DoSProtection \t 2. ZoneProtection \t 3. END-SCRIPT \n")

 if TestProfile=="2":
   value=1
   while (value!="20"):
     time.sleep(3)
     print("\n Please choose the traffic-gen profile :\n")
     value=input("Scan: \t \t 1.TCP Scan \t \t 2.UDP Scan \t \t 3.HostSweep \t \nFlood: \t \t 4.TCP Flood \t \t 5.UDP Flood \t \t 6.ICMP Flood  \t \t 7.SCTP Flood \t \t 8.Other-IP Flood \t \nProto options: \t 9.ICMP Fragmention \t 10.ICMP Ping Zero ID \t 11.Non-SYN TCP \t \nIP Options: \t 12.IP Spoofing \t 13.IP Fragmention \t 14.Record-Route \t  \n \t \t 15.Strict-src-Routing \t 16.Loose-src-Routing \t 17.Timestamp \t \n \t\t 20.EXIT \n")

     if value=="1":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting TCP Scan  ********* ")
      #os.system('nmap -sS dst_ip')
      p=subprocess.Popen(["nmap","-sS",dst_ip])
      print("\n Scan automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Scan Terminated  *********  \n")

     if value=="2":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting UDP Scan  ********* ")
      p=subprocess.Popen(["nmap","-sU",dst_ip])
      print("\n Scan automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Scan Terminated  *********  \n")

     if value=="3":
      dst_ip=input("\n \t Enter Target/Destination Subnet x.x.x.x/x : ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting HostSweep  ********* ")
      p=subprocess.Popen(["nmap","-sn",dst_ip])
      print("\n Scan automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  HostSweep Terminated  *********  \n")

     if value=="4":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      dst_port=input("\n \t Enter TCP Destination Port: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting TCP SYN Flood  ********* ")
      p=subprocess.Popen(["hping3","-S",dst_ip,"-p",dst_port,"--faster"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

     if value=="5":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting UDP Flood  ********* ")
      p=subprocess.Popen(["hping3","-2",dst_ip,"--faster"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

     if value=="6":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      src_ip=input("\n \t Enter Source IP Address: ")
      #t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting ICMP Flood  ********* ")
      for i in range(20,220):
         p=subprocess.Popen(["hping3","-1",dst_ip,"--fast","--icmp-ipsrc",src_ip],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      #print("\n Flood automatically terminates within",t,"seconds \n")
      #time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      q=subprocess.Popen(["killall","hping3"])
      print("\n **********  Flooding Terminated  *********  \n")

     if value=="7":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting SCTP Flood  ********* ")
      p=subprocess.Popen(["hping3","-n",dst_ip,"-0","--ipproto","132","--flood","--destport","7654"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

     if value=="8":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting Other-IP Flood  ********* ")
      p=subprocess.Popen(["hping3","-n",dst_ip,"-0","--ipproto","47","--flood","--destport","7654"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

     if value=="9":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending Fragmented ICMP Packets ********* ")
      p=subprocess.Popen(["hping3",dst_ip,"-x","--icmp"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="10":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending Ping Zero ID Packets ********* ")
      p=subprocess.Popen(["hping3","-1",dst_ip,"--icmp-ipid","0"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="11":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending Non-SYN TCP Packets ********* ")
      p=subprocess.Popen(["hping3","-R",dst_ip],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="12":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      src_ip=input("\n \t Enter Spoofed Source IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Initiating Source Spoofed Traffic  ********* ")
      p=subprocess.Popen(["hping3","-1",dst_ip,"-a",src_ip],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="13":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending Fragmented IP Packets  ********* ")
      p=subprocess.Popen(["hping3","-S",dst_ip,"-f"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="14":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending IP Packets ********* ")
      p=subprocess.Popen(["hping3",dst_ip,"--rroute","--icmp"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="15":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending IP Packets (Strict-source Routing) ********* ")
      p=subprocess.Popen(["nping","--tcp",dst_ip,"--ip-options","S","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="16":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending IP Packets (Loose-source Routing) ********* ")
      p=subprocess.Popen(["nping","--tcp",dst_ip,"--ip-options","L","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="17":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Sending IP Packets (Timestamp) ********* ")
      p=subprocess.Popen(["nping","--tcp",dst_ip,"--ip-options","T","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      print("\n Traffic automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Traffic Terminated  *********  \n")

     if value=="20":
      print("\n\n =======  Exiting Zone-Protection Traffic Profile  ========== \n")
      break

 if TestProfile=="1":
   value=1
   while (value!="4"):
    time.sleep(3)
    print("\n Please choose the traffic-gen profile :\n")
    value=input(" \t \t 1.TCP Flood \t 2.UDP Flood \t \t 3.ICMP Flood \n \t \t 4.SCTP Flood \t 5.Other-IP Flood \t 6.EXIT \n")

    if value=="1":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      dst_port=input("\n \t Enter TCP Destination Port: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting TCP SYN Flood  ********* ")
      p=subprocess.Popen(["hping3","-S",dst_ip,"-p",dst_port,"--faster"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

    if value=="2":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      dst_port=input("\n \t Enter UDP Destination Port: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting UDP Flood  ********* ")
      p=subprocess.Popen(["hping3","-2",dst_ip,"-p",dst_port,"--faster"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

    if value=="3":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      src_ip=input("\n \t Enter Source IP Address: ")
      #t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting ICMP Flood  ********* ")
      for i in range(20,220):
       p=subprocess.Popen(["hping3","-1",dst_ip,"--fast","--icmp-ipsrc",src_ip,],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
      #print("\n Flood automatically terminates in",t,"seconds \n")
      #time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      q=subprocess.Popen(["killall","hping3"])
      print("\n **********  Flooding Terminated  *********  \n")

    if value=="4":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting SCTP Flood  ********* ")
      p=subprocess.Popen(["hping3","-n",dst_ip,"-0","--ipproto","132","--flood","--destport","7654"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

    if value=="5":
      dst_ip=input("\n \t Enter Target/Destination IP Address: ")
      t=int(input("\n \t Enter time duration (in sec) for which traffic is to be generated: "))
      print (" \n **********  Starting Other-IP Flood  ********* ")
      p=subprocess.Popen(["hping3","-n",dst_ip,"-0","--ipproto","47","--flood","--destport","7654"])
      print("\n Flood automatically terminates in",t,"seconds \n")
      time.sleep(t)
      p.send_signal(signal.SIGINT)
      p.terminate()
      print("\n **********  Flooding Terminated  *********  \n")

    if value=="6":
      print("\n\n =======  Exiting DOS-Protection Traffic Profile  ========== \n")
      break

 if TestProfile=="3":
    print("\n\n =======  EXITING TRAFFIC GENERATION  ========== \n")
    break
