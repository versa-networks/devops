#!/usr/bin/python
from datetime import datetime

class AddressList:
    def __init__(self, filename: str, uploadedtime: datetime, download_status: str, size: int):
        self.filename = filename
        self.uploadedtime = uploadedtime
        self.download_status = download_status
        self.size = size

class ApplianceAddressList:
    def __init__(self, filename: str, uploadedtime: datetime, upload_status: str, size: int, appliance: str):
        self.filename = filename
        self.uploadedtime = uploadedtime
        self.upload_status = upload_status
        self.size = size
        self.appliance = appliance

class Organization:
    def __init__(self):
        self.address_lists = []
        self.appliance_address_lists = []

    def add_address_list(self, address_list: AddressList):
        self.address_lists.append(address_list)

    def add_appliance_address_list(self, appliance_address_list: ApplianceAddressList):
        self.appliance_address_lists.append(appliance_address_list)