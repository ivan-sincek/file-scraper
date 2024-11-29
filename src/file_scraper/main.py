#!/usr/bin/env python3

from .utils import config, scrape, validate

def main():
	success, args = validate.Validate().validate_args()
	if success:
		config.banner()
		scraper = scrape.FileScraper(
			args.directory,
			args.template,
			args.beautify,
			args.threads,
			args.out,
			args.debug
		)
		scraper.run()

if __name__ == "__main__":
	main()
