Security Posture Evaluation Automation Script – User Guide
==========================================================

  **Author**            [Swetha Ragunath](file:///C:\display\~swetha.r) [A Vishnu](file:///C:\display\~vishnu.a) [Snekha Ravichandran](file:///C:\display\~snekhar) [Arun Chandar](file:///C:\display\~arunc)
  -------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Architected By**    [Arun Chandar](file:///C:\display\~arunc)
  **Verified By**      [Ashwani Parashar](file:///C:\display\~ashwani)

  ---------------------------------
  -   #### **Purpose**
  
  -   #### **What the tool does**
  
  -   #### **Report Dashboard**
  
  -   #### **How-to Guide**
  
  -   #### **Summary of Tests**
  
  ---------------------------------

#### **Purpose:**

-   This script lets us to quickly assess the security posture of any
    end-user device & evaluate whether their firewall solutions are
    efficient enough to stop malicious traffic from affecting their
    devices.

-   It can also be used during Customer Demos to demonstrate the working
    of Versa Security features for any SWG/SASE scenarios

-   This is a light-weight tool that is easy to install & quick in
    execution

-   Supported in any Windows 10, MAC, Ubuntu OS devices

NOTE: Provided Service Templates can be imported to any
Versa Director just by changing
the *&lt;org-name&gt;***,** *certificate/key* for SSL Decryption &
SNAT-pool config for Cloud-Lookup

#### Latest Version Update:

<<<<<<< HEAD
**v6.2     **-&gt;  Updated Geo-location based IP list for IP-Filtering
traffic-gen
=======
**v6.3     **-&gt;  Updated IP list for IP-Filtering traffic-gen. A predefined 
csv file is also available within Tool folder to generate Bad IP Reputation traffic
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

**v6.0     **-&gt;  1) 'Internet Reachability Check' has been included
prior to traffic generation

             2)  Tool lets you to generate web-traffic based on an input
csv file which has a list of Categories/URLs. A predefined csv file is
also available within Tool folder to generate safe/legitimate traffic

#### **What the tool does:**

-   Lets you to generate Safe/Legitimate web-traffic from the user
    machine based on an input csv file

-   Lets you to generate anomalous/malicious traffic from the user
    machine to test any of the following Next-Gen Firewall features:

    -   URL Filtering

    -   IP Filtering  (Reputation & Geo-location based)

    -   Anti-Virus

    -   IDP (Versa IPS Engine)

**NOTE:** *Ideally, the execution time is approximately within 3-4
minutes*

-   Once the traffic-generation is completed, a report will be
    automatically generated with the overall assessment results,
    separately for each of the modules. Python DASH is used for this
    purpose.

#### **Report Dashboard:**

-   Evaluation Report will be displayed in a web GUI, i.e., a simple
    HTTP web-page, with interactive data visualizations for easy
    interpretation

-   Seperate tabs are available for each module – Legit Websites, URL-F,
    IP-Filtering, AV, IDP

-   Each security module tab will have:

    -   Security Risk Rating (Critical/ High-Risk/ Moderate-Risk/
        Low-Risk)

    -   Overall Traffic Statistics

    -   Block vs Bypass stats for respective malicious websites/payload

#### **How-to Guide:**

-   Download "Security_Posture_Evaluation_Tool.zip" to your PC & extract all the contents

-   Make sure Python3 & python-pip is installed in the PC where you want
    to use the script

-   Installing tool prerequisites :

**       1)‘***requirements.txt’* can be used to automatically install
dependent python packages. Open command prompt in your laptop & give the
following command,

           1. In Windows OS,

*              **pip install -r &lt;path/to/requirements.txt&gt;***

           2. In Linux/Ubuntu/ MAC OS

*              **sudo python3 -m pip install -r
&lt;path/to/requirements.txt&gt; ***

         2) Install dnspython library using

