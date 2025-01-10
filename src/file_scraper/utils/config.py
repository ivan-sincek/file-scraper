#!/usr/bin/env python3

APP_VERSION = "v4.5"

EXCLUDES = ["car", "css", "gif", "jpeg", "jpg", "mp3", "mp4", "nib", "ogg", "otf", "eot", "png", "storyboard", "strings", "svg", "ttf", "webp", "woff", "woff2", "xib", "vtt"]
"""
List of file extensions.
"""

def banner():
	"""
	Display the banner.
	"""
	print("#########################################################################")
	print("#                                                                       #")
	print("#                           File Scraper v4.5                           #")
	print("#                                   by Ivan Sincek                      #")
	print("#                                                                       #")
	print("# Scrape files for sensitive information.                               #")
	print("# GitHub repository at github.com/ivan-sincek/file-scraper.             #")
	print("#                                                                       #")
	print("#########################################################################")
