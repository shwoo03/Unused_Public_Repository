package crawler

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/chromedp/cdproto/network"
	"github.com/chromedp/chromedp"
	"github.com/gocolly/colly/v2"
)

// Request는 크롤 시작 시 전달되는 파라미터 집합입니다.
type Request struct {
	StartURL    string `json:"startUrl"`
	ProxyURL    string `json:"proxyUrl"`
	MaxDepth    int    `json:"depth"`
	CookiesFile string `json:"cookiesFile"`
}

// String은 상태 표시용 명령 문자열을 생성합니다.
func (r Request) String() string {
	return fmt.Sprintf("start_url=%s proxy_url=%s max_depth=%d cookies_file=%s", r.StartURL, r.ProxyURL, r.MaxDepth, r.CookiesFile)
}

// Run은 colly 기반 크롤을 수행하고 결과를 output.txt에 기록합니다.
func Run(req Request) error {
	if req.MaxDepth <= 0 {
		req.MaxDepth = 3
	}

	outputPath := filepath.Join(".", "output.txt")
	if err := os.WriteFile(outputPath, []byte{}, 0644); err != nil {
		return fmt.Errorf("output 파일 생성 실패: %w", err)
	}

	u, err := url.Parse(req.StartURL)
	if err != nil {
		return fmt.Errorf("URL 파싱 실패: %w", err)
	}
	baseHost := u.Hostname() // ex) localhost
	hostWithPort := u.Host   // ex) localhost:30102
	if baseHost == "" {
		return errors.New("호스트를 판별할 수 없습니다")
	}

	// 쿠키 로드
	var cookies []*http.Cookie
	if req.CookiesFile != "" {
		cs, err := loadCookies(req.CookiesFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "쿠키 로드 경고: %v\n", err)
		} else {
			cookies = cs
		}
	}

	c := colly.NewCollector(
		colly.AllowedDomains(baseHost, hostWithPort),
		colly.MaxDepth(req.MaxDepth),
		colly.Async(true),
	)
	c.SetRequestTimeout(30 * time.Second)
	c.UserAgent = "Fuzzingzzingi-GoCrawler/0.1"

	if req.ProxyURL != "" && strings.ToLower(req.ProxyURL) != "none" {
		if err := c.SetProxy(req.ProxyURL); err != nil {
			return fmt.Errorf("프록시 설정 실패: %w", err)
		}
	}

	// Colly에 쿠키 설정
	if len(cookies) > 0 {
		if err := c.SetCookies(req.StartURL, cookies); err != nil {
			fmt.Fprintf(os.Stderr, "Colly 쿠키 설정 실패: %v\n", err)
		}
	}

	seen := sync.Map{}
	mu := &sync.Mutex{}

	writeURL := func(u string) {
		mu.Lock()
		defer mu.Unlock()
		f, err := os.OpenFile(outputPath, os.O_APPEND|os.O_WRONLY, 0644)
		if err != nil {
			return
		}
		defer f.Close()
		_, _ = f.WriteString(u + "\n")
	}

	c.OnRequest(func(r *colly.Request) {
		// OnRequest에서는 중복 체크를 하지 않습니다.
		// OnResponse/OnHTML에서 Visit 호출 전 미리 seen에 등록하기 때문입니다.
		// 만약 리다이렉트로 인한 중복이 발생하면 수집되겠지만, 큰 문제는 아닙니다.
	})

	c.OnResponse(func(r *colly.Response) {
		norm := normalize(r.Request.URL.String())
		writeURL(norm)

		// 동적 렌더링으로 추가 링크 수집 시도 (비 HTML은 건너뜀)
		ct := strings.ToLower(string(r.Headers.Get("Content-Type")))
		if !strings.Contains(ct, "text/html") && !strings.Contains(ct, "application/xhtml") {
			return
		}
		// 쿠키 전달하여 동적 로드
		links, err := fetchDynamicLinks(norm, req.ProxyURL, cookies)
		if err != nil {
			fmt.Fprintf(os.Stderr, "렌더링 링크 수집 실패 %s: %v\n", norm, err)
			return
		}
		for _, l := range links {
			n := normalize(l)
			host := hostOf(n)

			if host != baseHost && host != hostWithPort {
				continue
			}
			if _, loaded := seen.LoadOrStore(n, true); loaded {
				continue
			}
			_ = r.Request.Visit(n)
		}
	})

	c.OnHTML("a[href]", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		abs := e.Request.AbsoluteURL(link)
		norm := normalize(abs)
		host := hostOf(norm)
		if host != baseHost && host != hostWithPort {
			return
		}
		if _, loaded := seen.LoadOrStore(norm, true); loaded {
			return
		}
		_ = e.Request.Visit(norm)
	})

	c.OnError(func(r *colly.Response, err error) {
		fmt.Fprintf(os.Stderr, "크롤 오류 %s: %v\n", r.Request.URL, err)
	})

	if err := c.Visit(req.StartURL); err != nil {
		return fmt.Errorf("초기 방문 실패: %w", err)
	}
	c.Wait()
	return nil
}

