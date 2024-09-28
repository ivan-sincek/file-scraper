#!/usr/bin/env python3

import alive_progress, argparse, base64, bs4, concurrent.futures, datetime, jsbeautifier, json, OpenSSL.crypto, os, regex as re, subprocess, sys, threading, urllib.parse

# ----------------------------------------

class Stopwatch:

	def __init__(self):
		self.__start = datetime.datetime.now()

	def stop(self):
		self.__end = datetime.datetime.now()
		print(("Script has finished in {0}").format(self.__end - self.__start))

stopwatch = Stopwatch()

# ----------------------------------------

def validate_directory_files(directory):
	tmp = []
	for path, dirs, files in os.walk(directory):
		for file in files:
			file = os.path.join(path, file)
			if os.path.isfile(file) and os.access(file, os.R_OK) and os.stat(file).st_size > 0:
				tmp.append(file)
	return tmp

def validate_template_reject(obj):
	for key in obj:
		for subkey in obj[key]:
			if subkey not in ["query", "search", "ignorecase", "minimum", "maximum", "decode", "unique", "collect"]:
				obj[key].pop(subkey)
	return obj

def validate_template_query(obj):
	subkey = "query"
	for key in obj:
		if subkey not in obj[key] and not isinstance(obj[key][subkey], str) or len(obj[key][subkey]) < 1:
			obj.pop(key)
	return obj

def validate_template_search(obj):
	subkey = "search"
	for key in obj:
		if subkey in obj[key]:
			if not isinstance(obj[key][subkey], bool) or obj[key][subkey] is not True:
				obj[key].pop(subkey)
			else:
				const = ".*"
				obj[key][subkey] = const + obj[key]["query"].strip(const) + const
	return obj

def validate_template_ignorecase(obj):
	subkey = "ignorecase"
	for key in obj:
		if subkey in obj[key]:
			if not isinstance(obj[key][subkey], bool) or obj[key][subkey] is not True:
				obj[key].pop(subkey)
	return obj

def validate_template_min_max(obj):
	for subkey in ["minimum", "maximum"]:
		for key in obj:
			if subkey in obj[key]:
				if not isinstance(obj[key][subkey], int) or obj[key][subkey] < 1:
					obj[key].pop(subkey)
	return obj

def validate_template_decode(obj):
	subkey = "decode"
	for key in obj:
		if subkey in obj[key]:
			if not isinstance(obj[key][subkey], str) or len(obj[key][subkey]) < 1 or obj[key][subkey].lower() not in ["url", "base64", "hex", "cert"]:
				obj[key].pop(subkey)
			else:
				obj[key][subkey] = obj[key][subkey].lower()
	return obj

def validate_template_unique(obj):
	subkey = "unique"
	for key in obj:
		if subkey in obj[key]:
			if not isinstance(obj[key][subkey], bool) or obj[key][subkey] is not True:
				obj[key].pop(subkey)
	return obj

def validate_template_collect(obj):
	subkey = "collect"
	for key in obj:
		if subkey in obj[key]:
			if not isinstance(obj[key][subkey], bool) or obj[key][subkey] is not True:
				obj[key].pop(subkey)
	return obj

def validate_template_all(obj):
	obj = validate_template_reject(obj)
	obj = validate_template_query(obj)
	obj = validate_template_search(obj)
	obj = validate_template_ignorecase(obj)
	obj = validate_template_min_max(obj)
	obj = validate_template_decode(obj)
	obj = validate_template_unique(obj)
	obj = validate_template_collect(obj)
	return obj

# ----------------------------------------

def unique(sequence):
	seen = set()
	return [x for x in sequence if not (x in seen or seen.add(x))]

def jload_file(file, validate = True):
	tmp = []
	try:
		tmp = json.loads(open(file, "r", encoding = "ISO-8859-1").read())
	except json.decoder.JSONDecodeError:
		pass
	if validate and tmp:
		tmp = validate_template_all(tmp)
	return tmp

