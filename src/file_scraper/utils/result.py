#!/usr/bin/env python3

import dataclasses

@dataclasses.dataclass
class Result:
	"""
	Class for storing a single result.
	"""
	text   : str
	append : str  = ""

@dataclasses.dataclass
class FileResults:
	"""
	Class for storing file results.
	"""
	file   : str
	results: dict[str, list[Result]] = dataclasses.field(default_factory = dict)
