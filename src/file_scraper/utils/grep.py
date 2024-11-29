#!/usr/bin/env python3

import regex as re

def validate(query: str):
	"""
	Validate a regular expression.
	"""
	success = False
	message = ""
	try:
		re.compile(query)
		success = True
	except re.error:
		message = f"Invalid RegEx: {query}"
	return success, message

def find(text: str, query: str, ignorecase: bool = True) -> tuple[list, str]:
	"""
	Extract all matches from a text using the specified RegEx pattern.\n
	Returns an empty list and an error message on failure.
	"""
	tmp = []
	message = ""
	try:
		tmp = re.findall(query, text, flags = re.MULTILINE | (re.IGNORECASE if ignorecase else 0))
	except re.error as ex:
		message = str(ex)
	return tmp, message

def replace(text: str, query: str, new = "", ignorecase: bool = True):
	"""
	Replace all matches from a text using the specified RegEx pattern with a new value.\n
	Returns an empty string and an error message on failure.
	"""
	tmp = ""
	message = ""
	try:
		tmp = re.sub(query, new, text, flags = re.MULTILINE | (re.IGNORECASE if ignorecase else 0))
	except re.error as ex:
		message = str(ex)
	return tmp, message
