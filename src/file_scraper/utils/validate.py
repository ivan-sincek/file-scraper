#!/usr/bin/env python3

from . import array, config, directory, file, general, grep, template

import argparse, sys

class MyArgParser(argparse.ArgumentParser):

	def print_help(self):
		print(f"File Scraper {config.APP_VERSION} ( github.com/ivan-sincek/file-scraper )")
		print("")
		print("Usage:   file-scraper -dir directory -o out          [-t template     ] [-th threads]")
		print("Example: file-scraper -dir decoded   -o results.html [-t template.json] [-th 10     ]")
		print("")
		print("DESCRIPTION")
		print("    Scrape files for sensitive information")
		print("DIRECTORY")
		print("    Directory containing files or a single file to scrape")
		print("    -dir, --directory> = decoded | files | test.exe | etc.")
		print("TEMPLATE")
		print("    File containing extraction details or a single RegEx to use")
		print("    Default: built-in JSON template file")
		print("    -t, --template = template.json | \"secret\\: [\\w\\d]+\" | etc.")
		print("EXCLUDES")
		print("    Exclude all files ending with the specified extension")
		print("    Specify 'default' to load the built-in list")
		print("    Use comma-separated values")
		print("    -e, --excludes = mp3 | default,jpg,png | etc.")
		print("INCLUDES")
		print("    Include all files ending with the specified extension")
		print("    Overrides the excludes")
		print("    Use comma-separated values")
		print("    -i, --includes = java | json,xml,yaml | etc.")
		print("BEAUTIFY")
		print("    Beautify [minified] JavaScript (.js) files")
		print("    -b, --beautify")
		print("THREADS")
		print("    Number of parallel threads to run")
		print("    Default: 30")
		print("    -th, --threads = 10 | etc.")
		print("OUT")
		print("    Output file")
		print("    -o, --out = results.html | etc.")
		print("DEBUG")
		print("    Enable debug output")
		print("    -dbg, --debug")

	def error(self, message):
		if len(sys.argv) > 1:
			print("Missing a mandatory option (-dir, -o) and/or optional (-t, -e, -i, -b, -th, -dbg)")
			print("Use -h or --help for more info")
		else:
			self.print_help()
		exit()

class Validate:

	def __init__(self):
		"""
		Class for validating and managing CLI arguments.
		"""
		self.__parser = MyArgParser()
		self.__parser.add_argument("-dir", "--directory", required = True , type   = str         , default = ""   )
		self.__parser.add_argument("-t"  , "--template" , required = False, type   = str         , default = ""   )
		self.__parser.add_argument("-e"  , "--excludes" , required = False, type   = str.lower   , default = ""   )
		self.__parser.add_argument("-i"  , "--includes" , required = False, type   = str.lower   , default = ""   )
		self.__parser.add_argument("-b"  , "--beautify" , required = False, action = "store_true", default = False)
		self.__parser.add_argument("-th" , "--threads"  , required = False, type   = str         , default = ""   )
		self.__parser.add_argument("-o"  , "--out"      , required = True , type   = str         , default = ""   )
		self.__parser.add_argument("-dbg", "--debug"    , required = False, action = "store_true", default = False)

	def validate_args(self):
		"""
		Validate and return the CLI arguments.
		"""
		self.__success = True
		self.__args = self.__parser.parse_args()
		self.__validate_template()
		self.__validate_excludes()
		self.__validate_includes()
		self.__validate_directory()
		self.__validate_threads()
		return self.__success, self.__args

	def __error(self, message: str):
		"""
		Set the success flag to 'False' to prevent the main task from executing, and print an error message.
		"""
		self.__success = False
		general.print_error(message)

	# ------------------------------------

	def __validate_template(self):
		tmp = None
		if self.__args.template:
			if file.is_file(self.__args.template):
				success, message = file.validate(self.__args.template)
				if not success:
					self.__error(message)
				else:
					tmp = file.read(self.__args.template)
					if not tmp:
						self.__error(f"No template was found in \"{self.__args.template}\"")
					else:
						tmp, message = template.deserialize(tmp)
						if message:
							self.__error(f"{message} from \"{self.__args.template}\"")
			else:
				success, message = grep.validate(self.__args.template)
				if not success:
					self.__error(message)
				else:
					tmp = template.build(self.__args.template)
		else:
			tmp, message = template.load_default()
			if not tmp:
				self.__error("Cannot deserialize the default template")
		self.__args.template = tmp

	def __validate_excludes(self):
		tmp = []
		if self.__args.excludes:
			excludes = array.remove_empty_strings(self.__args.excludes.split(","))
			if not excludes:
				self.__error("No file extensions to exclude were specified")
			else:
				for exclude in excludes:
					if exclude == "default":
						tmp.extend(config.EXCLUDES)
					else:
						tmp.append(exclude)
				tmp = array.unique(tmp)
		self.__args.excludes = tmp

	def __validate_includes(self):
		tmp = []
		if self.__args.includes:
			includes = array.remove_empty_strings(self.__args.includes.split(","))
			if not includes:
				self.__error("No file extensions to include were specified")
			else:
				tmp = array.unique(includes)
		self.__args.includes = tmp

	def __validate_directory(self):
		tmp = []
		if not directory.exists(self.__args.directory):
			self.__error(f"\"{self.__args.directory}\" does not exist")
		elif directory.is_directory(self.__args.directory):
			success, message = directory.validate(self.__args.directory)
			if not success:
				self.__error(message)
			else:
				tmp = directory.filter_files(directory.list_files(self.__args.directory), self.__args.excludes, self.__args.includes)
				if not tmp:
					self.__error(f"No valid files were found in \"{self.__args.directory}\"")
		else:
			success, message = file.validate(self.__args.directory)
			if not success:
				self.__error(message)
			else:
				tmp = [self.__args.directory]
		self.__args.directory = tmp

	def __validate_threads(self):
		tmp = 30
		if self.__args.threads:
			if not self.__args.threads.isdigit():
				self.__error("Number of parallel threads must be numeric")
			else:
				tmp = int(self.__args.threads)
				if tmp <= 0:
					self.__error("Number of parallel threads must be greater than zero")
		self.__args.threads = tmp
