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
	Returns a unique [sorted] list based on 'Result.text'.
	"""
	tmp = []
	exists = set()
	for entry in obj:
		if key in entry.results:
			for result in entry.results[key]:
				if result.text not in exists:
					tmp.append(result)
					exists.add(result.text)
	if tmp:
		tmp = sorted(tmp, key = lambda x: x.text.casefold())
	return tmp