> ***pip3 install dnspython --trusted-host
> [files.pythonhosted.org](http://files.pythonhosted.org) --trusted-host
> [pypi.org](http://pypi.org) --trusted-host
> [pypi.python.org](http://pypi.python.org)***
>
> ***Note:** In case if any package installation fails, try “pip3
> install &lt;package-name&gt;” to install the package manually *

-   Once the installation is complete, PC is now ready to use the script

****IMPORTANT NOTE:**  **Particularly when using the script for AV
traffic-gen, please make sure End-point Security is disabled in user PC
(Windows Defender 'Virus & Threat Protection' settings or similar
settings on MAC/Ubuntu)****

-   *Script Execution*

> On Windows, simply double-click on the .py file to run the script
>
> On Linux/Ubuntu/ MAC, use the command -  *python3
> SecurityEvaluationScript\_vX.py*

-   Firstly, the tool automatically checks for Internet connectivity on
    the user PC. Only if Internet connection is UP, tool moves on to
    traffic generation section, otherwise tool execution is aborted.

-   When connected to Internet, user will be prompted to choose from a
    list of options (Legit-Websites, URL-F, IP-F, AV, IDP) to generate
    corresponding traffic.

<!-- -->

-   Once you select an option, traffic generation will automatically
    begin for the selected module (The execution screen will display the
    details & the status of the real-time traffic)

-   For Safe/Legit Websites, the predefined csv file '*urls-input.csv*'
    can be given as input when tool prompts for Filename - See the above
    screenshot or reference. (NOTE: The input file should be available
    within the same folder as the python file)

***NOTE: **In case of Anti-Virus module, none of the malicious files
will be saved to local PC to avoid any security concern. It will be
immediately deleted by the script automatically, provided, End-Point
Security is already disabled/turned-OFF in user PC (Windows/MAC/Linux)
before executing Anti-Virus*

-   Once the traffic generation is completed, you can exit it & get a
    Web-based Dashboard with detailed statistical reports w.r.t each
    module. 

> You will see following message - ***Dash is running on
> [http://ip:por](http://ipport)t ***

-   Now open the displayed Dash URL <http://127.0.0.1:8084> in Chrome or
    any local web-browser

***DISCLAIMER:***  We are not responsible for any infections or
downloads or executions that may happen with the inappropriate usage of
the script

#### Summary of Tests:

1.   ***URL Filtering***

> Web-traffic towards the below listed websites will be generated

  **Category**                **URL**
  --------------------------- ---------------------------------------------------------------------
  **Gambling**                [http://mybetting.in/](https://mybetting.in/)
                              [http://10cricmedia.com/](https://10cricmedia.com/)
                              [http://www.gambling.com](https://www.gambling.com)
  **Adult and Pornography**   [http://www.playboy.com](https://www.playboy.com)
                              [http://www.redtube.com](https://www.redtube.com)
                              [http://www.pornhub.com](https://www.pornhub.com)
  **Malware**                 [http://punchbaby.com](https://punchbaby.com)
                              <http://astalavista.box.sk>
  **Weapons**                 [http://winchester.com](https://winchester.com)
                              <http://www.weapons-universe.com>
  **Dating**                  [http://www.okcupid.com](https://www.okcupid.com)
                              [http://tinder.com](https://tinder.com)
                              [http://bumble.com](https://bumble.com)
  **Auctions**                [http://www.bidspotter.com/en-us](https://www.bidspotter.com/en-us)
                              <http://www.bidfind.com>
                              [http://www.auctionzip.com](https://www.auctionzip.com)
  **Proxy**                   [http://www.kproxy.com](https://www.kproxy.com)
                              [http://proxify.com](https://proxify.com)
                              [http://www.4everproxy.com](https://www.4everproxy.com)
  **Drugs**                   [http://marijuanastocks.com](https://marijuanastocks.com)
                              [http://hightimes.com](https://hightimes.com)
                              [http://magicmushroom.com](https://magicmushroom.com)

2. *IP Filtering*

> ICMP traffic towards the following IP addresses will be generated
>
> i\. Reputation based

  **Reputation**         **IP Address**
  ---------------------- -----------------
  **Spam Sources**       68.119.100.163
<<<<<<< HEAD
                         201.172.172.201
                         134.119.216.167
  **Windows Exploits**   206.191.152.37
  **Botnets**            72.5.161.12
                         162.217.98.146
  **Phishing**           157.7.184.33
                         17.17.17.17
=======
                         61.177.173.37
                         218.28.190.77
                         185.255.96.99
                         156.146.63.145
                         5.188.210.47
                         185.190.42.200
                         134.119.216.167                       
  **Botnets**            72.5.161.12
                         206.191.152.37
                         162.217.98.146
  **Phishing**           157.7.184.33
                         17.17.17.17
                         210.211.125.204
                         103.13.140.5
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
  **Proxy**              192.95.4.124

ii\. Geo-Location Based

  **Geo-location**   **IP Address**
  ------------------ ----------------
  **Iran**           103.216.60.2
                     217.219.91.130
  **Cuba**           152.206.128.1
                     181.225.224.3
  **Syria**          109.238.152.1
                     109.238.144.8
  **North Korea**    175.45.179.45

3. *Anti-Virus*

> Below listed malicious files will be downloaded from the Git
> repository

  **File Type**   **File**
  --------------- ----------------------------------
  **com**         eicar.com
  **zip**         eicarcom2.zip
                  eicar\_com.zip
  **exe**         GlobeImposter-ransomware-EXE.exe
                  KryptikEldoradoRansomware.exe
  **vbs**         VisualBasicMalware.vbs
  **Unknown**     Blackmatter-Ransomware
                  StartPage-Adware

4\. *IDS/IPS*

> Exploits on following applications will be attempted from the user PC

  **Application**               **CVE**
  ----------------------------- -----------------
  **ElasticSearch**             CVE-2015-5531
  **Apache Flink**              CVE-2020-17519
  **Apache Struts 2**           CVE-2018-11776
  **Apache Log4j Injection **   CVE-2021-45046 


