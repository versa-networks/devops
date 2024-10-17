## Download the spack from the spack server, uploaded it, and make it available on the director(UI) which donot have Internet access
    - Tested in Python 3.10 with Windows
    - Tested in Python 3.8  with Bionic
    - Tested on Director 21.3.2

## Use Case:
    - This python script performs the necessary functions to download the spack from the spack server, uploaded it, and make it available on the director UI.  
    - The script performs the following functions:
       * Fetches the list of available spacks from the spack server.
       * Downloads the required spack file from the spack server.
       * Checksum Validation.
       * Uploads the spack file to the director via the API.
       * Reports the task progress on the director for spack upload.
    - Caveats:
        - Director release should be 21.2.3/21.3.2 or above which supports upload API.



## Prerequisites 
  - Jumpbox or User machine should have internet access and spack-server url "spack.versanetworks.com" should be accessible.
  - Reachability to Director is required on port 9182.


## Executing the Python Scripts
  - Run 'python3 Spack-Downlaod.py' or 'python Spack-Downlaod.py'

## Output Files
  - Output is displayed on the console itself 


## Author Information
------------------

Sudhir Walia - Versa Networks
