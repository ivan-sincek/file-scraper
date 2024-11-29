#!/usr/bin/env python3

from . import result

def sort_by_file(obj: list[result.FileResults]):
	"""
	Sort the results by 'FileResults.file'.
	"""
	return sorted(obj, key = lambda entry: entry.file.casefold())

def select_text_by_key(obj: list[result.FileResults], key: str) -> list[result.Result]:
	"""
	Get all 'FileResults.results[key]' for the specified key.\n
	Returns a unique [sorted] list.
	"""
	tmp = []
	for entry in obj:
		if key in entry.results:
			tmp.extend(entry.results[key])
	return tmp
