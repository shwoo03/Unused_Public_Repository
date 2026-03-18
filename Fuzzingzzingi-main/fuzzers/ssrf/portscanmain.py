from fuzzers.ssrf.port_scanner import PORTSCANNER
import time

# url = 'https://notelass.site/introduce/'
# http://127.0.0.1:8080
def portscan():
    portscanner = PORTSCANNER()

    print('\n\n')
    print('PORT SCANNER')
    print('\n\n')
    time.sleep(1)
    print('INPUT EXAMPLE -> https://naver.com/')
    url = input('PLEASE INPUT URL : ')

    print('INPUT EXAMPLE -> http://127.0.0.1:8080')
    parameter = input('PLEASE INPUT PARAMETER : ')
    print('\n\n')

    portscanner.execute_portscan(url, parameter)
