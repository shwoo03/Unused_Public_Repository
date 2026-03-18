"""
Scrapy + Playwright 기본 설정.
runspider로 실행 시 스파이더의 custom_settings가 우선 적용됩니다.
"""

import os

BOT_NAME = "fuzzingzzingi"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

USER_AGENT = "FuzzingzzingiCrawler/0.2 (+https://example.com)"
ROBOTSTXT_OBEY = False
LOG_LEVEL = "INFO"

DOWNLOAD_TIMEOUT = 30
CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# 프록시는 스파이더 인자나 환경변수 HTTP_PROXY/HTTPS_PROXY로 주입합니다. (기본값: 사용 안 함)
PROXY = os.environ.get("HTTP_PROXY", "")

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30_000
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# SQLite 경로 (환경변수 SQLITE_PATH로 덮어쓰기 가능)
SQLITE_PATH = os.environ.get("SQLITE_PATH", "data/crawl.db")

# ITEM_PIPELINES는 스파이더 custom_settings에서 활성화됨

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
