#!/usr/bin/env python3

from . import file

import dataclasses, enum, json

class Encoding(str, enum.Enum):
	"""
	Enum containing encodings.
	"""
	NONE   = ""
	URL    = "url"
	BASE64 = "base64"
	HEX    = "hex"
	PEM    = "pem"

@dataclasses.dataclass
class TemplateEntry:
	"""
	Class for storing a single entry of the extraction template.
	"""
	query         : str
	search        : bool | str = False
	ignorecase    : bool       = False
	minimum       : int        = 0
	maximum       : int        = 0
	minimum_decode: int        = 0
	maximum_decode: int        = 0
	decode        : Encoding   = ""
	unique        : bool       = False
	collect       : bool       = False

	def __post_init__(self):
		const = ".*"
		if self.search:
			self.search = const + self.query.strip(const) + const

@dataclasses.dataclass
class Template:
	"""
	Class for storing an extraction template.
	"""
	entries: dict[str, TemplateEntry] = dataclasses.field(default_factory = dict)

# ----------------------------------------

def deserialize(template_json: str) -> tuple[Template | None, str]:
	"""
	Deserialize a template from a JSON string.\n
	Returns 'None' and an error message on failure.
	"""
	template = Template()
	message = ""
	try:
		tmp = json.loads(template_json)
		for key in tmp.keys():
			template.entries[key] = TemplateEntry(**tmp[key])
			template.entries[key].decode = Encoding(template.entries[key].decode)
	except Exception:
		template = None
		message = "Cannot deserialize the template"
	return template, message

def load_default():
	"""
	Load the default template from the installation directory.\n
	Returns 'None' and an error message on failure.
	"""
	return deserialize(file.read(file.get_template()))

def build(query: str):
	"""
	Build a template from the specified regular expression.
	"""
	template                  = Template()
	entry                     = TemplateEntry(query, True)
	entry.ignorecase          = True
	entry.unique              = True
	entry.collect             = True
	template.entries["RegEx"] = entry
	return template
