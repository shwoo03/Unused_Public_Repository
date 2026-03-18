from fuzzers.file_download.File_Download import FileDownloadVulnerabilitySpider
from scrapy.crawler import CrawlerProcess


def file_download():
    process = CrawlerProcess()
    process.crawl(FileDownloadVulnerabilitySpider)
    process.start()
