pplications, URL-Categorisations & Reputations based

# Traffic Generation using Python Scripts

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
Verified by Arun Chandar& Ashwani Parashar
```
```
Purpose
Traffic Generation:
App-ID Filtering:
URL Filtering:
Configuration Template:
```
## Purpose

Lets assume we want to demonstrate the firewall restrictions based on pre-defined categories, reputations,
Applications, Application-filters/Groups and so on. Finding applications/urls matching the appropriate categories
like malware sites etc would be a tedious process. To reduce these efforts, this script enables us to simulate
traffic matching different url-categories, reputations, application-groups etc matching the provided service
templates config during the below scenarios:

```
Customer Demos and PoCs
SD-Security App/URLF testing
App-ID & URL Filtering for VSA/SASE use-cases
Quick Functional testing on new releases
```
The script is also designed in such a way that it enables users to simulate traffic based on the following
options:

1. Applications
2. Application-Groups
3. Application-Filters - High-Risk, Non-Business & Web-Browsing
4. URL-Categories - Shopping, Social-Network, Job-search, Gambling, Adult Content, Malware sites, Weapons,
dating etc.
5. URL-Reputations - Trustworthy, Moderate_Risk, Suspicious, High-Risk
6. Manual provisions for both Applications & URLs

Currently, the scripts are integrated with pre-defined urls that would simulate the required categories as
required like malware, weapons sites etc.

There will also be a Service Template which can be cloned/exported to any environments for re-usability.

## Traffic Generation:

Prerequisites:

```
Following tools needs to be installed on Windows 10:
```
```
Python
Web Browser (Google-Chrome)
VSA Client (for SASE use-cases)
```
```
The Scripts can be run all popular OS like Ubuntu/Linux (or) Windows as long as Chrome and Python3 is
installed.
Traffic-generation script - APP-ID_URLF_Chrome.py
Download the attached python file to a PC in your test environment from which you need to generate web-
traffic
Once copied, run the file using python3.
This will prompt you to choose one of the traffic generation profiles - Application or URL Filtering, as
shown below:
```

Example scenario used for this wiki section:

Here, for this script demonstration, we use a Windows PC installed with VSA client (7.5.6) & connected to a SASE
gateway. The gateway is enabled with NGFW & has App-ID & URLF policies configured.

( Please refer the service templates attached later in this section to view the App-ID/URL-Filtering rules )

The purpose is to use the script to easily generate the desired web-application traffic from any Windows machine
(LAN/VSA client) to verify the Next-Gen Firewall rule actions configured in the VOS device.


### 1.

### 2.

### 1.

### 2.

### 3.

## App-ID Filtering:

```
For App-ID FW, run the python script and select "1"
```
```
Selecting "1.Application FW" will take you to the below screen where you can either choose,
Predefined list - Application/Application-Group/Application-filter traffic, (or)
Manual input
```
```
Under predefined Application/App-group/App-Filter list, you can choose one of the three options -
Applications
Application Groups
Application Filter
```
```
Selecting "1.Applications" prompts you to choose a web-app from the list as shown below:
```

```
Note: O365 Applications requires login to Microsoft Account.
```
```
Choose any application from the list (1-18) as necessary. This opens the respective web-application in a
new browser tab.
```
For example, selecting "1.AWS" will open AWS console in a new Chrome tab as below

NOTE: If any additional requirements required, please leave a comment to check the feasibility to accommodate
into the script.

As per this set-up, the web-app AWS-console is set to 'allow' and hence the webpage accessible.

```
Firewall Rule hit-counts can be viewed from Director GUI as shown below, Under Monitor -> Services -> NGFW -
> Policies of VOS gateway device :
```

```
Application/Application-Groups/Application-Filter statistics can be viewed from the VOS Device using below
commands.
```
"show orgs org-services <Org-Name> application-identification statistics application brief"

"show orgs org-services <Org-Name> application-identification statistics predefined-application-group"

"show orgs org-services <Org-Name> application-identification statistics predefined-application-filter"


1.
2.
3.
4.

```
Firewall Logs can be viewed from the Analytics (provided LEF is configured)
```
```
Similar procedure applies for Application-Groups & Application-Filter as well
Under "2.Application-Groups", we have the below predefined options:
```
```
Amazon-Apps
Google-Apps
Social-Media-Apps
Office365-Apps (Requires Login to Microsoft account)
```
```
Choose any option from the list (1-4) as necessary. This opens respective web-applications in a new browser
tab.
```
```
For example, selecting " 4 " - Office365-Apps, will open all the listed web-apps (SharePoint, PowerPoint,
Outlook, MS-Excel, MS-Teams) each in a new Chrome tab as shown below
```

### 1.

### 2.

### 3.

### 4.

```
Similarly under "3.Application-Filter", we have the below predefined options:
```
```
High-Risk-Applications
Non-Business-Traffic
Business Traffic
Web-Browsing
```
```
Choose any option from the list (1-4) as necessary. This opens respective web-applications in a new browser
tab.
```
```
For example, selecting "3.Business Traffic" will open the below displayed applications(MacAfee, WebEx)in a
new Chrome tab as shown below
```
By selecting "2.Enter Web Application URL manually" from the main menu, script will prompt you to enter the URL
Manually.


### 1.

### 2.

### 3.

## URL Filtering:

```
Execute the script which opens up the python3 terminal as shown. For URL Filtering traffic profiles, type " 2
" in the prompt as below
```
```
On pressing ENTER, it displays options for traffic-gen profiles. Either choose from predefined list (1-2)
or type web-URL manually (3)
```
```
URL Categories
Reputation-Based, (OR)
Manual input
```
```
Selecting " 1 " - URL Categories profile, prompts you to choose websites from one of the below categories:
```

```
Choose any URL-category from the list (1-10) as necessary. This opens the respective websites in a new
browser tab.
```
For example, on selecting " 1 " - Shopping, lets us choose any of the listed sites: 1. Amazon, 2. Flipkart,

3. Myntra

NOTE: In this demo set-up, URL firewall action for 'Shopping' category is set to captive-action "ASK", whereas
as an exception, Amazon.com website is configured to be whitelisted in URLF profile.

To verify this,

```
Selecting " 1 " - Amazon in the terminal prompt,
```
```
As shown below, Amazon website opens in a new Chrome tab thus verifying URL whitelist action.
```
```
Similarly to verify Caption-action "ASK" for other Shopping websites, choose "3" - Myntra in the prompt as
shown,
```

Selecting "3" will open Myntra webpage in a new Chrome tab.

```
NOTE: Since captive-action is set to "ASK", the URL request redirects to captive-portal page with Ask
Form as shown below.
```
```
Clicking on 'Continue' (in captive-portal page) opens up Myntra website.
```
```
URLF profile rule hit-counts on VOS gateway can be verified using the command:
```
```
"show orgs org-services <Org-Name> security profiles url-filtering user-defined statistics <URLF-
Profile-Name>"
```

```
1.
2.
3.
4.
5.
```
```
The same can be viewed from Director GUI, go to the appliance & navigate to Monitor -> Services -> NGFW
-> URL Filtering
```
```
Similarly, any of the other URL-categories can be chosen to automatically open corresponding websites in a
new Chrome tab & the Firewall rule actions on VOS device can be verified accordingly.
```
NOTE: Category options 4-10 (as seen from above screenshot) currently have one website each & complaint in Versa
SPACK 1893

Please try all profiles & if any suggestions please leave a comment

```
Next under URLF traffic-gen profile we have Reputation-based
```
```
Reputation-Based traffic-gen profile has the following options:
```
```
Trustworthy
Moderate_risk
Suspicious
High-risk
Manual input
```
NOTE: Currently each risk-level has one website each & is complaint with Versa SPACK 1893

```
To use this, choose " 2 " (Reputation-Based) from the sub-menu within 'URL Filtering Profile'
```

```
From the displayed options (1-5), choose as desired to automatically open a corresponding website in a new
Chrome tab
```
```
Firewall rule actions corresponding to the websites accessed can be verified using the statistics command
from VOS cli (or) from Director GUI under Monitor -> Services -> NGFW -> URL Filtering of the VOS appliance
```
```
To view traffic statistics for predefined-reputations in VOS, select 'URL Reputation Predefined' from the
drop-down list as highlighted below:
```
NOTE: As per this set-up, on SASE GW, the URLF actions configured for each reputation are as follows: Trustworthy

- "ALLOW", Moderate_risk - "ALERT", Suspicious - "BLOCK", High_risk - "BLOCK"

```
The URLF profile statistics can also be verified from Analytics (provided LEF is configured)
```
```
Below screenshot shows the URLF actions applied to the websites based on their reputation-level
```

## Configuration Template:

You can use this template as reference or import this predefined service template into your test environment &
modify as necessary

Service templates(Type NextGen Firewall) -

```
Application-Filtering.cfg
```
```
The above Application-Filtering Service Template has the following Firewall policies with Application/App-
Group/App-Filter Configured:
```
```
URLF.cfg
```
```
The above URLF Service template has the following URLF Profile configured:
```
NOTE-1: To reuse the service templates, replace the org name before importing to Director as below:


NOTE-2: Above service template does not include SSL Decryption Rule & Captive-portal configuration. Please make
sure the same is configured in your test environment for captive portal actions (Decryption rule with action
'decrypt' or 'no-decrypt' will work).
