from fuzzers.sql_injection.Sql_Injection import SqlInjection


def sql():
    SQLI = SqlInjection()
    url_list = SQLI.get_url()
    payloads_simple, payloads_union, payloads_error, payloads_blind, payloads_time = SQLI.get_payloads()

    for i in url_list:
        params = SQLI.get_params(i)
        for param in params:
            SQLI.execute_sqli(i, param[0], param[1],
                                   payloads_simple, payloads_union, payloads_blind, payloads_error, payloads_time)
# param[0]은 method, param[1]은 parameter 입니다~
    SQLI.cursor.close()
    SQLI.connection.close()

def sql_encoding():
    SQLI = SqlInjection()
    url_list = SQLI.get_url()
    payloads_simple, payloads_union, payloads_error, payloads_blind, payloads_time = SQLI.get_payloads()

    payloads_simple = SQLI.encoding_payloads(payloads_simple)
    payloads_union = SQLI.encoding_payloads(payloads_union)
    payloads_error = SQLI.encoding_payloads(payloads_error)
    payloads_blind = SQLI.encoding_payloads(payloads_blind)
    payloads_time = SQLI.encoding_payloads(payloads_time)

    for i in url_list:
        params = SQLI.get_params(i)
        for param in params:
            SQLI.execute_sqli(i, param[0], param[1],
                                   payloads_simple, payloads_union, payloads_blind, payloads_error, payloads_time)
    # param[0]은 method, param[1]은 parameter 입니다~
    SQLI.cursor.close()
    SQLI.connection.close()
    # param_list[0] = method , param_list[1] = parameters

def sqli_get_option():
    print('SQL INJECTION\n1.\tBASIC\n2.WITH ENCODING')
    sqli_option = input('OPTION : ')
    if sqli_option == '1':
        sql()
    elif sqli_option == '2':
        sql_encoding()
    else:
        print(f'NO OPTION {sqli_option}')
