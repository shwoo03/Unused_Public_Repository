import requests
import mysql.connector
import time
from urllib.parse import quote, parse_qs
import json
from colorama import init, Fore, Style
import os

class SqlInjection:
    def __init__(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        payload_dir = os.path.join(base_path, "..", "..", "payloads", "SQL Injection", "basic_payloads")

        try:
            with open(os.path.join(payload_dir, "union_based.txt"), 'r', encoding='utf-8') as union:
                self.basic_union = [u.strip() for u in union.readlines()]
        except FileNotFoundError:
            print("union_based.txt file not found.")
            self.basic_union = []

        try:
            with open(os.path.join(payload_dir, "error_based.txt"), 'r', encoding='utf-8') as error:
                self.basic_error = [e.strip() for e in error.readlines()]
        except FileNotFoundError:
            print("error_based.txt file not found.")
            self.basic_error = []

        try:
            with open(os.path.join(payload_dir, "time_based.txt"), 'r', encoding='utf-8') as ttime:
                self.basic_time = [t.strip() for t in ttime.readlines()]
        except FileNotFoundError:
            print("time_based.txt file not found.")
            self.basic_time = []

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

    def get_payloads(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        payload_dir = os.path.join(base_path, "..", "..", "payloads", "SQL Injection", "main_payloads")

        payloads_simple = []
        payloads_union = []
        payloads_error = []
        payloads_blind = []
        payloads_time = []

        try:
            with open(os.path.join(payload_dir, "simple_payload.txt"), 'r', encoding='utf-8') as file:
                payloads_simple = [s.strip() for s in file.readlines()]
        except FileNotFoundError:
            print("simple_payload.txt file not found.")

        try:
            with open(os.path.join(payload_dir, "union_payload.txt"), 'r', encoding='utf-8') as file:
                payloads_union = [u.strip() for u in file.readlines()]
        except FileNotFoundError:
            print("union_payload.txt file not found.")

        try:
            with open(os.path.join(payload_dir, "error_payload.txt"), 'r', encoding='utf-8') as file:
                payloads_error = [e.strip() for e in file.readlines()]
        except FileNotFoundError:
            print("error_payload.txt file not found.")

        try:
            with open(os.path.join(payload_dir, "blind_payload.txt"), 'r', encoding='utf-8') as file:
                payloads_blind = [b.strip() for b in file.readlines()]
        except FileNotFoundError:
            print("blind_payload.txt file not found.")

        try:
            with open(os.path.join(payload_dir, "time_payload.txt"), 'r', encoding='utf-8') as file:
                payloads_time = [t.strip() for t in file.readlines()]
        except FileNotFoundError:
            print("time_payload.txt file not found.")

        return payloads_simple, payloads_union, payloads_error, payloads_blind, payloads_time

    def encoding_payloads(self, payload_list):
        spc_list = ["'", '"', ' ', '(', ')', '|', '&', '=']
        for payload in payload_list:
            for char in payload:
                if char in spc_list:
                    payload = payload.replace(char, quote(char))
                    payload_list.append(payload)

        return payload_list

    def checksqli_union(self, url, method, param):
        # union
        if param:
            for union_base in self.basic_union:
                for key in param:
                    param[key] = union_base
                    print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')
                    if method == 'GET':
                        try:
                            resp = requests.get(url, params=param, allow_redirects=True)
                            if resp.status_code == 200 or resp.is_redirect:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {union_base}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {union_base}')

                    elif method == 'POST':
                        try:
                            resp = requests.post(url, data=param, allow_redirects=True)
                            if resp.status_code == 200 or resp.is_redirect:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {union_base}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {union_base}')

        return False

    def checksqli_error(self, url, method, param):
        # error based
        if param:
            for error_base in self.basic_error:
                for key in param:
                    param[key] = error_base
                    print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')
                    if method == 'GET':
                        try:
                            resp = requests.get(url, params=param)
                            if resp.status_code == 500 and 'Fuzzingzzing' in resp.text:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {error_base}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {error_base}')

                    elif method == 'POST':
                        try:
                            resp = requests.post(url, data=param)
                            if resp.status_code == 500 and 'Fuzzingzzing' in resp.text:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {error_base}")
                                return url, method, param

                        except Exception as e:
                            print(f'REQUEST ERROR : {error_base}')
        return False

    def checksqli_time(self, url, method, param):
        # time based
        if param:
            for time_base in self.basic_time:
                for key in param:
                    param[key] = time_base
                    print(f'CHECKING...\turl : {url}\t\tmethod : {method}\t\tpayload : {param}')

                    if method == 'GET':
                        try:
                            start_time = time.time()
                            resp = requests.get(url, params=param, timeout=7)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {time_base}")
                                return url, method, param

                        except Exception as e:
                            if "Timeout" in str(e):
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {time_base}")
                                return url, method, param
                            else:
                                print(f'REQUEST ERROR : {time_base}')

                    elif method == 'POST':
                        try:
                            start_time = time.time()
                            resp = requests.post(url, data=param, timeout=7)
                            end_time = time.time() - start_time
                            if int(end_time) >= 5:
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {time_base}")
                                return url, method, param

                        except Exception as e:
                            if "Timeout" in str(e):
                                print(f"{Fore.RED}checked{Style.RESET_ALL}basic payload = {time_base}")
                            else:
                                print(f'REQUEST ERROR : {time_base}')
        return False

    def execute_simple(self, url, method, param, payloads):
        init()
        for payload_simple in payloads:
            for key in param:
                param[key] = payload_simple

                if method == 'GET':
                    try:
                        resp = requests.get(url, params=param)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_simple}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_simple}")

                elif method == 'POST':
                    try:
                        resp = requests.post(url, data=param)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_simple}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_simple}")

        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}SIMPLE PAYLOAD DOESN'T WORKS{Style.RESET_ALL}")

    def execute_union(self, url, method, param, payloads):
        init()
        for payload_union in payloads:
            for key in param:
                param[key] = payload_union

                if method == 'GET':
                    try:
                        resp = requests.get(url, params=param)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_union}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_union}")

                elif method == 'POST':
                    try:
                        resp = requests.post(url, data=param)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_union}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_union}")
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}UNION_BASED PAYLOAD DOESN'T WORKS{Style.RESET_ALL}")

    def execute_error(self, url, method, param, payloads_error, payloads_blind):
        init()
        for payload_error in payloads_error:
            for key in param:
                param[key] = payload_error

                if method == 'GET':
                    try:
                        resp = requests.get(url, params=param)
                        if 'Fuzzingzzing' in resp.text:
                            print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}ERROR PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}\t Fuzzingzzing : YES")
                        else:
                            print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}")

                elif method == 'POST':
                    try:
                        resp = requests.post(url, data=param)
                        if 'Fuzzingzzing' in resp.text:
                            print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}ERROR PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}\t Fuzzingzzing : YES")
                        else:
                            print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}SIMPLE PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}\t STATUS : {resp.status_code}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payloads_error}")

        for payload_blind in payloads_blind:
            for key in param:
                param[key] = payload_blind

                if method == 'GET':
                    try:
                        start_time = time.time()
                        resp = requests.get(url, params=param)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}")

                elif method == 'POST':
                    try:
                        start_time = time.time()
                        resp = requests.post(url, data=param)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}")
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}ERROR_BASED PAYLOAD DOESN'T WORKS{Style.RESET_ALL}")

    def execute_time(self, url, method, param, payloads_time, payloads_blind):
        init()
        for payload_time in payloads_time:
            for key in param:
                param[key] = payload_time
                if method == 'GET':
                    try:
                        start_time = time.time()
                        resp = requests.get(url, params=param, timeout=7)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_time}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_time}")

                elif method == 'POST':
                    try:
                        start_time = time.time()
                        resp = requests.post(url, data=param, timeout=7)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_time}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_time}")

        for payload_blind in payloads_blind:
            for key in param:
                param[key] = payload_blind

                if method == 'GET':
                    try:
                        start_time = time.time()
                        resp = requests.get(url, params=param)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}")

                elif method == 'POST':
                    try:
                        start_time = time.time()
                        resp = requests.post(url, data=param)
                        end_time = int(time.time() - start_time)
                        print(f"{Style.BRIGHT}{Fore.BLUE}SQL INJECTION{Fore.RED}BLIND PAYLOAD{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}\t STATUS : {resp.status_code}\t RESPONSE_TIME : {end_time}")

                    except Exception as e:
                        print(f"{Style.BRIGHT}{Fore.RED}REQUEST ERROR{Style.RESET_ALL}\t method : {method}  URL : {url}\t params : {param}\t PAYLOAD : {payload_blind}")
        else:
            print(f"{Style.BRIGHT}{Fore.BLUE}TIME_BASED PAYLOAD DOESN'T WORKS{Style.RESET_ALL}")

    def execute_sqli(self, url, method, param, payloads_simple, payloads_union, payloads_blind, payloads_error, payloads_time):

        union_check = self.checksqli_union(url, method, param)
        error_check = self.checksqli_error(url, method, param)
        time_check = self.checksqli_time(url, method, param)

        if union_check:
            checked_url, checked_method, checked_param = union_check

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_simple = self.encoding_payloads(payloads_simple)
            self.execute_simple(checked_url, checked_method, checked_param, payloads_simple)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_union = self.encoding_payloads(payloads_union)
            self.execute_union(checked_url, checked_method, checked_param, payloads_union)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {union_check}\t\tmethod : {error_check}\t\tparam : {checked_param}')
            payloads_error = self.encoding_payloads(payloads_error)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_error(checked_url, checked_method, checked_param, payloads_error, payloads_blind)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_time = self.encoding_payloads(payloads_time)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_time(checked_url, checked_method, checked_param, payloads_time, payloads_blind)

        elif error_check:
            checked_url, checked_method, checked_param = error_check

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_simple = self.encoding_payloads(payloads_simple)
            self.execute_simple(checked_url, checked_method, checked_param, payloads_simple)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_union = self.encoding_payloads(payloads_union)
            self.execute_union(checked_url, checked_method, checked_param, payloads_union)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {union_check}\t\tmethod : {error_check}\t\tparam : {checked_param}')
            payloads_error = self.encoding_payloads(payloads_error)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_error(union_check, error_check, checked_param, payloads_error, payloads_blind)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_time = self.encoding_payloads(payloads_time)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_time(checked_url, checked_method, checked_param, payloads_time, payloads_blind)

        elif time_check:
            checked_url, checked_method, checked_param = time_check

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_simple = self.encoding_payloads(payloads_simple)
            self.execute_simple(checked_url, checked_method, checked_param, payloads_simple)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_union = self.encoding_payloads(payloads_union)
            self.execute_union(checked_url, checked_method, checked_param, payloads_union)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {union_check}\t\tmethod : {error_check}\t\tparam : {checked_param}')
            payloads_error = self.encoding_payloads(payloads_error)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_error(union_check, error_check, checked_param, payloads_error, payloads_blind)

            print(f'EXECUTING SQL INJECTION FUZZING...\turl : {checked_url}\t\tmethod : {checked_method}\t\tparam : {checked_param}')
            payloads_time = self.encoding_payloads(payloads_time)
            payloads_blind = self.encoding_payloads(payloads_blind)
            self.execute_time(checked_url, checked_method, checked_param, payloads_time, payloads_blind)