import contextlib
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import scrapy
import tldextract
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.exceptions import DropItem
from scrapy_playwright.page import PageMethod

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PIPELINE_PATH = f"{__name__}.DuplicateURLPipeline"


def get_env(name: str, default: str) -> str:
    return os.environ.get(name, default)


class PlaywrightSpider(scrapy.Spider):
    name = "crawler"

    custom_settings = {
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30_000,
        "CONCURRENT_REQUESTS": 32,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            PIPELINE_PATH: 100,
        },
    }

    def __init__(
        self,
        start_url: Optional[str] = None,
        proxy_url: Optional[str] = None,
        cookies_file: str = "cookie_header.txt",
        max_depth: int = 3,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url 인자가 필요합니다.")

        self.start_urls = [start_url]
        if proxy_url is None or str(proxy_url).lower() in {"", "none"}:
            self.proxy_url = None
        else:
            self.proxy_url = proxy_url
        if not self.proxy_url:
            env_proxy = get_env("HTTP_PROXY", "")
            self.proxy_url = env_proxy or None

        self.domain_origin = tldextract.extract(self.start_urls[0]).registered_domain
        self.output_file = "output.txt"
        self.seen_urls = set()
        self.max_depth = max_depth

        self.cookies = self.load_cookies(cookies_file)

    def load_cookies(self, cookies_file: str) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        if not os.path.exists(cookies_file):
            logging.info("쿠키 파일이 없습니다: %s", cookies_file)
            return cookies

        with open(cookies_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    name, value = line.strip().split("=", 1)
                    cookies[name] = value
        logging.info("쿠키 %d개 로드 완료 (%s)", len(cookies), cookies_file)
        return cookies

    async def start(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield self._build_request(url, depth=0)

    def _build_request(self, url: str, depth: int) -> Request:
        return scrapy.Request(
            url=url,
            callback=self.parse,
            cookies=self.cookies,
            meta={
                "depth": depth,
                "playwright": True,
                "playwright_context_kwargs": self._context_kwargs(),
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 1500),
                    PageMethod(
                        "evaluate",
                        """
                        document.querySelectorAll('[onclick]').forEach((el) => {
                            const href = el.getAttribute('href') || '';
                            if (href.includes('logout.php')) { return; }
                            try { el.click(); } catch (e) {}
                        });
                        """,
                    ),
                ],
                "errback": self.errback,
            },
        )

    def parse(self, response: HtmlResponse):
        try:
            normalized_url = self.normalize_url(response.url)

            if self._should_skip_response(response, normalized_url):
                return

            self._remember_url(normalized_url)
            yield {"url": normalized_url}

            depth = response.meta.get("depth", 0)
            if depth >= self.max_depth:
                return

            for link in self.extract_links(response):
                yield self._build_request(link, depth=depth + 1)

        except Exception as exc:  # pylint: disable=broad-except
            logging.error("parse 에러: %s", exc)

    def _should_skip_response(self, response: HtmlResponse, normalized_url: str) -> bool:
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore")
        logging.debug("Content-Type for %s: %s", response.url, content_type)

        if content_type and not content_type.startswith("text"):
            logging.debug("비-텍스트 콘텐츠 스킵: %s", response.url)
            return True

        if normalized_url in self.seen_urls:
            logging.debug("이미 방문한 URL 스킵: %s", normalized_url)
            return True

        return False

    def _remember_url(self, normalized_url: str) -> None:
        self.seen_urls.add(normalized_url)
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(f"{normalized_url}\n")
            f.flush()

    def extract_links(self, response: HtmlResponse) -> Iterable[str]:
        a_links = response.xpath("//a/@href").getall()
        logging.debug("링크 %d개 발견: %s", len(a_links), response.url)

        for link in a_links:
            absolute = response.urljoin(link)
            normalized = self.normalize_url(absolute)

            if self._is_in_scope(normalized):
                yield normalized

    def _is_in_scope(self, url: str) -> bool:
        if url.endswith("logout.php"):
            return False

        domain = tldextract.extract(url).registered_domain
        if domain != self.domain_origin:
            return False

        if url in self.seen_urls:
            return False

        return True

    def normalize_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        filtered_query = {k: v for k, v in query.items() if k not in ["random", "session", "timestamp"]}
        normalized_query = urlencode(filtered_query, doseq=True)

        normalized_url = urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                normalized_query,
                parsed_url.fragment,
            )
        )
        logging.debug("정규화 URL: %s", normalized_url)
        return normalized_url

    def _context_kwargs(self) -> Dict:
        context_kwargs: Dict = {
            "ignore_https_errors": True,
        }
        if self.proxy_url:
            context_kwargs["proxy"] = {"server": self.proxy_url}
        return context_kwargs

    async def errback(self, failure):
        logging.error("요청 실패: %s", failure)


class DuplicateURLPipeline:
    """중복 URL 제거 및 SQLite 기록 파이프라인."""

    def __init__(self, db_connection):
        self.seen_urls = set()
        self.db_connection = db_connection
        self.cursor = db_connection.cursor()

    @classmethod
    def from_crawler(cls, crawler):
        db_path = Path(os.environ.get("SQLITE_PATH", "data/crawl.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS collected_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
            """
        )
        return cls(conn)

    def close_spider(self, spider):
        try:
            self.db_connection.commit()
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("커밋 실패: %s", exc)
        finally:
            with contextlib.suppress(Exception):
                self.cursor.close()
                self.db_connection.close()

    def process_item(self, item, spider):
        normalized_url = spider.normalize_url(item["url"])
        if normalized_url in self.seen_urls:
            raise DropItem(f"Duplicate URL found: {item['url']}")

        self.seen_urls.add(normalized_url)
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO collected_urls (url) VALUES (?)",
                (normalized_url,),
            )
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("URL DB 저장 실패: %s", exc)
            self.db_connection.rollback()
        return item


# scrapy runspider crawler.py -a start_url=http://localhost/DVWA/
