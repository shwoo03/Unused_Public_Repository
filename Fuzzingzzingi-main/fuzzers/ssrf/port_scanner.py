import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urlunparse


class PORTSCANNER:
    def __init__(self):
        with open('payloads/SSRF/port.txt', 'r') as f:
            self.port_num = [port.strip() for port in f]

    def requesting(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                print(f'Port Scanner :\t{url} RESPONSE :\t{resp.status_code}')
            elif resp == 302:
                print(f'Port Scanner :\t{url} may open!!\t{resp.status_code}')
            else:
                print(f'Port Scanner :\t{url} close!!\t{resp.status_code}')

        except Exception as e:
            print(f'Port Scanner :\t{url} \tREQUEST ERROR!!')

    def port_scan(self, url, param):
        url_list = []
        for port in self.port_num:
            parsed_param = urlparse(param)
            domain = parsed_param.netloc
            domain = domain.replace(f':{parsed_param.port}', '') if parsed_param.port else domain

            if domain != "":
                param_domain = domain + f':{port}'
                port_param = parsed_param._replace(netloc=param_domain)
                port_param = urlunparse(port_param)
                port_url = url+port_param
                url_list.append(port_url)
                # 포트 번호 가져와서 파라미터 속 도메인 뒤에 갖다 붙이고 url_list로 반환

        return url_list

    def execute_portscan(self, url, param):
        url_list = self.port_scan(url, param)

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(self.requesting, url_list))

# 포트 스캔 사용법
# 사용자가 의심 가는 url 및 파라미터가 있다면
# 입력하도록