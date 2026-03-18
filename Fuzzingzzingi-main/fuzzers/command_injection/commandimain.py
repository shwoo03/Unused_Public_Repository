from fuzzers.command_injection.Command_Injection import CommandInjection


def command_injection():
    CI = CommandInjection()
    url_list = CI.get_url()
    payloads = CI.get_payloads()

    CI.generate_payloads(5)
    CI.generate_payloads(10)

    for url in url_list:
        params = CI.get_params(url)
        for param in params:
            CI.execute_commandi(url, param[0], param[1], payloads)
    # param[0]은 method, param[1]은 parameter 입니다~

    CI.file_close()
    CI.cursor.close()
    CI.connection.close()
