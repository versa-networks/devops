import json
import jsondiff

class Site:
	def __init__(self, json):
		self.name = json.get('name')
		self.ipAddress = json.get('ipAddress')
		self.type = json.get('appType')
		self.branchId = json.get('branchId')
		self.json_data = json

	#@staticmethod
	def get_site_names(json_text):
        	json_object = json.loads(json_text.text)
        	pairs = json_object.items()
        	print("\n List of Sites \n")
        	for key, value in pairs:
                	for key  in value:
                        	print(key.get('name') +'  '+key.get('ipAddress'))
