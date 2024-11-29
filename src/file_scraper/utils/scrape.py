#!/usr/bin/env python3

from . import array, file, general, grep, jquery, rabin, report, result, stopwatch, string, template

import alive_progress, concurrent.futures, enum, regex as re, threading

class Highlight(enum.Enum):
	"""
	Enum containing stages.
	"""
	MATCHED = "file-scraper-matched"
	DECODED = "file-scraper-decoded"

def highlight_matched(matched: str):
	"""
	Highlight a matched string.
	"""
	return f"<{Highlight.MATCHED.value}>{matched}</{Highlight.MATCHED.value}>"

def highlight_decoded(decoded: str):
	"""
	Highlight a decoded string.
	"""
	return f"\n<{Highlight.DECODED.value}>{decoded}</{Highlight.DECODED.value}>"

# ----------------------------------------

class FileScraper:

	def __init__(
		self,
		files   : list[str],
		template: template.Template,
		beautify: bool,
		threads : int,
		out     : str,
		debug   : bool
	):
		"""
		Class for file scraping.
		"""
		self.__files      = files
		self.__template   = template
		self.__beautify   = beautify
		self.__threads    = threads
		self.__out        = out
		self.__debug      = debug
		self.__print_lock = threading.Lock()

	def run(self):
		"""
		Start file scraping.
		"""
		print(f"Files to scrape: {len(self.__files)}")
		print("Press CTRL + C to exit early - results will be saved")
		results = []
		with alive_progress.alive_bar(len(self.__files), title = "Progress:") as bar:
			with concurrent.futures.ThreadPoolExecutor(max_workers = self.__threads) as executor:
				subprocesses = []
				try:
					for path in self.__files:
						subprocesses.append(executor.submit(self.__run, path))
					for subprocess in concurrent.futures.as_completed(subprocesses):
						tmp: result.FileResults = subprocess.result()
						if tmp.results:
							results.append(tmp)
							self.__print_success(tmp.file)
						bar()
				except KeyboardInterrupt:
					executor.shutdown(wait = True, cancel_futures = True)
		if not results:
			print("No results")
		else:
			print(f"Files with valid results: {len(results)}")
			print("Generating the report...")
			doc = report.Report(jquery.sort_by_file(results), self.__template, self.__out)
			doc.generate()
			stopwatch.stopwatch.stop()
			doc.save()

	def __run(self, path: str):
		"""
		Returns searches with highlighted matches or exact matches.
		"""
		results = result.FileResults(path)
		if self.__beautify and path.endswith(".js"):
			file.beautify(path)
		response, error = rabin.run(path)
		if error:
			self.__print_exception(error)
		else:
			for key, entry in self.__template.entries.items():
				tmp = self.__search(response, entry) if entry.search else self.__match(response, entry)
				if tmp:
					results.results[key] = tmp
		return results

	def __search(self, response: str, entry: template.TemplateEntry) -> list[result.Result]:
		"""
		Returns searches with highlighted matches.
		"""
		results = []
		searches, error = grep.find(response, entry.search, entry.ignorecase)
		if error:
			self.__print_exception(error)
		else:
			if entry.unique:
				searches = array.unique(searches)
			for searched in searches:
				tmp = result.Result(searched)
				success = False
				for matched in array.unique(re.findall(entry.query, tmp.text, entry.ignorecase)):
					if not string.is_length_valid(matched, entry.minimum, entry.maximum):
						continue
					success = True
					if entry.decode != template.Encoding.NONE:
						decoded = string.decode(matched, entry.decode)
						if not decoded or not string.is_length_valid(decoded, entry.minimum_decode, entry.maximum_decode):
							continue
						tmp.append += highlight_decoded(decoded)
					tmp.text = tmp.text.replace(matched, highlight_matched(matched)).strip()
				if success:
					results.append(tmp)
		return results

	def __match(self, response: str, entry: template.TemplateEntry) -> list[result.Result]:
		"""
		Returns exact matches.
		"""
		results = []
		matches, error = grep.find(response, entry.query, entry.ignorecase)
		if error:
			self.__print_exception(error)
		else:
			if entry.unique:
				matches = array.unique(matches)
			for matched in matches:
				tmp = result.Result(matched)
				if not string.is_length_valid(matched, entry.minimum, entry.maximum):
					continue
				if entry.decode != template.Encoding.NONE:
					decoded = string.decode(matched, entry.decode)
					if not decoded or not string.is_length_valid(decoded, entry.minimum_decode, entry.maximum_decode):
						continue
					tmp.append += highlight_decoded(decoded)
				tmp.text = tmp.text.strip()
				results.append(tmp)
		return results

	def __print_success(self, message: str):
		"""
		Print success.
		"""
		if self.__debug:
			with self.__print_lock:
				general.print_yellow(message)

	def __print_exception(self, message: str):
		"""
		Print exception.
		"""
		if self.__debug:
			with self.__print_lock:
				general.print_red(f"[ EXCEPTION ] {message}")
