import pymysql
import json
import hashlib
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    UnexpectedAlertPresentException, NoAlertPresentException,
    InvalidElementStateException, ElementNotInteractableException, TimeoutException, NoSuchElementException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures

def xss():
    # 데이터베이스 연결 설정
    db = pymysql.connect(
        host="13.209.63.65",
        database="Fuzzingzzingi",
        user="zzingzzingi",
        password="!Ru7eP@ssw0rD!12"
    )

    cursor = db.cursor()

    # 요청 데이터를 가져오는 SQL 쿼리
    query = "SELECT id, url, parameters FROM requests"
    cursor.execute(query)

    db_requests = cursor.fetchall()

    # 페이로드 파일에서 페이로드 리스트 불러오기
    base_path = os.path.dirname(os.path.abspath(__file__))
    payloads_path = os.path.join(base_path, "../../payloads/XSS/xss_payloads.txt")
    with open(payloads_path, 'r', encoding='utf-8') as file:
        payloads = [line.strip() for line in file.readlines()]

    # 취약점 정보를 저장할 리스트
    vulnerabilities = []

    def fuzz_request(url, params):
        param_keys = list(params.keys())

        # 각 파라미터에 독립적으로 페이로드 삽입
        for key in param_keys:
            for payload in payloads:
                hash_value = hashlib.md5(payload.encode()).hexdigest()
                fuzzed_params = params.copy()
                fuzzed_params[key] = payload + hash_value
                send_request(url, fuzzed_params, key, payload, hash_value)

        # 모든 파라미터에 동일한 페이로드를 동시에 삽입
        for payload in payloads:
            fuzzed_params = params.copy()
            hash_value = hashlib.md5(payload.encode()).hexdigest()
            for key in param_keys:
                fuzzed_params[key] = payload + hash_value
            send_request(url, fuzzed_params, ",".join(param_keys), payload, hash_value)

    def send_request(url, params, key, payload, hash_value):
        # Selenium 설정
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')  # SSL 인증서 오류 무시
        options.add_argument('--allow-running-insecure-content')
        # options.add_argument('--headless')

        # chromedriver 경로 설정
        chromedriver_path = os.path.join(base_path, "../../crawler/spiders/chromedriver")
        driver_service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=driver_service, options=options)

        try:
            # 페이지 로드
            driver.get(url)

            # 페이지가 완전히 로드될 때까지 기다림
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # 파라미터 입력
            for param_key, param_value in params.items():
                try:
                    input_element = driver.find_element(By.NAME, param_key)
                    if input_element.is_enabled() and input_element.is_displayed():
                        input_element.clear()
                        input_element.send_keys(param_value)
                    else:
                        print(f"Input element {param_key} is not interactable.")
                except (NoSuchElementException, InvalidElementStateException, ElementNotInteractableException, TimeoutException) as e:
                    print(f"Error with input element {param_key}: {e}")
                    continue

            # 버튼 클릭 시도
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if button.is_enabled() and button.is_displayed():
                        button.click()
                        break
                except Exception as e:
                    print(f"Error clicking button: {e}")
                    continue

            inputs = driver.find_elements(By.TAG_NAME, "input")
            for input_element in inputs:
                if input_element.get_attribute("type") in ["submit", "button"]:
                    try:
                        if input_element.is_enabled() and input_element.is_displayed():
                            input_element.click()
                            break
                    except Exception as e:
                        print(f"Error clicking input: {e}")
                        continue

            # 응답 분석
            page_source = driver.page_source
            if hash_value in page_source:
                log_vulnerability(url, key, payload, hash_value, page_source)
            else:
                print(f"Hash value not found in the page source for URL: {url} with payload: {payload}")

        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                if hash_value in alert_text:
                    log_vulnerability(url, key, payload, hash_value, alert_text)
                else:
                    print(f"Hash value not found in the alert text for URL: {url} with payload: {payload}")
            except NoAlertPresentException:
                pass
        except Exception as e:
            print(f"Unexpected error: {e}")

        finally:
            driver.quit()

    def log_vulnerability(url, parameter, payload, hash_value, response):
        response_snippet_length = 1000  # 스니펫 길이를 1000자로 설정
        start_index = response.find(payload)
        end_index = start_index + len(payload) if start_index != -1 else response_snippet_length

        response_snippet = response[start_index:end_index].strip()
        if not response_snippet:
            response_snippet = "[Payload not reflected in response]"

        vulnerability_info = {
            "url": url,
            "parameter": parameter,
            "payload": payload,
            "hash_value": hash_value,
            "response_snippet": response_snippet
        }

        # 취약점 리스트에 추가
        vulnerabilities.append(vulnerability_info)

        # 터미널에 취약한 URL과 파라미터 출력
        print(f"Vulnerable URL: {url} | Parameter: {parameter}")

    # 병렬 퍼징 실행
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for db_request in db_requests:
            request_id, url, params = db_request
            params = json.loads(params.replace('FUZZ', ''))  # 'FUZZ'를 빈 문자열로 대체

            if params:  # 파라미터가 있는 경우에만 테스트 수행
                futures.append(executor.submit(fuzz_request, url, params))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")

    db.close()

    # 취약점 정보를 URL 순서대로 정렬하여 JSON 파일로 저장
    filtered_vulnerabilities = [vuln for vuln in vulnerabilities if
                                vuln["response_snippet"] != "[Payload not reflected in response]"]

    filtered_vulnerabilities.sort(key=lambda x: x["url"])
    with open('vulnerabilities.json', 'w', encoding='utf-8') as json_file:
        json.dump(filtered_vulnerabilities, json_file, indent=4)