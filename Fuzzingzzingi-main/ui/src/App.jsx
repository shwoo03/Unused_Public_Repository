import { useEffect, useMemo, useState } from 'react'
import './App.css'

const defaultUrl = 'http://localhost:30102'

function App() {
  const [form, setForm] = useState({
    startUrl: defaultUrl,
    proxyUrl: '',
    depth: 3,
    cookiesFile: '',
  })
  const [status, setStatus] = useState({
    running: false,
    last_command: null,
    last_error: null,
    output_file: null,
    db_path: null,
  })
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState(null)

  const pollingInterval = useMemo(() => (status.running ? 2000 : 6000), [status.running])

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status')
      if (!res.ok) return
      const data = await res.json()
      setStatus(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchStatus()
    const id = setInterval(fetchStatus, pollingInterval)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollingInterval])

  const handleChange = (field) => (e) => {
    const value = field === 'depth' ? Number(e.target.value) : e.target.value
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setMessage(null)
    try {
      const res = await fetch('/api/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          startUrl: form.startUrl,
          proxyUrl: form.proxyUrl || 'none',
          depth: form.depth,
          cookiesFile: form.cookiesFile,
        }),
      })
      const data = await res.json()
      if (!res.ok || !data.ok) {
        throw new Error(data.error || '크롤 시작에 실패했습니다.')
      }
      setMessage('크롤을 시작했습니다. 상태가 곧 갱신됩니다.')
      fetchStatus()
    } catch (err) {
      setMessage(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <div className="hero">
        <div>
          <p className="eyebrow">WHS2기 웹 퍼저</p>
          <h1>스마트 크롤 & 퍼징 컨트롤 패널</h1>
          <p className="lede">
            Playwright + Scrapy 기반 크롤러를 한 번에 제어하고, 도메인 스코프를 벗어나지 않도록 자동 보호합니다.
            프록시와 쿠키는 선택 사항이며, 기본 DB는 로컬 SQLite입니다.
          </p>
        </div>
        <div className="badge">{status.running ? '실행 중' : '대기 중'}</div>
      </div>

      <div className="grid">
        <div className="card">
          <h2>크롤 파라미터</h2>
          <form onSubmit={handleSubmit} className="form">
            <label>
              시작 URL
              <input
                required
                type="url"
                value={form.startUrl}
                onChange={handleChange('startUrl')}
                placeholder="http://localhost:30102"
              />
            </label>
            <label>
              프록시 (없으면 비워두세요)
              <input
                type="text"
                value={form.proxyUrl}
                onChange={handleChange('proxyUrl')}
                placeholder="http://127.0.0.1:8080"
              />
            </label>
            <label>
              최대 크롤 깊이
              <input
                type="number"
                min={1}
                max={6}
                value={form.depth}
                onChange={handleChange('depth')}
              />
            </label>
            <label>
              쿠키 파일 (선택)
              <input
                type="text"
                value={form.cookiesFile}
                onChange={handleChange('cookiesFile')}
                placeholder="cookie_header.txt"
              />
            </label>
            <button type="submit" disabled={submitting || status.running}>
              {submitting ? '시작 중...' : status.running ? '실행 중' : '크롤 시작'}
            </button>
            {message && <p className="message">{message}</p>}
          </form>
        </div>

        <div className="card status">
          <h2>실시간 상태</h2>
          <ul>
            <li>
              <span>실행 상태</span>
              <strong className={status.running ? 'pill running' : 'pill idle'}>
                {status.running ? '실행 중' : '대기'}
              </strong>
            </li>
            <li>
              <span>마지막 명령</span>
              <code>{status.last_command || '-'}</code>
            </li>
            <li>
              <span>마지막 오류</span>
              <code className="error-text">{status.last_error || '-'}</code>
            </li>
            <li>
              <span>output.txt</span>
              <code>{status.output_file || '-'}</code>
            </li>
            <li>
              <span>DB (SQLite)</span>
              <code>{status.db_path || '-'}</code>
            </li>
          </ul>
          <p className="note">도메인 범위는 registered_domain 기준으로 자동 제한됩니다.</p>
        </div>
      </div>
    </div>
  )
}

export default App
