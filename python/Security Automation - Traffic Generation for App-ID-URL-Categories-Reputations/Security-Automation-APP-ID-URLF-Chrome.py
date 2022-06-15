#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:30:19 2022

@author: arunchandar, swetha, vishnu
"""
import webbrowser
import platform
import time
TestProfile=1
if platform.system().lower()=='windows':
    bpath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
elif platform.system().lower()=='linux':
    bpath = "/usr/bin/google-chrome"
def webapp(url):
    webbrowser.register('chrome',None,webbrowser.BackgroundBrowser(bpath))
    webbrowser.get('chrome').open_new(url)
while (TestProfile!="4"):
 print("\n Please choose a feature for traffic-gen: \n")
 TestProfile=input(" \t \t 1. App-FW Profile \t 2. URLF Profile \t 3. EXIT-SCRIPT \n")
 while TestProfile=="1":
  print("\n\t\t ========       AppFW-TrafficGen       ======== ")
  option=input (" Select type: \n\t\t 1. Predefined list \t 2. Enter WebApp URL manually \t 3. Exit AppFW-TrafficGen\n")
  while (option=="1"):
   app_options=input("AppFW Traffic Options:\n\t \t 1. Applications  \t 2. Application Groups \n\t\t 3. Application Filter \t  4. Back-To-Main-Menu \n")
   while app_options=="1":
    print("\n Select any App:\n")
    app=input("\t \t 1. AWS \t 2. Flipkart \t 3. Facebook \t 4. Facebook Video \t 5. Facebook Games \t 6. Whatsapp \n \t \t 7. Instagram \t 8. Bittorrent \t 9. Kproxy \t 10. Google_Ads \t 11. Youtube \t\t 12. Netflix \n \t\t 13. Sharepoint  14. Powerpoint 15. Outlook \t 16. MS-Excel \t\t 17. MS-Teams \t\t 18. Google-groups \n \t \t 19. GoBack \n")
    if app=="1":url= 'https://www.aws.amazon.com/console/'
    if app=="2":url= 'https://www.flipkart.com'
    if app=="3":url= 'https://www.facebook.com'
    if app=="4":url= 'https://www.facebook.com/chotoonz/videos/funny-cartoons-for-kids/505985553540399/'
    if app=="5":url= 'https://www.facebook.com/games/'
    if app=="6":url= 'https://www.whatsapp.com'
    if app=="7":url= 'https://www.instagram.com'
    if app=="8":url= 'https://www.bittorrent.com'
    if app=="9":url= 'https://www.kproxy.com'
    if app=="10":
     print("Opening ndtv.com ==> You should see Adds Getting Blocked")     
     url= 'https://www.ndtv.com'
    if app=="11":url= 'https://www.youtube.com'
    if app=="12":url= 'https://www.netflix.com'
    if app=="13":url= 'https://versanetworks.sharepoint.com/'
    if app=="14":url= 'https://www.office.com/launch/powerpoint'
    if app=="15":url= 'https://outlook.office.com/mail/inbox'
    if app=="16":url= 'https://www.office.com/launch/excel'
    if app=="17":url= 'https://teams.microsoft.com/'
    if app=="18":url='https://groups.google.com/my-groups'
    if app=="19":
     print("\n \t \t ~~~~~~~~~ Exiting Applications ~~~~~~~~~ \n")
     break
    webapp(url)        
   while app_options=="2":
    print("\n Select any App-Group :\n")
    app=input("\t \t 1. Amazon-Apps  \t  2. Google-Apps \n \t\t 3. Social-Media-Apps \t  4. Office365-Apps \n \t\t 5. Exit \n")
    if app=="1":
        print(" Opening Amazon-Apps \"Aws\" \"Chime\" \"Amazon Prime\"  \"Amazon Music\" ")        
        url = ['https://www.aws.amazon.com/console/',
              'https://app.chime.aws/meetings',
              'https://www.primevideo.com/',
              'https://music.amazon.in/' ]
        for u in url:
            webapp(u)
    if app=="2":
        print(" Opening Google-Apps  \"Gmail\" \"Google-Drive\" \"google-analytics\" ")        
        url= ['https://www.gmail.com',
              'https://drive.google.com',
              'https://analytics.google.com/analytics/web/' ]
        for u in url:
            webapp(u)
    if app=="3":
        print(" Opening Social-Media Apps  \"Facebook\" \"Tinder\" \"Orkut\" ")        
        url=['https://www.facebook.com',
             'https://tinder.com',
             'http://www.orkut.com/']
        for u in url:
            webapp(u)     
    if app=="4":
        print(" Opening O365-Apps  \"Sharepoint\"  \"Powerepoint\"  \"Outlook\"  \"MS-Excel\" \"MS-Teams\" \n ")
        print(" \t\t ******** Please login to O365 Account ********\n ")
        print(" \t\t NOTE:  Will wait for 30 seconds for you to login, before opening rest of O365 Sites\n ")
        url= 'https://www.office.com/launch/powerpoint'
        webapp(url)
        time.sleep(30)
        url = ['https://versanetworks.sharepoint.com/',
              'https://outlook.office.com/mail/inbox',
              'https://www.office.com/launch/excel',
              'https://teams.microsoft.com/']
        for u in url:
            webapp(u)     
    if app=="5":
     print(" \n \t \t ~~~~~~~~~ Exiting Application Groups ~~~~~~~~~ \n ")
     break
   while app_options=="3":
    print("\n Select any App-Filter category :\n")
    app=input("\t \t 1. High-Risk-Applications  \t 2. Non-Business Apps \n \t\t 3. Business Apps \t\t 4. Web-Browsing \n\t\t 5. Exit \n")
    if app=="1":
     print(" !WARNING ! \n Opening Predefined High Risk Applications \"Brightcove\" \"2shared\" \" 4tube\" \"Gigatribe\" ")
     url= ['https://www.brightcove.com',
           'https://www.2shared.com/',
           'https://www.4tube.com/',
           'https://www.gigatribe.com/']
     for u in url:
         webapp(u)
    if app=="2":
     print(" ! WARNING ! \n Opening Predefined Non-Business Applications \"01net\" \"Baidu\" \" Bitlord\" \"Cartoonnetwork\" \n The above apps may possess Risk") 
     url= ['https://www.01net.com',
           'https://baidu.com',
           'https://www.bitlord.com',
           'https://www.cartoonnetwork.com']
     for u in url:
         webapp(u)
    if app=="3":
     print("Opening Predefined Business Applications  \"mcafee\" \"webex\" ")     
     url=['https://www.mcafee.com/en-in/index.html',
          'https://www.webex.com/']
     for u in url:
         webapp(u)
    if app=="4":
     print("Opening Predefined Web-Browsing Applications \"bing\" \"mailru\" \" anz\" ")
     url=['https://www.mail2000.co',
          'https://mail.ru/',
          'https://www.anz.com.au']
     for u in url:
         webapp(u)     
    if app=="5":
     print("\n \t \t ~~~~~~~~~ Exiting Application Filters ~~~~~~~~~ \n")
     break
   if app_options=="4":
       break
  while (option=="2"):
   url=input("\nEnter the URL : \t ")
   webbrowser.open_new(url)
   print(" \n \t \t ~~~~~~~~~ Exiting Manual Entry ~~~~~~~~~ \n")
   break
  if option=="3":
   print("\n \t \t ============================== Exiting AppFW-TrafficGen ============================== \n ")
   break
 while (TestProfile=="2"):
   uprof=1
   while (uprof!="4"):
     print("\n\t\t ========       URLF-TrafficGen       ======== ")
     uprof=input (" URLF Traffic Options: \n\t\t 1. URL Categories \t 2. Reputation-Based \n \t \t \t \t (OR) \n \t \t \t 3. Enter URL manually \n \t \t \t \t (OR) \n \t \t \t 4.EXIT URLF-TrafficGen \n")
     while (uprof=="1"):
      print("\n Select any category :\n")
      cat=int(input(" \t  1. Shopping \t \t 2. Social-Network \t 3. job_search \t 4. gambling \t 5. adult-sites  \n \t  6. Malware sites \t 7. weapons \t \t 8. dating \t 9. auctions \t 10. proxy-sites \n \t 11. Goto Main menu \n"))
      while (cat==1):
       site=input(" \t \t 1. Amazon \t \t 2. Flipkart \t \t 3. Myntra \t \t 4. Goto another category \n")
       if site=="1": url= 'https://www.amazon.com'
       if site=="2": url = 'https://www.flipkart.com'
       if site=="3": url= 'https://www.myntra.com'
       if site=="4":
        print("\n\t\t --------  Exiting Shopping category  --------- \n")
        break
       webbrowser.open_new(url)
      while (cat==2):
       site=input(" \t \t 1. Facebook \t \t 2. Instagram \t \t 3. Twitter \n \t \t 4. Whatsapp \t \t 5. Telegram \t \t 6. Goto another category \n")
       if site=="1": url= 'https://www.facebook.com'
       if site=="2": url = 'https://www.instagram.com'
       if site=="3": url= 'https://www.twitter.com'
       if site=="4": url= 'https://www.whatsapp.com'
       if site=="5": url= 'https://telegram.org'
       if site=="6":
        print("\n\t\t --------  Exiting Social-Network category  --------- \n")
        break
       webbrowser.open_new(url)
      while (cat==3):
       site=input(" \t \t 1. LinkedIn \t \t 2. Naukri \t \t 3. Monster \t \t 4. Goto another category \n")
       if site=="1": url= 'https://www.linkedin.com'
       if site=="2": url = 'https://www.naukri.com'
       if site=="3": url= 'https://www.monster.com'
       if site=="4":
        print("\n\t\t --------  Exiting JobSearch category  --------- \n")
        break
       webbrowser.open_new(url)
      if cat==5: url= 'https://www.playboy.com'
      if cat==10:url='https://www.kproxy.com'
      if cat==4: url= 'https://www.bet365.com'
      if cat==6: url= 'https://astalavista.box.sk'
      if cat==7: url= 'https://www.grabagun.com'
      if cat==8: url= 'https://www.match.com'
      if cat==9: url= 'https://www.ebay.com'
      if cat==11:
       print("\n\t\t ~~~~~~~~~ Exiting URLF Category-based profile ~~~~~~~~~ \n")
       break
      if cat>3:
       webbrowser.open_new(url)
     while (uprof=="2"):
      print("\n Select a Reputation type :\n")
      cat=input(" \n\t \t 1. Trustworthy \t 2. moderate_risk \n\t\t 3. Suspicious \t\t 4. High-risk \n\t \t 5. Enter URL manually \t 6. Goto Main menu \n") 
      if cat=="1": url= 'cricbuzz.com'
      if cat=="2": url= 'adform.com'
      if cat=="3": url= 'https://www.prochoiceamerica.org/'
      if cat=="4": url= 'http://www.proxify.com/'
      if cat=="5": url= input("\n \t Type website URL: \t")
      if cat=="6":
       print("\n\t\t ~~~~~~~~~ Exiting URLF Reputation-based profile ~~~~~~~~~ \n")
       break
      webbrowser.open_new(url)
     if uprof=="3":
      url= input("\n \t Type website URL: \t")
      webbrowser.open_new(url)
      print(" \n \t \t ~~~~~~~~~ Exiting Manual Entry ~~~~~~~~~ \n")
     if uprof=="4":
      print("\n\t\t ============================== Exiting URLF-TrafficGen ============================== \n")
      break
   break
 if TestProfile=="3":
  print("\n\n ************************************************* EXITING TRAFFIC-GEN SCRIPT ************************************************ \n")
  break

   
    
       
