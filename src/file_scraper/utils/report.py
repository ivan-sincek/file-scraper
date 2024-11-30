#!/usr/bin/env python3

from . import file, grep, jquery, result, scrape, template

from bs4 import BeautifulSoup

import os

class Report:

	def __init__(
		self,
		results : list[result.FileResults],
		template: template.Template,
		out     : str
	):
		"""
		Class for creating an HTML report.
		"""
		self.__results  = results
		self.__template = template
		self.__out      = out
		self.__soup     = ""

	def generate(self):
		"""
		Generate an HTML report.
		"""
		self.__soup = file.read(file.get_report())
		self.__soup = self.__soup.replace("</filename>", self.__out.rsplit(os.path.sep)[-1], 1)
		self.__soup = self.__soup.replace("</font>", file.get_font().replace("\\", "\\\\"), 1)
		self.__soup = BeautifulSoup(self.__soup, "html.parser")
		for res in self.__results:
			self.__add_header(res.file)
			for key, values in res.results.items():
				self.__add_results(key, values)
		for key, entry in self.__template.entries.items():
			if entry.collect:
				collection = jquery.select_text_by_key(self.__results, key)
				if collection:
					self.__add_collection(key, collection)
		self.__soup = self.__soup.prettify(formatter = "html5")
		for highlight in scrape.Highlight:
			self.__soup = self.__soup.replace(f"&lt;{highlight.value}&gt;", f"<span class=\"{highlight.name.lower()}\">")
			self.__soup = self.__soup.replace(f"&lt;/{highlight.value}&gt;", "</span>")

	def __add_header(self, path: str):
		"""
		Add a file name header.
		"""
		attributes = {"onclick": "collapseFile(this)"}
		h2 = self.__soup.new_tag("h2", **attributes)
		h2.string = path
		self.__soup.html.body.find("div").append(h2)

	def __add_results(self, key: str, values: list[result.Result]):
		"""
		Add results unde the file name header.
		"""
		attributes = {"class": key, "onclick": "collapseSingle(this)", "style": "background-color: var(--active);"}
		if not self.__soup.html.body.nav.ul.find("button", attributes):
			button = self.__soup.new_tag("button", **attributes)
			button.string = key
			li = self.__soup.new_tag("li")
			li.append(button)
			self.__soup.html.body.nav.ul.append(li)
		# --------------------------------
		attributes = {"class": key, "style": "display: block;"}
		button = self.__soup.new_tag("button", **attributes)
		button.string = key
		self.__soup.html.body.find("div").append(button)
		# --------------------------------
		attributes = {"style": "display: block;"}
		pre = self.__soup.new_tag("pre", **attributes)
		pre.string = ("\n").join(value.text + value.append for value in values)
		self.__soup.html.body.find("div").append(pre)

	def __add_collection(self, key: str, values: list[result.Result]):
		"""
		Add a collection modal.
		"""
		attributes = {"class": key, "onclick": "popModal(this)", "style": "background-color: var(--inactive);"}
		if not self.__soup.html.body.nav.ul.find("button", attributes):
			button = self.__soup.new_tag("button", **attributes)
			button.string = f"{key}\u2197"
			li = self.__soup.new_tag("li")
			li.append(button)
			self.__soup.html.body.nav.ul.append(li)
		# --------------------------------
		attributes = {"class": key, "style": "display: none;"}
		pre = self.__soup.new_tag("pre", **attributes)
		pre.string = ("\n").join(value.text + value.append for value in values)
		self.__soup.html.body.find_all("div", limit = 2)[1].append(pre)

	def save(self):
		"""
		Save the report an output file.
		"""
		file.overwrite(self.__soup, self.__out)
