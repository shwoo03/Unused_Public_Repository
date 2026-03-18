import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
UI_DIST = ROOT / "ui" / "dist"

app = Flask(__name__, static_folder=str(UI_DIST), static_url_path="/")

CRAWL_THREAD: Optional[threading.Thread] = None
LAST_COMMAND: Optional[str] = None
LAST_ERROR: Optional[str] = None
OUTPUT_FILE = ROOT / "output.txt"
DB_PATH = ROOT / "data" / "crawl.db"


def build_crawl_command(start_url: str, proxy_url: str, depth: int, cookies_file: Optional[str]):
    args = [
        "scrapy",
        "runspider",
        "crawler/spiders/crawler.py",
        "-a",
        f"start_url={start_url}",
        "-a",
        f"proxy_url={proxy_url}",
        "-a",
        f"max_depth={depth}",
        "-s",
        "LOG_LEVEL=INFO",
    ]
    if cookies_file:
        args.extend(["-a", f"cookies_file={cookies_file}"])
    return args


def run_crawl(start_url: str, proxy_url: str, depth: int, cookies_file: Optional[str]):
    global LAST_COMMAND, LAST_ERROR
    cmd = build_crawl_command(start_url, proxy_url, depth, cookies_file)
    LAST_COMMAND = " ".join(cmd)
    LAST_ERROR = None
    OUTPUT_FILE.write_text("", encoding="utf-8")
    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True, cwd=ROOT)
        if result.returncode != 0:
            LAST_ERROR = result.stderr.strip() or f"크롤러 오류 (코드 {result.returncode})"
    except Exception as exc:  # pylint: disable=broad-except
        LAST_ERROR = f"크롤 실행 실패: {exc}"


def start_crawl_thread(start_url: str, proxy_url: str, depth: int, cookies_file: Optional[str]):
    global CRAWL_THREAD
    if CRAWL_THREAD and CRAWL_THREAD.is_alive():
        return False
    CRAWL_THREAD = threading.Thread(
        target=run_crawl,
        args=(start_url, proxy_url, depth, cookies_file),
        daemon=True,
    )
    CRAWL_THREAD.start()
    return True


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    data = request.get_json(force=True)
    start_url = (data.get("startUrl") or "").strip()
    proxy_url = (data.get("proxyUrl") or "none").strip()
    depth = int(data.get("depth") or 3)
    cookies_file = (data.get("cookiesFile") or "").strip() or None

    if not start_url:
        return jsonify({"ok": False, "error": "startUrl이 필요합니다."}), 400

    started = start_crawl_thread(start_url, proxy_url, depth, cookies_file)
    if not started:
        return jsonify({"ok": False, "error": "이미 크롤러가 실행 중입니다."}), 409

    return jsonify({"ok": True, "message": "크롤링을 시작했습니다.", "command": LAST_COMMAND})


@app.route("/api/status", methods=["GET"])
def api_status():
    running = CRAWL_THREAD.is_alive() if CRAWL_THREAD else False
    return jsonify(
        {
            "running": running,
            "last_command": LAST_COMMAND,
            "last_error": LAST_ERROR,
            "output_file": str(OUTPUT_FILE),
            "db_path": str(DB_PATH),
        }
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_ui(path):
    if UI_DIST.exists():
        if path and (UI_DIST / path).exists():
            return send_from_directory(UI_DIST, path)
        return send_from_directory(UI_DIST, "index.html")
    return jsonify({"message": "UI가 아직 빌드되지 않았습니다. `cd ui && npm run build` 후 다시 시도하세요."}), 503


def main():
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
