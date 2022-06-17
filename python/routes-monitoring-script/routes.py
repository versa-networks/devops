import json
import jsondiff
import tabulate
import os

class RoutingTable:
	def __init__(self, json):
		self.name = 'Versa-LAN-VR'
		#for key, value in pairs:
		#	for key  in value:
		#	print(key.get('name') +'  '+key.get('ipAddress'))

	#@staticmethod
	def print_routes(json_text, name):
		json_object = json.loads(json_text.text)
		pairs = json_object.items()
		print()
		print("Routes for Routing instance : " + name + " AFI: ipv4  SAFI: unicast")
		print()
		print("Codes: E1 - OSPF external type 1, E2 - OSPF external type 2")
		print("IA - inter area, iA - intra area,")
		print("L1 - IS-IS level-1, L2 - IS-IS level-2")
		print("N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2")
		print("RTI - Learnt from another routing-instance")
		print("+ - Active Route)")
		#Prot   Type  Dest Address/Mask   Next-hop        Age      Interface name
		print('%-8s%-8s%-22s%-18s%-10s%-22s' %("Prot","Type","Dest Address/Mask","Next-hop","Age","Interface"))
		print('%-8s%-8s%-22s%-18s%-10s%-22s' %("-----","-----","-----------------","-----------","---","---------"))
		for key, value in pairs:
			for key  in value:
			#print(key.get('name') +'  '+key.get('ipAddress'))
				print('%-8s%-8s%-22s%-18s%-10s%-22s' % (key.get('protocol'),key.get('type'),key.get('dest-prefix'), key.get('next-hop'), key.get('age'),key.get('interface-name')))
				#print('%-6s%-24s%-12s' % (key.get('protocol'),key.get('dest-prefix'), key.get('next-hop')))
				#print(key.get('dest-prefix'))
				#print(tabulate([[key.get('dest-prefix'),key.get('next-hop')]], headers=['Dest Address/Mask', 'next-hop']))

	def print_routes_to_file(json_text, data, filename):
		name = data[0]
		json_object = json.loads(json_text.text)
		pairs = json_object.items()
		try:
			outF = open(filename, "a")		
			print("", file=outF)
			print("Routes for Routing instance : " + name + " AFI: ipv4  SAFI: unicast", file=outF)
			print("",file=outF)
			print("Codes: E1 - OSPF external type 1, E2 - OSPF external type 2", file=outF)
			print("IA - inter area, iA - intra area,", file=outF)
			print("L1 - IS-IS level-1, L2 - IS-IS level-2", file=outF)
			print("N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2", file=outF)
			print("RTI - Learnt from another routing-instance", file=outF)
			print("+ - Active Route)", file=outF)
			#Prot   Type  Dest Address/Mask   Next-hop        Age      Interface name
			print( '%-8s%-8s%-22s%-18s%-10s%-22s' %("Prot","Type","Dest Address/Mask","Next-hop","Age","Interface"), file=outF)
			print( '%-8s%-8s%-22s%-18s%-10s%-22s' %("-----","-----","-----------------","-----------","---","---------"), file=outF)
			for key, value in pairs:
				for key  in value:
				#print(key.get('name') +'  '+key.get('ipAddress'))
					print( '%-8s%-8s%-22s%-18s%-10s%-22s' % (key.get('protocol'),key.get('type'),key.get('dest-prefix'), key.get('next-hop'), key.get('age'),key.get('interface-name')), file=outF)
					#print('%-6s%-24s%-12s' % (key.get('protocol'),key.get('dest-prefix'), key.get('next-hop')))
					#print(key.get('dest-prefix'))
					#print(tabulate([[key.get('dest-prefix'),key.get('next-hop')]], headers=['Dest Address/Mask', 'next-hop']))
			outF.close()
			print("Succesfully saved " + name +" rti state to txt file")
		except:
			print("Failure to save " + name + " rti state to txt file")

	def save_routes_to_json_file(json_text, data, site, filename):
		outF = open(filename, "a")
		d = {'Site': site, 'Org': data[2], 'rti': data[0]}
		json_object = json.loads(json_text.text)
		d.update(json_object)
		json.dump(d, outF, indent = 6)
		outF.close()

class Route:
	def __init__(self, json):
		self.rtiindex = json.get('rti-index')
		self.destprefix = json.get('dest-prefix')
		self.proto = json.get('proto')
		if json.get('act') == true:
			self.active = True
		else:
			self.active = False
		self.nexthop = json.get('next-hop')