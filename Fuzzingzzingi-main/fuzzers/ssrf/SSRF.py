import requests
import mysql.connector
import re
from colorama import init, Fore, Style
import json
import validators
from fuzzers.ssrf.local import LOCAL


class SSRF:
    def __init__(self):
        self.basic_payload = open('payloads/SSRF/basic_ssrf_payloads.txt', 'r', encoding='utf-8')
        self.ssrf_payload = open('payloads/SSRF/ssrf_payloads.txt', 'r', encoding='utf-8')
        self.ssrf_whitelist_payload = open('payloads/SSRF/ssrf_whitelist_payloads.txt', 'r', encoding='utf-8')

        self.target_param = re.compile(r'(url|path|file|image|api|locate)')
        self.target_resp = '2UDkb36hDLPMzInN3FDvVf527tQzfKMx+Lj96kZUbBocXMw9ylIPEBeq+5sQ8CRVlwcq7fapCnCtQa4'
        self.mylocalhost = 'http://localhost:8080'
        self.local_server = LOCAL()  # Initialize the local server
        self.local_server.start_server()  # Start the local server

        self.connection = None
        self.cursor = None

    def get_url(self):
        url_list = []

        try:
            self.connection = mysql.connector.connect(
                host="13.209.63.65",
                database="Fuzzingzzingi",
                user="zzingzzingi",
                password="!Ru7eP@ssw0rD!12"
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()

                self.cursor.execute(f'SELECT url FROM requests;')
                result = self.cursor.fetchall()

                for url in result:
                    url_list.append(url[0])

        except Exception as e:
            print(f"SQL connect error : {e} ")

        return url_list

    def get_params(self, url):
        json_result = []

        self.cursor.execute('SELECT method, parameters FROM requests WHERE url=%s', (url,))
        result = self.cursor.fetchall()

        for(method, parameters) in result:
            json_data = json.loads(parameters)
            json_result.append((method, json_data))

        return json_result

    def checkParamUrlPattern(self, param):
        if validators.url(param):
            return True
        else:
            return False

    def get_payloads(self):
        ssrf_payloads = []
        white_payloads = []

        ssrf = self.ssrf_payload.readlines()
        white = self.ssrf_whitelist_payload.readlines()

        for s in ssrf:
            ssrf_payloads.append(s.strip())
        for w in white:
            white_payloads.append(w.strip())

        return ssrf_payloads, white_payloads

    def get_basic_payloads(self):
        basic_payloads = []

        basic = self.basic_payload.readlines()

        for b in basic:
            basic_payloads.append(b.strip())

        return basic_payloads

    def check_param(self, param):
        for key in param:
            if not self.target_param.search(key.lower()):
                return False

        return True

    def requestingSSRF_check(self, url, method, param, payload, local_request):
        if method == 'GET':
            try:
                resp = requests.get(url, params=param)
                status = int(resp.status_code) - 1

                if status >= 200 and status < 400:
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param

                elif self.target_resp in resp.text or self.local_server.get_trigger():  # Check the trigger
                    print(f"Checked Basic payload = {payload}")
                    self.local_server.reset_trigger()  # Reset the trigger
                    return url, method, param

            except Exception as e:
                if "Connection refused" in str(e):
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param

                elif "Timeout" in str(e):
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param
                else:
                    print(f"REQUEST ERROR : {payload}")

        elif method == 'POST':
            try:
                resp = requests.post(url, data=param)
                status = int(resp.status_code) - 1

                if status >= 200 and status < 400:
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param

                elif self.target_resp in resp.text or self.local_server.get_trigger():  # Check the trigger
                    print(f"Checked Basic payload = {payload}")
                    self.local_server.reset_trigger()  # Reset the trigger
                    return url, method, param

            except Exception as e:
                if "Connection refused" in str(e):
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param
                elif "Timeout" in str(e):
                    print(f"Checked Basic payload = {payload}")
                    return url, method, param
                else:
                    print(f"REQUEST ERROR : {payload}")
        return False # 테스트 시 조정

    def requestingSSRF_execute(self, url, method, param, payload):
        if method == 'GET':
            try:
                resp = requests.get(url, params=param)
                print(f"{Style.BRIGHT}{Fore.RED}SSRF{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp.status_code}")

            except Exception as e:
                print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}")

        elif method == 'POST':
            try:
                resp = requests.post(url, data=param)
                print(f"{Style.BRIGHT}{Fore.RED}SSRF{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp.status_code}")

            except Exception as e:
                print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}")
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}!!!\tThere is no SSRF Vulnerability\t!!!{Style.RESET_ALL}")

    def check_ssrf(self, url, method, param, local_request):
        if param:
            if self.check_param(param):
                basic_payloads = self.get_basic_payloads()
                for payload in basic_payloads:
                    for key in param:
                        if self.checkParamUrlPattern(param[key]):
                            payload = self.mylocalhost
                            param[key] = self.mylocalhost
                            print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')
                            return self.requestingSSRF_check(url, method, param, payload, local_request)

                        else:
                            param[key] = payload
                            print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')
                            return self.requestingSSRF_check(url, method, param, payload, local_request)
            else:
                print(f'NO TARGET PARAMETER IN THIS URL : {url}')

        return False # 테스트 시 조정

    def execute_injection(self, url, method, param, payloads):
        init()
        for payload in payloads:
            payload = payload.strip()
            for key in param.keys():
                param[key] = payload
                self.requestingSSRF_execute(url, method, param, payload)

    def execute_whitelist(self, url, method, param, payloads):
        init()
        inject_url = url
        # whitelist 기반 우회 시도
        for payload in payloads:
            payload = payload.strip()
            inject_url += payload

            if method:
                try:
                    resp = requests.get(url, params=param)
                    print(f"{Style.BRIGHT}{Fore.RED}SSRF{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : WHITELIST\t PAYLOAD : {payload}\t STATUS : {resp.status_code}")

                except Exception as e:
                    print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}")

            inject_url = url

    def execute_ssrf(self, url, method, param, ssrf_payloads, white_payloads):
        local_request = self.local_server.get_trigger()
        check_result = self.check_ssrf(url, method, param, local_request)

        if check_result:
            checked_url, checked_method, checked_param = check_result
            print(f'EXECUTING SSRF FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            self.execute_whitelist(checked_url, checked_method, checked_param, white_payloads)
            self.execute_injection(checked_url, checked_method, checked_param, ssrf_payloads)

        self.local_server.reset_trigger()  # Reset the trigger after execution

    def close_file(self):
        self.ssrf_whitelist_payload.close()
        self.ssrf_payload.close()
