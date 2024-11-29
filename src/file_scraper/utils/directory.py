#!/usr/bin/env python3

from . import array, file

import os

def exists(path: str):
	"""
	Returns 'True' if a path exists.
	"""
	return os.path.exists(path)

def is_directory(directory: str):
	"""
	Returns 'True' if the 'directory' exists and is a regular directory.
	"""
	return os.path.isdir(directory)

def validate(directory: str):
	"""
	Validate a directory.\n
	Success flag is 'True' if the directory has a read permission and is not empty.
	"""
	success = False
	message = ""
	if not os.access(directory, os.R_OK):
		message = f"\"{directory}\" does not have a read permission"
	elif not os.stat(directory).st_size > 0:
		message = f"\"{directory}\" is empty"
	else:
		success = True
	return success, message

def list_files(directory: str) -> list[str]:
	"""
	Get all valid files from a directory. Recursive.
	"""
	tmp = []
	for path, dirnames, filenames in os.walk(directory):
		for filename in filenames:
			full = os.path.join(path, filename)
			if file.validate_silent(full):
				tmp.append(full)
	return array.unique(tmp)

def filter_files(files: list[str], blacklist: list[str] = None, whitelist: list[str] = None):
	"""
	Filter out files based on the specified blacklist and whitelist.
	"""
	tmp = []
	if whitelist:
		for file in files:
			if any(file.endswith(ext) for ext in whitelist):
				tmp.append(file)
	elif blacklist:
		for file in files:
			if not any(file.endswith(ext) for ext in blacklist):
				tmp.append(file)
	else:
		tmp = files
	return tmp