def jquery(obj, query, key = None):
	tmp = []
	if query == "sort_by_file":
		tmp = sorted(obj, key = lambda entry: entry["file"].casefold())
	if query == "matched":
		for entry in obj:
			if key in entry["matched"]:
				tmp.extend(entry["matched"][key])
	return tmp

def write_file(data, out):
	confirm = "yes"
	if os.path.isfile(out):
		print(("'{0}' already exists").format(out))
		confirm = input("Overwrite the output file (yes): ")
	if confirm.lower() == "yes":
		try:
			open(out, "w", encoding = "UTF-8").write(data)
			print(("Results have been saved to '{0}'").format(out))
		except FileNotFoundError:
			print(("Cannot save results to '{0}'").format(out))

# ----------------------------------------

class FileScraper:

	def __init__(self, files, template, beautify, threads, out, debug):
		self.__files      = files
		self.__template   = template
		self.__out        = out
		self.__debug      = debug
		self.__beautify   = beautify
		self.__threads    = threads
		self.__print_lock = threading.Lock()
		self.__res_enc    = "ISO-8859-1"
		self.__url_enc    = "UTF-8"
		self.__highlight  = {
			"matched": "file-scraper-matched",
			"decoded": "file-scraper-decoded"
		}
		self.__soup       = None
		self.__results    = []

	def run(self):
		print(("Files to scrape: {0}").format(len(self.__files)))
		print("Press CTRL + C to exit early - results will be saved")
		with alive_progress.alive_bar(len(self.__files), title = "Progress:") as bar:
			with concurrent.futures.ThreadPoolExecutor(max_workers = self.__threads) as executor:
				subprocesses = []
				try:
					for file in self.__files:
						subprocesses.append(executor.submit(self.__run, file))
					for subprocess in concurrent.futures.as_completed(subprocesses):
						result = subprocess.result()
						if isinstance(result, dict) and "file" in result:
							if self.__debug:
								print(result["file"])
							self.__results.append(result)
						bar()
				except KeyboardInterrupt:
					executor.shutdown(wait = True, cancel_futures = True)
		if not self.__results:
			print("No results")
		else:
			self.__results = jquery(self.__results, "sort_by_file")
			self.__set_html_content()
			stopwatch.stop()
			write_file(self.__soup, self.__out)

	def __run(self, file):
		response = None
		try:
			if self.__beautify and file.endswith(".js"):
				data = jsbeautifier.beautify_file(file)
				open(file, "w").write(data)
			response = subprocess.run(("rabin2 -zzzqq \"{0}\"").format(file), shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT).stdout
			if response:
				response = response.decode(self.__res_enc).replace("\\n", "\n")
				response = self.__grep(response)
				if response:
					response = {"file": file, "matched": response}
		except Exception as ex:
			response = None
			self.__print_error(ex)
		return response

	def __grep(self, response):
		tmp = {}
		for key in self.__template:
			subtemplate = self.__template[key]
			flags = re.MULTILINE | (re.IGNORECASE if "ignorecase" in subtemplate else 0)
			try:
				if "search" in subtemplate:
					# --------------------
					array = []
					searched = re.findall(subtemplate["search"], response, flags)
					if searched:
						if "unique" in subtemplate:
							searched = unique(searched)
						for i in range(len(searched)):
							results = {"matched": unique(re.findall(subtemplate["query"], searched[i], flags)), "decoded": []}
							if results["matched"]:
								if any(subkey in ["minimum", "maximum", "decode"] for subkey in subtemplate):
									results = self.__validate_matched(results["matched"], subtemplate)
								if results["matched"]:
									for j in range(len(results["matched"])):
										searched[i] = searched[i].replace(results["matched"][j], ("<{0}>{1}</{0}>").format(self.__highlight["matched"], results["matched"][j])).strip()
									for j in range(len(results["decoded"])):
										searched[i] += ("\n<{0}>{1}</{0}>").format(self.__highlight["decoded"], results["decoded"][j])
									array.append(searched[i])
						if array:
							tmp[key] = array
					# --------------------
				else:
					# --------------------
					results = {"matched": re.findall(subtemplate["query"], response, flags), "decoded": []}
					if "unique" in subtemplate:
						results["matched"] = unique(results["matched"])
					if any(subkey in ["minimum", "maximum", "decode"] for subkey in subtemplate):
						results = self.__validate_matched(results["matched"], subtemplate)
					if results["matched"]:
						for i in range(len(results["decoded"])):
							results["matched"][i] += ("\n<{0}>{1}</{0}>").format(self.__highlight["decoded"], results["decoded"][i])
						tmp[key] = results["matched"]
					# --------------------
			except Exception as ex:
				self.__print_error(ex)
		return tmp

	def __validate_matched(self, matched, subtemplate):
		tmp = {"matched": [], "decoded": []}
		for match in matched:
			length = len(match)
			if ("minimum" in subtemplate and length < subtemplate["minimum"]) or ("maximum" in subtemplate and length > subtemplate["maximum"]):
				continue
			if "decode" in subtemplate:
				try:
					decoded = ""
					if subtemplate["decode"] == "url":
						decoded = urllib.parse.unquote(match, encoding = self.__url_enc)
						decoded = self.__replace(decoded, binary = False)
					elif subtemplate["decode"] == "base64":
						decoded = base64.b64decode(match)
						decoded = self.__replace(decoded, binary = True)
					elif subtemplate["decode"] == "hex":
						decoded = bytes.fromhex(match.replace("0x", "").replace("\\", "").replace("x", ""))
						decoded = self.__replace(decoded, binary = True)
						match = match.replace("\\\\", "\\")
					elif subtemplate["decode"] == "cert":
						if "CERTIFICATE" in match.upper():
							decoded = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, match)
							decoded = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_TEXT, decoded)
						else:
							decoded = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, match)
							decoded = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_TEXT, decoded)
						decoded = self.__replace(decoded, binary = True)
					if decoded:
						tmp["decoded"].append(decoded)
						tmp["matched"].append(match)
				except Exception:
					continue
		return tmp

	def __replace(self, string, binary = False):
		if binary:
			return string.replace(b"\x00", b"").replace(b"\r", b"").decode(self.__url_enc).strip()
		else:
			return string.replace("\x00", "").replace("\r", "").strip()

	def __set_html_content(self):
		self.__soup = """
		<!DOCTYPE html>
		<html lang="en">
			<head>
				<meta charset="UTF-8">
				<title></filename> | File Scraper</title>
				<meta name="author" content="Ivan Šincek">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<style>
					@font-face {
						font-family: "Fira Code Medium";
						src: url("file://</font>") format("opentype");
					}
					html {
						height: 100%;
					}
					body {
						background-color: #F8F8F8;
						margin: 0;
						height: inherit;
						color: #262626;
						font-family: "Fira Code Medium", sans-serif;
						font-size: 0.8em;
						font-weight: 400;
						text-align: left;
						word-break: break-all;
					}
					nav {
						right: 0;
						bottom: 0;
						position: fixed;
						z-index: 3301;
					}
					ul {
						display: flex;
						flex-wrap: wrap;
						margin: 0;
						padding: 0;
						list-style-type: none;
					}
					div {
						/* display: flex; */
						flex-direction: column;
						padding: 1em;
					}
					div.modal {
						top: 0;
						right: 0;
						bottom: 0;
						left: 0;
						position: fixed;
					}
					a {
						text-decoration: none;
					}
					h2 {
						margin: 0.8em 0 0.2em 0;
						color: #717171;
						font-size: inherit;
						cursor: pointer;
						font-weight: inherit;
					}
					button {
						/* display: block; */
						background-color: #C8C8C8;
						padding: 0.2em 0.4em;
						color: inherit;
						font-family: inherit;
						font-size: inherit;
						text-transform: lowercase;
						text-align: inherit;
						cursor: pointer;
						border: 0.07em solid #B8B8B8;
					}
					pre {
						/* display: block; */
						background-color: #E8E8E8;
						margin: 0;
						padding: 0.2em;
						font-family: inherit;
						font-size: 1em;
						white-space: pre-wrap;
						border: 0.07em solid #B8B8B8;
					}
					div.modal pre {
						/* display: none; */
						height: 100%;
						overflow-y: scroll;
					}
					span.matched {
						color: #FF1919;
					}
					span.decoded {
						color: #1919FF;
					}
				</style>
			</head>
			<body>
				<nav>
					<ul>
						<li>
							<button onclick="collapse_all()">Hide All</button>
						</li>
						<li>
							<button onclick="uncollapse_all()">Show All</button>
						</li>
					</ul>
				</nav>
				<div style="display: flex;">
					<a href="https://github.com/ivan-sincek/file-scraper">https://github.com/ivan-sincek/file-scraper</a>
				</div>
				<div class="modal" style="display: none;"></div>
				<script>
					const nav_main = document.getElementsByTagName('nav')[0];
					const nav_main_buttons = nav_main.getElementsByTagName('button');
					// --------------------
					const div_main = document.getElementsByTagName('div')[0];
					const div_main_headers = div_main.getElementsByTagName('h2');
					const div_main_buttons = div_main.getElementsByTagName('button');
					const div_main_pres = div_main.getElementsByTagName('pre');
					// --------------------
					const div_modal = document.getElementsByTagName('div')[1];
					const div_modal_pres = div_modal.getElementsByTagName('pre');
					// --------------------
					const button_inactive = '#C8C8C8';
					const button_active = '#64C76A';
					// --------------------
					for (let i = 0; i < div_main_buttons.length; i++) {
						div_main_buttons[i].addEventListener('click', function() {
							div_main_pres[i].style.display = div_main_pres[i].style.display !== 'none' ? 'none' : 'block';
						});
					}
					// --------------------
					function set_file_method(button) {
						let header = button.previousElementSibling;
						while (header && header.tagName !== 'H2') {
							header = header.previousElementSibling;
						}
						if (button.style.display !== 'none') {
							header.setAttribute('onclick', 'collapse_file(this)');
						} else {
							header.setAttribute('onclick', 'uncollapse_file(this)');
							let next = header.nextElementSibling;
							while (next && next.tagName !== 'H2') {
								if (next.style.display !== 'none') {
									header.setAttribute('onclick', 'collapse_file(this)');
									break;
								}
								next = next.nextElementSibling;
							}
						}
					}
					function modify_file(header, display, method) {
						let next = header.nextElementSibling;
						while (next && next.tagName !== 'H2') {
							next.style.display = display;
							next = next.nextElementSibling;
						}
						header.setAttribute('onclick', method);
					}
					function collapse_file(header) {
						modify_file(header, 'none', 'uncollapse_file(this)');
					}
					function uncollapse_file(header) {
						modify_file(header, 'block', 'collapse_file(this)');
					}
					// --------------------
					function hide_modal() {
						div_modal.style.display = 'none';
						for (let i = 0; i < div_modal_pres.length; i++) {
							div_modal_pres[i].style.display = 'none';
						}
						for (let i = nav_main_buttons.length - div_modal_pres.length; i < nav_main_buttons.length; i++) {
							nav_main_buttons[i].style.backgroundColor = button_inactive;
						}
					}
					// --------------------
					function modify_all(display, method_file, method_nav, color) {
						div_main.style.display = 'flex';
						for (let i = 0; i < div_main_headers.length; i++) {
							div_main_headers[i].setAttribute('onclick', method_file);
						}
						for (let i = 0; i < div_main_buttons.length; i++) {
							div_main_buttons[i].style.display = div_main_pres[i].style.display = display
						}
						for (let i = 2; i < nav_main_buttons.length - div_modal_pres.length; i++) {
							nav_main_buttons[i].setAttribute('onclick', method_nav);
							nav_main_buttons[i].style.backgroundColor = color;
						}
						hide_modal();
					}
					function collapse_all() {
						modify_all('none', 'uncollapse_file(this)', 'uncollapse_single(this)', button_inactive);
					}
					function uncollapse_all() {
						modify_all('block', 'collapse_file(this)', 'collapse_single(this)', button_active);
					}
					// --------------------
					function modify_single(button, display, method, color) {
						div_main.style.display = 'flex';
						for (let i = 0; i < div_main_buttons.length; i++) {
							if (div_main_buttons[i].className === button.className) {
								div_main_buttons[i].style.display = div_main_pres[i].style.display = display;
								set_file_method(div_main_buttons[i]);
							}
						}
						button.setAttribute('onclick', method);
						button.style.backgroundColor = color;
						hide_modal();
					}
					function collapse_single(button) {
						modify_single(button, 'none', 'uncollapse_single(this)', button_inactive);
					}
					function uncollapse_single(button) {
						modify_single(button, 'block', 'collapse_single(this)', button_active);
					}
					// --------------------
					function pop_modal(button) {
						for (let i = nav_main_buttons.length - div_modal_pres.length; i < nav_main_buttons.length; i++) {
							nav_main_buttons[i].style.backgroundColor = button_inactive;
						}
						for (let i = 0; i < div_modal_pres.length; i++) {
							if (div_modal_pres[i].className !== button.className) {
								div_modal_pres[i].style.display = 'none';
							} else if (div_modal_pres[i].style.display !== 'none') {
								div_modal.style.display = 'none';
								div_modal_pres[i].style.display = 'none';
								div_main.style.display = 'flex';
							} else {
								div_modal.style.display = 'flex';
								div_modal_pres[i].style.display = 'block';
								button.style.backgroundColor = button_active;
								div_main.style.display = 'none';
							}
						}
					}
				</script>
			</body>
		</html>
		"""
		print(("Files with valid results: {0}").format(len(self.__results)))
		print("Generating report...")
		self.__soup = self.__soup.replace("</filename>", self.__out.rsplit(os.path.sep)[-1], 1)
		self.__soup = self.__soup.replace("</font>", os.path.join(os.path.abspath(os.path.split(__file__)[0]), "FiraCode-Medium.otf").replace("\\", "\\\\"), 1)
		self.__soup = bs4.BeautifulSoup(self.__soup, "html.parser")
		for result in self.__results:
			self.__add_header(result["file"])
			for key in result["matched"]:
				self.__add_results(key, ("\n").join(result["matched"][key]))
		for key in self.__template:
			if "collect" in self.__template[key]:
				tmp = jquery(self.__results, "matched", key)
				if tmp:
					self.__add_collection(key, ("\n").join(sorted(unique(tmp), key = str.casefold)))
		self.__soup = self.__soup.prettify()
		for key in self.__highlight:
			self.__soup = self.__soup.replace(("&lt;{0}&gt;").format(self.__highlight[key]), ("<span class=\"{0}\">").format(key))
			self.__soup = self.__soup.replace(("&lt;/{0}&gt;").format(self.__highlight[key]), "</span>")
			self.__soup = re.sub(r"\s?</span>", "</span>", self.__soup)

	def __add_header(self, filename):
		attributes = {"onclick": "collapse_file(this)"}
		h2 = self.__soup.new_tag("h2", **attributes)
		h2.string = filename
		self.__soup.html.body.find_all("div")[0].append(h2)

	def __add_results(self, key, results):
		attributes = {"class": key, "onclick": "collapse_single(this)", "style": "background-color: #64C76A;"}
		if not self.__soup.html.body.nav.ul.find_all("button", attributes):
			button = self.__soup.new_tag("button", **attributes)
			button.string = key
			li = self.__soup.new_tag("li")
			li.append(button)
			self.__soup.html.body.nav.ul.append(li)
		# --------------------------------
		attributes = {"class": key, "style": "display: block;"}
		button = self.__soup.new_tag("button", **attributes)
		button.string = key
		self.__soup.html.body.find_all("div")[0].append(button)
		# --------------------------------
		attributes = {"style": "display: block;"}
		pre = self.__soup.new_tag("pre", **attributes)
		pre.string = results
		self.__soup.html.body.find_all("div")[0].append(pre)

	def __add_collection(self, key, collection):
		attributes = {"class": key, "onclick": "pop_modal(this)", "style": "background-color: #C8C8C8;"}
		if not self.__soup.html.body.nav.ul.find_all("button", attributes):
			button = self.__soup.new_tag("button", **attributes)
			button.string = key + " all"
			li = self.__soup.new_tag("li")
			li.append(button)
			self.__soup.html.body.nav.ul.append(li)
		# --------------------------------
		attributes = {"class": key, "style": "display: none;"}
		pre = self.__soup.new_tag("pre", **attributes)
		pre.string = collection
		self.__soup.html.body.find_all("div")[1].append(pre)

	def __print_error(self, ex):
		with self.__print_lock:
			print(ex)

