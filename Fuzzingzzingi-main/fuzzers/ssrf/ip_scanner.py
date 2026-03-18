import requests
from concurrent.futures import ThreadPoolExecutor
import re
import validators
# 포트 80,

class IPSCANNER:
    def __init__(self):
        self.ip_band_a = re.compile(r'10\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)')
        self.ip_band_b = re.compile(r'172\.(?:1[6-9]|2[0-9]|3[0-1])\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)')
        self.ip_band_c = re.compile(r'192\.168\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)\.(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5]|x)')

    def requesting(self, url):
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                print(f'IP Scanner :\t{url} RESPONSE :\t{resp.status_code}')
        except Exception as e:
            if "Connection refused" in str(e):
                print(f'IP Scanner :\t{url} \trefused the connection')
            elif "Timeout" in str(e):
                print(f'IP Scanner :\t{url} \tresponse timeout')
            else:
                print(f'IP Scanner :\t{url} \tREQUEST ERROR!!')

    def customizing(self, url, ip, lower, upper):
        # lower ~ upper까지의 ip 숫자를 x 부분에 붙여 넣고 scan_list로 반환
        scan_list = []
        if self.error_handler(ip, lower, upper):
            for num in range(int(lower), int(upper)+1, 1):
                target_num = str(num)
                target_ip = ip.replace('x', target_num)
                target_url = url + target_ip
                print(target_url)
                scan_list.append(target_url)
        print(scan_list)
        return scan_list

    def error_handler(self, ip, lower, upper):
        ip_sp = ip.split()
        if ip_sp.count('x') > 1:
            print(f"DDoS ATTACK MAY OCCUR. PLEASE USE ONE x")
            return False
        # x를 하나만 두게 해서 너무 많은 요청 보내지 못하도록

        if not self.ip_band_a.match(ip) and not self.ip_band_b.match(ip) and not self.ip_band_c.match(ip):
            print(f"IP Error\t\t Internal IP : 10.0.0.0 ~ 10.255.255.255\t172.16.0.0 ~ 172.31.255.255\t192.168.0.0 ~ 192.168.255.255")
            return False
        # 내부 ip 대역과 매치하는가?

        if int(lower) < 0:
            print(f"IP lower bound Error\t\t Should be 0 ~ 255")
            return False

        if int(upper) > 255:
            print(f"IP upper bound Error\t\t Should be 0 ~ 255")
            return False
        # ip 경계값 확인

        return True

    def execute_ipscan(self, url, ip, lower, upper):
        scan_list = self.customizing(url, ip, lower, upper)
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(self.requesting, scan_list))
        # 멀티스레딩 이용