func normalize(raw string) string {
	u, err := url.Parse(raw)
	if err != nil {
		return raw
	}
	q := u.Query()
	for _, k := range []string{"random", "session", "timestamp"} {
		q.Del(k)
	}
	u.RawQuery = q.Encode()
	u.Fragment = ""
	return u.String()
}

func hostOf(raw string) string {
	u, err := url.Parse(raw)
	if err != nil {
		return ""
	}
	return u.Hostname()
}

// loadCookies reads cookies from a KEY=VALUE formatted file
func loadCookies(path string) ([]*http.Cookie, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var cookies []*http.Cookie
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			cookies = append(cookies, &http.Cookie{
				Name:  strings.TrimSpace(parts[0]),
				Value: strings.TrimSpace(parts[1]),
			})
		}
	}
	return cookies, scanner.Err()
}

// fetchDynamicLinks는 headless Chromium으로 렌더링해 onclick 등 JS로 만들어진 링크를 추출한다.
func fetchDynamicLinks(targetURL, proxy string, cookies []*http.Cookie) ([]string, error) {
	opts := append(chromedp.DefaultExecAllocatorOptions[:],
		chromedp.Flag("headless", true),
		chromedp.Flag("disable-gpu", true),
		chromedp.Flag("disable-extensions", true),
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.Flag("no-sandbox", true),
	)
	if proxy != "" && strings.ToLower(proxy) != "none" {
		opts = append(opts, chromedp.ProxyServer(proxy))
	}

	allocCtx, cancelAlloc := chromedp.NewExecAllocator(context.Background(), opts...)
	defer cancelAlloc()

	ctx, cancelCtx := chromedp.NewContext(allocCtx)
	defer cancelCtx()

	timeoutCtx, cancelTimeout := context.WithTimeout(ctx, 40*time.Second) // 타임아웃 약간 증가
	defer cancelTimeout()

	// 쿠키 설정 액션 준비
	var tasks chromedp.Tasks
	if len(cookies) > 0 {
		tasks = append(tasks, chromedp.ActionFunc(func(ctx context.Context) error {
			for _, c := range cookies {
				// 도메인은 targetURL 기반으로 설정하거나, 빈 값으로 두면 현재 도메인 적용
				if err := network.SetCookie(c.Name, c.Value).
					WithURL(targetURL).
					Do(ctx); err != nil {
					return err
				}
			}
			return nil
		}))
	}

	var links []string
	tasks = append(tasks,
		chromedp.Navigate(targetURL),
		chromedp.WaitReady("body", chromedp.ByQuery),
		chromedp.Sleep(2000*time.Millisecond), // JS 실행 대기

		chromedp.Evaluate(`
			(function() {
				const uniqueLinks = new Set();
				
				// 1. a[href], area[href]
				document.querySelectorAll('a[href], area[href]').forEach(el => uniqueLinks.add(el.href));
				
				// 2. form[action]
				document.querySelectorAll('form[action]').forEach(el => uniqueLinks.add(el.action));
				
				// 3. iframe[src], frame[src]
				document.querySelectorAll('iframe[src], frame[src]').forEach(el => uniqueLinks.add(el.src));

				// 4. Onclick analysis (location.href / window.location)
				document.querySelectorAll('[onclick]').forEach(el => {
					const code = el.getAttribute('onclick');
					if (code && !code.includes('logout')) {
						const match = code.match(/(?:location\.href|window\.location)\s*=\s*['"]([^'"]+)['"]/);
						if (match && match[1]) {
							const a = document.createElement('a');
							a.href = match[1];
							uniqueLinks.add(a.href);
						}
					}
				});
				return Array.from(uniqueLinks);
			})()
		`, &links),
	)

	if err := chromedp.Run(timeoutCtx, tasks); err != nil {
		return nil, err
	}

	fmt.Fprintf(os.Stderr, "[Debug] Found %d links on %s\n", len(links), targetURL)
	return links, nil
}
