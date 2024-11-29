#!/usr/bin/env python3

import colorama, termcolor

colorama.init(autoreset = True)

def print_error(message: str):
	"""
	Print an error message.
	"""
	print(f"ERROR: {message}")

def print_red(message: str):
	"""
	Print a message in red color.
	"""
	termcolor.cprint(message, "red")

def print_yellow(message: str):
	"""
	Print a message in yellow color.
	"""
	termcolor.cprint(message, "yellow")
