# **PAN to VERSA Conversion**

## Description

Converts a Palo Alto configuration export to a Versa configuration.

<!-- ## Getting Started-->

## Dependencies

1. Python Installed
2. Modules
   1. argparse
   2. traceback
   3. sys
   4. os
   5. csv
   6. logging
   7. lxml.etree
   8. zoneinfo
   9. sys
   10. re
   11. typing
   12. datetime

<!-- ### Installing-->

<!-- ### Executing program-->

<!-- ## Help-->

## Purpose

Converts a Palo Alto configuration export to a Versa configuration.

## Tested on

- Windows 11
- Python 3.10.6
- Director 21.3

## What it does

Converts a Palo Alto configuration export to a Versa configuration.

<!-- ## Variables -->

## Use of

### Command line arguments

```text
usage: pan-convert.py [-h] -pc PANCONFIGFILE [-z ZONEFILE] [-a APPFILE] [-s SUBFAMILIESFILE] [-u URLFILE]
                      [-c COUNTRIESFILE] (-T TEMPLATE | -D DEVICE) [-o OUTDIR] [-v VPATHSFILE] [-org ORGNAME]
                      -n TEMPLATENAME [-cil]

Convert Palo Alto config to Versa config

options:
  -h, --help            show this help message and exit
  -pc PANCONFIGFILE, --panconfigfile PANCONFIGFILE
                        Path to Palo Alto config file in XML format
  -z ZONEFILE, --zonefile ZONEFILE
                        Path to zone/interface CSV file
  -a APPFILE, --appfile APPFILE
                        Path to Versa predefined applications CSV file
  -s SUBFAMILIESFILE, --subfamiliesfile SUBFAMILIESFILE
                        Path to Versa application subfamiles CSV file
  -u URLFILE, --urlfile URLFILE
                        Path to Versa predefined URL categories XML file
  -c COUNTRIESFILE, --countriesfile COUNTRIESFILE
                        Path to Versa predefined countries XML file
  -T TEMPLATE, --template TEMPLATE
                        Template name
  -D DEVICE, --device DEVICE
                        Device name
  -o OUTDIR, --outputdir OUTDIR
                        Path to output directory
  -v VPATHSFILE, --versa-paths-file VPATHSFILE
                        Path to Versa path segments file
  -org ORGNAME, --org ORGNAME
                        Organization name
  -cil, --createinterfacelist
                        Create Interface List File
```

### Walkthrough

1. Export Config from PAN
   - Panorama
     - <https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000ClgzCAC>
   - Directly from Device
     - Generate then download tech support file download, then extract
     - From PA-Support-Dump\opt\pancfg\mgmt\saved-configs copy .merged-running-config.xml to the script folder of ./Source_Files/
   - Example: VVC-PAN-merged-running-config.xml
2. Export service template configuration file from Director to ./Source_Files/
   - Example: NGFW-Test.cfg
3. Run Script with -cil
   - This creates interface-list.csv file in ./Source_Files
   - example:\
     - `python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-Test.cfg -org RobK-Demo-1 -n NGFW-TEST -cil`
4. Edit interface-list.csv as needed.
   - Example would be that the PAN interface ids to Versa vni ids may need to be edited
5. (Optional) Update all the files in ./Predefined
6. Run script but DO NOT include -cil
   - example:\
     - `python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-TEST.cfg -org RobK-Demo-1 -n NGFW-TEST`
7. Import .cfg file from the Output_Files directory, into Versa Director.
   - The .cfg file will most likely need to be edited before it will import correctly. If you import using the API you will get exact line numbers that are causing the import to fail.
   - Example:\
     - `curl -X POST "https://cloud-demo.versa-networks.com:9182/vnms/template/import" -H "accept: application/xml" -H "Content-Type: multipart/form-data" -F "file=@PAN-merged-running-config.cfg;type=" -F "templateName=NGFW-TEST"`
     - You can also use swagger to import, the import call is under Template Service. It is Post /vnms/template/import.

### Useful links

- <https://protobook.qosmos.com/>
- <https://applipedia.paloaltonetworks.com/>

## Example

```bash
python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-TEST.cfg -org Test-Test -n NGFW-TEST
```

## Common Issues

1. Palo Alto default application names don't match to Versa default application names. Meaning that some application groups will not have the correct memebers.
   a. This will be reolved in a future release

## Authors

Sunil Ravi

### Updates

Rob Kauffman