# ----------------------------------------

class MyArgParser(argparse.ArgumentParser):

	def print_help(self):
		print("File Scraper v3.2 ( github.com/ivan-sincek/file-scraper )")
		print("")
		print("Usage:   file-scraper -dir directory -o out          [-t template     ] [-e excludes    ] [-th threads]")
		print("Example: file-scraper -dir decoded   -o results.html [-t template.json] [-e jpeg,jpg,png] [-th 10     ]")
		print("")
		print("DESCRIPTION")
		print("    Scrape files for sensitive information")
		print("DIRECTORY")
		print("    Directory containing files, or a single file to scrape")
		print("    -dir, --directory> = decoded | files | test.exe | etc.")
		print("TEMPLATE")
		print("    Template file with extraction details, or a single RegEx to use")
		print("    Default: built-in JSON template file")
		print("    -t, --template = template.json | \"secret\\: [\\w\\d]+\" | etc.")
		print("EXCLUDES")
		print("    Exclude all files that end with the specified extension")
		print("    Specify 'default' to load the built-in list")
		print("    Use comma-separated values")
		print("    -e, --excludes = mp3 | default,jpeg,jpg,png | etc.")
		print("INCLUDES")
		print("    Include all files that end with the specified extension")
		print("    Overrides excludes")
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
		print("    Output HTML file")
		print("    -o, --out = results.html | etc.")
		print("DEBUG")
		print("    Debug output")
		print("    -dbg, --debug")

	def error(self, message):
		if len(sys.argv) > 1:
			print("Missing a mandatory option (-dir, -o) and/or optional (-t, -e, -i, -b, -th)")
			print("Use -h or --help for more info")
		else:
			self.print_help()
		exit()

