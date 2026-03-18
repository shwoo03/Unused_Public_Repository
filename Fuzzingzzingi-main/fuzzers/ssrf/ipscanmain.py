from fuzzers.ssrf.ip_scanner import IPSCANNER
import validators

def ipscan():

    ipscanner = IPSCANNER()

    url = input('URL : ')
    if not validators.url(url):
        return False
    ip = input('IP : ')
    lower = input('Lower band : ')
    upper = input('Upper band : ')

    ipscanner.execute_ipscan(url, ip, lower, upper)


