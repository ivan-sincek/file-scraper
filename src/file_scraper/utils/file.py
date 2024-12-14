#!/usr/bin/env python3

import jsbeautifier, os

__ENCODING = "ISO-8859-1"

def __get_root_directory(subdirectory: str = ""):
	"""
	Get the full path to the installation directory.
	"""
	separator = os.path.sep
	return os.path.join(separator.join(os.path.abspath(__file__).split(separator)[0:-2]), subdirectory)

def get_template():
	"""
	Get the full path to the default template.
	"""
	return os.path.join(__get_root_directory("templates"), "default.json")

def get_report():
	"""
	Get the full path to the default report template.
	"""
	return os.path.join(__get_root_directory("reports"), "default.html")

def get_font():
	"""
	Get the full path to the default font.
	"""
	return os.path.join(__get_root_directory("fonts"), "FiraCode-Medium.woff2")

# ----------------------------------------

def is_file(file: str):
	"""
	Returns 'True' if the 'file' exists and is a regular file.
	"""
	return os.path.isfile(file)

def validate(file: str):
	"""
	Validate a file.\n
	Success flag is 'True' if the file has a read permission and is not empty.
	"""
	success = False
	message = ""
	if not os.access(file, os.R_OK):
		message = f"\"{file}\" does not have a read permission"
	elif not os.stat(file).st_size > 0:
		message = f"\"{file}\" is empty"
	else:
		success = True
	return success, message

def validate_silent(file: str):
	"""
	Silently validate a file.\n
	Returns 'True' if the 'file' exists, is a regular file, has a read permission, and is not empty.
	"""
	return os.path.isfile(file) and os.access(file, os.R_OK) and os.stat(file).st_size > 0

def read(file: str):
	"""
	Read a file as text.\n
	Whitespace will be stripped from the text.
	"""
	return open(file, "r", encoding = __ENCODING).read().strip()

def overwrite(text: str, out: str):
	"""
	Write a text to an output file.\n
	If the output file exists, prompt to overwrite it.
	"""
	confirm = "yes"
	if os.path.isfile(out):
		print(f"'{out}' already exists")
		confirm = input("Overwrite the output file (yes): ")
	if confirm.lower() in ["yes", "y"]:
		try:
			open(out, "w", errors = "ignore").write(text)
			print(f"Results have been saved to '{out}'")
		except FileNotFoundError:
			print(f"Cannot save the results to '{out}'")

def beautify(file: str):
	"""
	Beautify a JavaScript (.js) file.
	"""
	try:
		text = jsbeautifier.beautify_file(file)
		if text:
			open(file, "w").write(text)
	except Exception:
		pass
