from fuzzers.ssrf.SSRF import SSRF
from fuzzers.ssrf.local import LOCAL
from fuzzers.ssrf.portscanmain import portscan
from fuzzers.ssrf.ipscanmain import ipscan

def ssrf():
    ssrf = SSRF()
    local_server = LOCAL()

    # LOCAL 서버 스레드 시작

    url_list = ssrf.get_url()
    # 여기서 url을 리스트로 받아오고
    basic_payloads, white_payloads = ssrf.get_payloads()

    # 여기서 각 페이로드를 리스트로 받아와서

    for i in url_list:
        params = ssrf.get_params(i)
        # 여기서 url에 맞는 메소드, 파라미터 가져와서
        for param in params:
            ssrf.execute_ssrf(i, param[0], param[1], basic_payloads, white_payloads)
        # 여기서 ssrf 퍼저 동작

    # param[0]은 method, param[1]은 parameter 입니다~

    ssrf.close_file()
    ssrf.cursor.close()
    ssrf.connection.close()

    local_server.shutdown()

def ssrf_get_option():
    print('SSRF\n1.\tSSRF\n2.\tPORT SCANNING\n3.\tIP SCANNING')
    ssrf_option = input('OPTION : ')
    if ssrf_option == '1':
        ssrf()
    elif ssrf_option == '2':
        portscan()
    elif ssrf_option == '3':
        ipscan()
    else:
        print(f'NO OPTION {ssrf_option}')
