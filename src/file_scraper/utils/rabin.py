#!/usr/bin/env python3

import subprocess

__ENCODING = "ISO-8859-1"

def run(file: str):
	"""
	Run Rabin2 as a new subprocess.\n
	Returns an empty string and an error message on failure.
	"""
	response = ""
	message = ""
	try:
		tmp = subprocess.run(f"rabin2 -zzzqq \"{file}\"", shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT).stdout
		response = tmp.decode(__ENCODING).replace("\\n", "\n").replace("\\\\", "\\")
	except Exception as ex:
		message = str(ex)
	return response, message
