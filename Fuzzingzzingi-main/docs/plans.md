# Go 기반 스마트 퍼저 전환 계획

## 목표
- 백엔드를 Go로 전환해 단일 바이너리 실행을 지향하고, 크롤·프록시·API를 통합한다.
- 크롤러는 도메인 스코프/정규화/중복 필터를 유지하며 `output.txt`에 기록한다.
- UI는 기존 React(Vite) 결과를 Go 서버가 정적 서빙하고, API(`/api/crawl`, `/api/status`)로 연동한다.
- 브라우저 테스트(크롤 타겟 기동 시)와 프론트 빌드 테스트를 수행해 정상 동작을 검증한다.

## 진행 상황
- [x] Go 전환 설계 및 API/크롤러 구조 정의.
- [x] Go 서버/크롤러 구현, go.mod 작성.
- [x] README 및 의존성/실행 가이드 최신화.
- [ ] 테스트: `npm run build`, `go test ./...` 또는 `go run cmd/server/main.go` 후 브라우저 스모크 (`http://localhost:30102` 기동 필요). 현재 5000 포트 점유 및 대상 미기동으로 스모크 미수행.

## 구현 방향
1) **Go 서버**: `cmd/server/main.go`에서 Gin 기반 API 제공(`/api/crawl`, `/api/status`) + `ui/dist` 정적 서빙.
2) **크롤러**: `internal/crawler`에서 colly 기반 링크 수집, registered_domain 스코프, URL 정규화·중복 필터, `output.txt` 기록. 프록시는 옵션.
3) **상태 관리**: 실행 중 여부/마지막 명령/에러를 메모리 상태로 보관, API에서 조회.
4) **테스트**: UI 빌드(`npm run build`), Go 빌드/테스트, 브라우저 스모크(타겟 서버 필요). 타겟 미기동 시 에러 로그로 기록.

## 테스트 계획
- 프론트: `cd ui && npm run build`.
- 백엔드: `go run cmd/server/main.go` 또는 `go test ./...` (Go 설치 필요).
- 크롤 스모크: 타겟 서비스(`http://localhost:30102`) 기동 후 `/api/crawl` 호출, `output.txt` 확인. 타겟 미기동 시 연결 거부를 에러로 보고.