class Validate:

	def __init__(self):
		self.__proceed = True
		self.__parser  = MyArgParser()
		self.__parser.add_argument("-dir", "--directory", required = True , type   = str         , default = ""   )
		self.__parser.add_argument("-t"  , "--template" , required = False, type   = str         , default = ""   )
		self.__parser.add_argument("-e"  , "--excludes" , required = False, type   = str.lower   , default = ""   )
		self.__parser.add_argument("-i"  , "--includes" , required = False, type   = str.lower   , default = ""   )
		self.__parser.add_argument("-b"  , "--beautify" , required = False, action = "store_true", default = False)
		self.__parser.add_argument("-th" , "--threads"  , required = False, type   = str         , default = ""   )
		self.__parser.add_argument("-o"  , "--out"      , required = True , type   = str         , default = ""   )
		self.__parser.add_argument("-dbg", "--debug"    , required = False, action = "store_true", default = False)

	def run(self):
		self.__args           = self.__parser.parse_args()
		self.__args.directory = self.__parse_directory(self.__args.directory) # required
		self.__args.template  = self.__parse_template(self.__args.template)   if self.__args.template else self.__load_default_template()
		self.__args.excludes  = self.__parse_excludes(self.__args.excludes)   if self.__args.excludes else []
		self.__args.includes  = self.__parse_includes(self.__args.includes)   if self.__args.includes else []
		self.__args.threads   = self.__parse_threads(self.__args.threads)     if self.__args.threads  else 30
		self.__filter_directory()
		self.__args           = vars(self.__args)
		return self.__proceed

	def get_arg(self, key):
		return self.__args[key]

	def __error(self, msg):
		self.__proceed = False
		self.__print_error(msg)

	def __print_error(self, msg):
		print(("ERROR: {0}").format(msg))

	def __parse_directory(self, value):
		tmp = []
		if not os.path.exists(value):
			self.__error("Directory containing files, or a single file does not exist")
		elif os.path.isdir(value):
			tmp = validate_directory_files(value)
			if not tmp:
				self.__error("No valid files were found")
		else:
			if not os.access(value, os.R_OK):
				self.__error("File does not have a read permission")
			elif not os.stat(value).st_size > 0:
				self.__error("File is empty")
			else:
				tmp = [value]
		return tmp

	def __filter_directory(self):
		if self.__proceed:
			if self.__args.includes:
				tmp = []
				for file in self.__args.directory:
					if any(file.endswith(ext) for ext in self.__args.includes):
						tmp.append(file)
				self.__args.directory = tmp
			elif self.__args.excludes:
				tmp = []
				for file in self.__args.directory:
					if not any(file.endswith(ext) for ext in self.__args.excludes):
						tmp.append(file)
				self.__args.directory = tmp
			if not self.__args.directory:
				self.__error("No valid files were found")

	def __build_template(self, query):
		const = ".*"
		return {
			"query": {
				"query": query,
				"ignorecase": True,
				"search": const + query.strip(const) + const,
				"collect": True
			}
		}

	def __parse_template(self, value):
		tmp = {}
		if os.path.isfile(value):
			if not os.access(value, os.R_OK):
				self.__error("Template file does not have a read permission")
			elif not os.stat(value).st_size > 0:
				self.__error("Template file is empty")
			else:
				tmp = jload_file(value)
				if not tmp:
					self.__error("Template file does not have the correct structure")
		else:
			try:
				re.compile(value)
				tmp = self.__build_template(value)
			except re.error as ex:
				self.__error("Invalid RegEx")
		return tmp

	def __load_default_template(self):
		tmp = {}
		file = os.path.join(os.path.abspath(os.path.split(__file__)[0]), "default.json")
		if os.path.isfile(file) and os.access(file, os.R_OK) and os.stat(file).st_size > 0:
			tmp = jload_file(file)
		if not tmp:
			self.__error("Cannot load the default JSON template file")
		return tmp

	def __parse_excludes(self, value):
		tmp = []
		for entry in value.lower().split(","):
			entry = entry.strip()
			if not entry:
				continue
			elif entry == "default":
				tmp += ["car", "css", "gif", "jpeg", "jpg", "mp3", "mp4", "nib", "ogg", "otf", "eot", "png", "storyboard", "strings", "svg", "ttf", "webp", "woff", "woff2", "xib", "vtt"]
			else:
				tmp.append(entry)
		return unique(tmp)

	def __parse_includes(self, value):
		tmp = []
		for entry in value.lower().split(","):
			entry = entry.strip()
			if entry:
				tmp.append(entry)
		return unique(tmp)

	def __parse_threads(self, value):
		if not value.isdigit():
			self.__error("Number of parallel threads must be numeric")
		else:
			value = int(value)
			if value <= 0:
				self.__error("Number of parallel threads must be greater than zero")
		return value

# ----------------------------------------

def main():
	validate = Validate()
	if validate.run():
		print("###########################################################################")
		print("#                                                                         #")
		print("#                            File Scraper v3.2                            #")
		print("#                                    by Ivan Sincek                       #")
		print("#                                                                         #")
		print("# Scrape files for sensitive information.                                 #")
		print("# GitHub repository at github.com/ivan-sincek/file-scraper.               #")
		print("# Feel free to donate ETH at 0xbc00e800f29524AD8b0968CEBEAD4cD5C5c1f105.  #")
		print("#                                                                         #")
		print("###########################################################################")
		file_scraper = FileScraper(
			validate.get_arg("directory"),
			validate.get_arg("template"),
			validate.get_arg("beautify"),
			validate.get_arg("threads"),
			validate.get_arg("out"),
			validate.get_arg("debug")
		)
		file_scraper.run()

if __name__ == "__main__":
	main()
