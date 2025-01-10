# File Scraper

Scrape files for sensitive information, and generate an interactive HTML report. Based on Rabin2.

This tool is only as good as your [RegEx](https://github.com/ivan-sincek/file-scraper?tab=readme-ov-file#build-the-template--run) skills.

You can also style your own [report](https://github.com/ivan-sincek/file-scraper/blob/main/src/file_scraper/reports/default.html).

Tested on Kali Linux v2024.2 (64-bit).

Made for educational purposes. I hope it will help!

## Table of Contents

* [How to Install](#how-to-install)
	* [Install Radare2](#install-radare2)
	* [Standard Install](#standard-install)
	* [Build and Install From the Source](#build-and-install-from-the-source)
* [Build the Template & Run](#build-the-template--run)
* [Usage](#usage)
* [Images](#images)

## How to Install

### Install Radare2

On Kali Linux, run:

```bash
apt-get -y install radare2
```

---

On Windows OS, download and unpack [radareorg/radare2](https://github.com/radareorg/radare2/releases), then, add the `bin` directory to Windows `PATH` environment variable.

---

On macOS, run:

```bash
brew install radare2
```

### Standard Install

```bash
pip3 install --upgrade file-scraper
```

### Build and Install From the Source

```bash
git clone https://github.com/ivan-sincek/file-scraper && cd file-scraper

python3 -m pip install --upgrade build

python3 -m build

python3 -m pip install dist/file_scraper-4.5-py3-none-any.whl
```

## Build the Template & Run

Prepare a template such as [the default template](https://github.com/ivan-sincek/file-scraper/blob/main/src/file_scraper/templates/default.json):

```json
{
   "Auth.":{
      "query":"(?:basic|bearer)\\ ",
      "ignorecase":true,
      "search":true
   },
   "Variables":{
      "query":"(?:access|account|admin|auth|card|conf|cookie|cred|customer|email|history|ident|info|jwt|key|kyc|log|otp|pass|pin|priv|refresh|salt|secret|seed|session|setting|sign|token|transaction|transfer|user)[\\w\\d\\-\\_]*(?:\\\"\\ *\\:|\\ *\\=[^\\=]{1})",
      "ignorecase":true,
      "search":true
   },
   "Comments":{
      "query":"(?:(?<!\\:)\\/\\/|\\#).*(?:bug|compatibility|crash|deprecated|fix|issue|legacy|problem|review|security|todo|to do|to-do|to_do|vuln|warning)",
      "ignorecase":true,
      "search":true
   },
   "Abs. URL":{
      "query":"[\\w\\d\\+]*\\:\\/\\/[\\w\\d\\@\\-\\_\\.\\:\\/\\?\\&\\=\\%\\#]+",
      "unique":true,
      "collect":true
   },
   "IPv4":{
      "query":"(?:\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(?:\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}",
      "unique":true,
      "collect":true
   },
   "Base64":{
      "query":"(?:[a-zA-Z0-9\\+\\/]{4})*(?:[a-zA-Z0-9\\+\\/]{4}|[a-zA-Z0-9\\+\\/]{3}\\=|[a-zA-Z0-9\\+\\/]{2}\\=\\=)",
      "minimum":8,
      "decode":"base64",
      "minimum_decode":6,
      "unique":true,
      "collect":true
   },
   "HEX":{
      "query":"(?:(?:0x|(?:\\\\)+x)[a-fA-F0-9]{2})+|(?:[a-fA-F0-9]{2})+",
      "minimum":12,
      "decode":"hex",
      "minimum_decode":6,
      "unique":true,
      "collect":true
   },
   "PEM":{
      "query":"-----BEGIN (?:CERTIFICATE|PRIVATE KEY)-----[\\s\\S]+?-----END (?:CERTIFICATE|PRIVATE KEY)-----",
      "decode":"pem",
      "unique":true,
      "collect":true
   }
}
```

**Make sure your regular expressions return only one capturing group, e.g., `[1, 2, 3, 4]`; and not a touple, e.g., `[(1, 2), (3, 4)]`.**

Make sure to properly escape regular expression specific symbols in your template file, e.g., make sure to escape dot `.` as `\\.`, and forward slash `/` as `\\/`, etc.

| Name | Type | Required |Description |
| --- | --- | --- | --- |
| query | str | yes | Regular expression query. |
| search | bool | no | Highlight matches within the searched lines; otherwise, extract the matches. |
| ignorecase | bool | no | Case-insensitive search. |
| minimum | int | no | Only accept matches longer than `int` characters. |
| maximum | int | no | Only accept matches lesser than `int` characters. |
| decode | str | no | Decode the matches. Available decodings: `url`, `base64` `hex`, `pem`. |
| minimum_decode | int | no | Only accept decodings longer than `int` characters. |
| maximum_decode | int | no | Only accept decodings lesser than `int` characters. |
| unique | bool | no | Filter out duplicates. |
| collect | bool | no | Collect all the matches in one place. |

`minimum_decode` and `maximum_decode` will check the length of the decoded string after bad characters are removed.

---

How I typically run the tool:

```fundamental
file-scraper -dir directory -o results.html -e default
```

Default (built-in) exclude file types:

```fundamental
car, css, gif, jpeg, jpg, mp3, mp4, nib, ogg, otf, eot, png, storyboard, strings, svg, ttf, webp, woff, woff2, xib, vtt
```

## Usage

```fundamental
File Scraper v4.5 ( github.com/ivan-sincek/file-scraper )

Usage:   file-scraper -dir directory -o out          [-t template     ] [-th threads]
Example: file-scraper -dir decoded   -o results.html [-t template.json] [-th 10     ]

DESCRIPTION
    Scrape files for sensitive information
DIRECTORY
    Directory containing files or a single file to scrape
    -dir, --directory> = decoded | files | test.exe | etc.
TEMPLATE
    File containing extraction details or a single RegEx to use
    Default: built-in JSON template file
    -t, --template = template.json | "secret\: [\w\d]+" | etc.
EXCLUDES
    Exclude all files ending with the specified extension
    Specify 'default' to load the built-in list
    Use comma-separated values
    -e, --excludes = mp3 | default,jpg,png | etc.
INCLUDES
    Include all files ending with the specified extension
    Overrides the excludes
    Use comma-separated values
    -i, --includes = java | json,xml,yaml | etc.
BEAUTIFY
    Beautify [minified] JavaScript (.js) files
    -b, --beautify
THREADS
    Number of parallel threads to run
    Default: 30
    -th, --threads = 10 | etc.
OUT
    Output file
    -o, --out = results.html | etc.
DEBUG
    Enable debug output
    -dbg, --debug
```

## Images

<p align="center"><img src="https://github.com/ivan-sincek/file-scraper/blob/main/img/interactive_report_1.png" alt="Interactive Report (1)"></p>

<p align="center">Figure 1 - Interactive Report (1)</p>

<p align="center"><img src="https://github.com/ivan-sincek/file-scraper/blob/main/img/interactive_report_2.png" alt="Interactive Report (2)"></p>

<p align="center">Figure 2 - Interactive Report (2)</p>

<p align="center"><img src="https://github.com/ivan-sincek/file-scraper/blob/main/img/interactive_report_3.png" alt="Interactive Report (3)"></p>

<p align="center">Figure 3 - Interactive Report (3)</p>
