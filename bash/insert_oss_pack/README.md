## Readme for insert_oss_pack
    - There are cases when a Director does not have connectivity to the Internet. In such cases
      the OSS pack must be copied onto the Director. 
    - Upon running the script, on can see the requisite files on Director UI->Inventory->Software Images ->OSS Pack
    - Tested on Director 21.2.2

## Prerequisites 
  - OSS pack must be downloaded to Director 
  - The script will need to run on the Active Director. It needs sudo privileges


## Bash Scripts
  - insert-osspack.sh: this is the script that needs to be executed
  - example: sudo insert-osspack.sh --file /tmp/versa-flexvnf-osspack-20230919.bin -subs flex --ver 20230919
  - the script copies the file to appropiate location and executes postgres commands, so that UI can see the new file


## Author Information
------------------

Sujay Datta - Versa Networks
