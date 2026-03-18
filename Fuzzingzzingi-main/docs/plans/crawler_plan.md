# 크롤러 고도화 계획 (Crawler Enhancement Plan)

## 개요
현재 Go 언어 기반의 크롤러(`internal/crawler`)는 `colly`를 이용한 정적 수집과 `chromedp`를 이용한 단순 동적 링크 수집 기능을 포함하고 있습니다.
하지만 Python 버전(`crawler/spiders/crawler.py`)에 비해 **쿠키 지원**과 **동적 상호작용(JS Click 등)** 기능이 부족하거나 미구현 상태입니다.
본 계획은 이를 보완하여 "고수준 크롤링"을 달성하고, Fuzzer가 더 많은 공격 표면을 찾을 수 있도록 돕는 것을 목표로 합니다.

## 사용자 리뷰 필요 사항 (User Review Required)
> [!IMPORTANT]
> **쿠키 파일 포맷**: 현재 Python 버전은 `Key=Value` 형태의 텍스트 파일을 가정하고 있습니다. Go 버전도 동일한 포맷을 지원할 예정입니다.
> **성능 영향**: 모든 페이지에 대해 `chromedp` (Headless Chrome)를 실행하여 동적 요소를 탐색할 경우 속도가 느려질 수 있습니다. 이를 완화하기 위해 `colly`로 먼저 수집하고, HTML이 아닌 응답은 건너뛰는 로직을 유지/강화합니다.

## 변경 제안 (Proposed Changes)

### 1. 쿠키 지원 추가 (`internal/crawler/crawler.go`)
- `CookiesFile` 경로가 제공되면 파일을 읽어 파싱합니다.
- 파싱된 쿠키를 `colly.Collector`에 적용합니다 (`c.SetCookies`).
- `chromedp` 실행 시에도 쿠키를 적용하여 인증된 세션에서의 동적 크롤링을 지원합니다.

### 2. 동적 상호작용 강화 (`internal/crawler/crawler.go`)
- 기존 `fetchDynamicLinks` 함수를 개선합니다.
- 단순히 `a[href]`만 수집하는 것이 아니라, `onclick` 속성을 가진 요소를 찾아 클릭 이벤트를 시뮬레이션하거나, 해당 JS 코드를 분석하여 잠재적인 URL을 추출하도록 개선합니다.
- Python 버전의 로직(`document.querySelectorAll('[onclick]')...`)을 참고하여 `chromedp.Evaluate` 스크립트를 보강합니다.

### 3. 로깅 및 예외 처리 개선
- 크롤링 진행 상황과 오류를 더 명확히 알 수 있도록 로그 메시지를 개선합니다.
- `output.txt` 기록 시 중복 제거 로직(이미 `sync.Map`으로 존재하지만)을 재확인합니다.

### 파일 변경 목록
#### [MODIFY] [crawler.go](file:///c:/Users/dntmd/OneDrive/Desktop/Fuzzingzzingi/internal/crawler/crawler.go)
- `loadCookies` 함수 추가
- `Run` 함수 내 쿠키 적용 로직 추가
- `fetchDynamicLinks` 함수 내 JS 실행 로직 보강 (`onclick` 처리 등)
- `chromedp` 실행 옵션에 쿠키 전달 추가

## 검증 계획 (Verification Plan)

### 자동화/단위 테스트 (Automated Tests)
- 현재 별도의 단위 테스트 파일이 없으므로, 기능 구현 후 통합 테스트 스타일로 검증합니다.

### 수동 검증 (Manual Verification)
1. **준비**: 로컬에 테스트용 타깃 서버(예: `DVWA` 또는 간단한 Mock 서버) 또는 포함된 `ui` 서버를 띄웁니다.
2. **쿠키 테스트**:
   - `cookie.txt`에 유효한 세션 쿠키를 저장합니다.
   - 크롤러를 실행하여 로그인해야만 접근 가능한 페이지(예: `/my-profile`)가 `output.txt`에 수집되는지 확인합니다.
3. **동적 링크 테스트**:
   - `onclick="location.href='...'"` 등으로 이동하는 링크가 있는 페이지를 크롤링합니다.
   - 해당 링크가 `output.txt`에 수집되는지 확인합니다.
4. **브라우저 스모크 테스트**:
   - `docs/plans`에 작성될 계획대로 구현 후, 제공된 UI(`http://localhost:5000`)를 통해 전체 플로우(UI 입력 -> Go 서버 -> 크롤러 실행 -> 결과 출력)가 정상 작동하는지 브라우저 도구로 녹화/확인합니다.
