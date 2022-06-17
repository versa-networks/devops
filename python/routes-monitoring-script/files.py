import os
from datetime import datetime

class File:
	def create_files(querytype, sitename):
		dateTimeObj = datetime.now()
		timestamp = str(dateTimeObj.year) + "-" +dateTimeObj.strftime("%m") + str(dateTimeObj.day) + "-" + dateTimeObj.strftime("%H%M%S") + "-"
		filename_txt = "output/" + timestamp + querytype + "-" + sitename + ".txt"
		filename_json = "output/json/" + timestamp + querytype + "-" + sitename + ".json"
		outF = open(filename_txt, "w")
		print("SITE: " + sitename, file=outF)
		print("QUERY TYPE: " + querytype, file=outF)
		outF.close()
		outF = open(filename_json, "w")
		outF.close()

		return filename_txt, filename_json

	def print_to_file(filename, text):
		outF = open(filename, "a")	
		print(text, file=outF)
		outF.close()