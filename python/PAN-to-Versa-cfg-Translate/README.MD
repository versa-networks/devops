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
usage: pan-convert.py [-h] -pc PAN_CONFIG_FILE [-z ZONE_FILE] [-a APP_FILE] [-s SUBFAMILIES_FILE] [-u URL_FILE] [-c COUNTRIES_FILE] (-T TEMPLATE_FILE_NAME | -D DEVICE_NAME) [-o OUTPUT_DIR] [-v VERSA_PATHS_FILE] [-cil]

Convert Palo Alto config to Versa config

options:
  -h, --help            show this help message and exit
  -pc PAN_CONFIG_FILE, --pan_config_file PAN_CONFIG_FILE
                        Path to Palo Alto config file in XML format
  -z ZONE_FILE, --zone_file ZONE_FILE
                        Path to zone/interface CSV file
  -a APP_FILE, --app_file APP_FILE
                        Path to Versa predefined applications CSV file
  -s SUBFAMILIES_FILE, --subfamilies_file SUBFAMILIES_FILE
                        Path to Versa application subfamilies CSV file
  -u URL_FILE, --url_file URL_FILE
                        Path to Versa predefined URL categories XML file
  -c COUNTRIES_FILE, --countries_file COUNTRIES_FILE
                        Path to Versa predefined countries XML file
  -T TEMPLATE_FILE_NAME, --template_file_name TEMPLATE_FILE_NAME
                        Template name
  -D DEVICE_NAME, --device_name DEVICE_NAME
                        Device name
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to output directory
  -v VERSA_PATHS_FILE, --versa_paths_file VERSA_PATHS_FILE
                        Path to Versa path segments file
  -cil, --create_interface_list
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
     - `python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-TEST.cfg -cil`
4. Edit interface-list.csv as needed.
   - Example would be that the PAN interface ids to Versa vni ids may need to be edited
5. (Optional) Update all the files in ./Predefined
6. Run script but DO NOT include -cil
   - example:\
     - `python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-TEST.cfg`
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
python.exe pan-convert.py -z ./Source_Files/interface-list.csv -pc ./Source_Files/PAN-merged-running-config.xml -T ./Source_Files/NGFW-TEST.cfg
```

## Common Issues

1. Palo Alto default application names don't match to Versa default application names. Meaning that some application groups will not have the correct memebers.
   a. This will be reolved in a future release

## Authors

Sunil Ravi

### Updates

Rob Kauffman
