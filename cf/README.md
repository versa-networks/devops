## This is a collection of AWS CloudFormation Templates/scripts and some configurations.

### It is important that you update the template image section for the Versa builds you want to run.


**Template mappings:**

|Template Name | Functions | Creates new VPC | VGW |
|------------|:----------:|:--------:|:-------:|
|aws-basic-headend.json       | 1 Dir, 1 Controller, 1 Analytics | YES | NO
|aws-basic-single-VOS-dual-transport.json | 1 VOS 2 EIPs for transport | YES | NO
|aws-basic-single-VOS.json | 1 VOS 1 EIP single transport | YES | NO
|aws-direct-connect-sf-sc-sd-da.json | 1 Dir, 1 Controller, 2 Analytics, Standalone VOS | YES | YES
|aws-direct-connect-sf-sc-sd-da-backup.json | 1 Dir, 1 Controller, 2 Analytics, Standalone VOS | YES | YES
|single-VOS.json | 1  1 EIP single transport| NO| NO
|aws-sf-sc-sd-sa-primary.json<br> aws-sf-sc-sd-sa-secondary.json | 2 VPCs (1 Dir, 1 Controller, 1 Analytics, 1 Standalone VOS) per VPC.<br> Availability Zone Selection | YES | YES
