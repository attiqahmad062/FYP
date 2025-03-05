# ner/scrapy_runner.py

import sys
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from apt.scrapy.tutorial.spiders.mittreattack import mittreattack # imported crawler

def run_scrapy_spider():
    # Set the Scrapy settings (it will look for settings.py in the 'tutorial' module)
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    # Connect the spider finished signal to a callback function
    def spider_finished():
        print("Spider finished.")
    
    process.crawl(ExampleSpider)
    process.start()  # This will block until the crawling is done
