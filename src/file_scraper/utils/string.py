#!/usr/bin/env python3

from . import template

import base64, OpenSSL.crypto, urllib.parse

__ENCODING = "UTF-8"

def is_length_valid(string: str, minimum: int = 0, maximum: int = 0):
	"""
	Validate the length of a string.\n
	Returns 'True' if neither a minimum nor a maximum is specified.\n
	Returns 'False' on failure.
	"""
	success = True
	length = len(string)
	if (minimum > 0 and length < minimum) or (maximum > 0 and length > maximum):
		success = False
	return success

def decode(string: str, encoding: template.Encoding):
	"""
	Decode a string.\n
	Returns an empty string on failure.
	"""
	decoded = ""
	try:
		if encoding == template.Encoding.URL:
			decoded = remove_bad_chars(urllib.parse.unquote(string))
		elif encoding == template.Encoding.BASE64:
			decoded = remove_bad_chars(base64.b64decode(string))
		elif encoding == template.Encoding.HEX:
			decoded = remove_bad_chars(bytes.fromhex(string.replace("0x", "").replace("\\", "").replace("x", "")))
		elif encoding == template.Encoding.PEM:
			if "CERTIFICATE" in string.upper():
				decoded = remove_bad_chars(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_TEXT, OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, string)))
			elif "PRIVATE KEY" in string.upper():
				decoded = remove_bad_chars(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_TEXT, OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, string)))
	except Exception:
		pass
	return decoded

def remove_bad_chars(string: str | bytes):
	"""
	Remove invalid characters and, if applicable, convert a byte string to a regular string.\n
	Returns an empty string on failure.
	"""
	if isinstance(string, str):
		return string.replace("\x00", "").replace("\r", "").strip()
	elif isinstance(string, bytes):
		return string.replace(b"\x00", b"").replace(b"\r", b"").decode(__ENCODING).strip()
	else:
		return ""
