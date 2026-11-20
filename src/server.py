"""HTTP interface for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from src.shortener import Shortener


def _page(content: str, message: str = "") -> str:
    escaped_message = f"<p class=\"error\">{escape(message)}</p>" if message else ""
    return (
        "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
        "<title>URL 단축기</title>"
        "<style>"
        "body{font-family:sans-serif;max-width:70rem;margin:2rem auto;padding:0 1rem}"
        ".chain{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem}"
        ".chain-node{border:1px solid #888;border-radius:.4rem;padding:.75rem}"
        ".chain-arrow{font-size:1.5rem}"
        "code{overflow-wrap:anywhere}"
        "</style><body>"
        "<h1>URL 단축기</h1>"
        f"{escaped_message}{content}"
        '<p><a href="/table">해시 테이블 보기</a></p>'
        "</body></html>"
    )


def _hash_explanation(key: str, capacity: int) -> str:
    value = 0
    steps = ["h0 = 0"]
    for index, character in enumerate(key, start=1):
        previous = value
        value = (value * 31 + ord(character)) % capacity
        steps.append(
            f"h{index} = ({previous} × 31 + ord({character!r})) mod {capacity} = {value}"
        )
    return (
        f"h(key) = h{len(key)}; "
        + "; ".join(steps)
        + f"; bucket = {value}"
    )


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    shortener: Shortener | None = None,
    strategy: str = "linear",
    storage_path: str | Path | None = None,
) -> ThreadingHTTPServer:
    active_shortener = (
        shortener
        if shortener is not None
        else Shortener(strategy, storage_path=storage_path)
    )

    class ShortenerHandler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _table_page(self) -> str:
            table = active_shortener.tables[0]
            bucket_name = "슬롯" if table.strategy_name == "선형 탐지" else "버킷"
            sections = [
                "<p>버킷의 연결 리스트 노드를 화살표로 잇고, 각 노드의 해시 과정을 "
                "펼쳐 볼 수 있습니다.</p>"
                f"<h2>URL → 짧은 코드 ({escape(table.strategy_name)})</h2>"
                f"<p>용량: {table.capacity}, 항목 수: {len(table)}, "
                f"적재율: {table.load_factor:.3f}</p>"
            ]
            for bucket_index, bucket in enumerate(table.slots()):
                sections.append(
                    f'<section class="bucket"><h3>{bucket_name} {bucket_index}</h3>'
                )
                if not bucket:
                    sections.append("<p>(비어 있음)</p></section>")
                    continue

                sections.append('<div class="chain">')
                for position, (url, code) in enumerate(bucket):
                    if position:
                        sections.append(
                            '<span class="chain-arrow" aria-label="다음 노드">→</span>'
                        )
                    escaped_url = escape(url)
                    escaped_code = escape(code)
                    escaped_href = escape(f"/r/{code}", quote=True)
                    hash_steps = escape(_hash_explanation(url, table.capacity))
                    if table.strategy_name == "선형 탐지":
                        visited = " → ".join(
                            str(slot) for slot in table.probe_path(url)
                        )
                        search_detail = f"<p>방문 슬롯: {visited}</p>"
                    else:
                        search_detail = (
                            f"<p>연결 리스트 노드: {position + 1}</p>"
                        )
                    sections.append(
                        '<article class="chain-node">'
                        f"<p>URL 키: <code>{escaped_url}</code></p>"
                        f"<p>짧은 코드: <code>{escaped_code}</code></p>"
                        f'<p>짧은 링크: <a href="{escaped_href}">'
                        f"{escaped_href}</a></p>"
                        f"{search_detail}"
                        "<details>"
                        "<summary>호너 해시 계산 과정</summary>"
                        f"<p><code>{hash_steps}</code></p>"
                        "</details>"
                        "</article>"
                    )
                sections.append("</div></section>")
            return _page("".join(sections))

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send_html(
                    200,
                    _page(
                        '<form action="/shorten" method="post">'
                        '<label>원본 URL <input type="url" name="url" required></label>'
                        '<button type="submit">짧게 만들기</button></form>'
                    ),
                )
                return
            if path == "/table":
                self._send_html(200, self._table_page())
                return
            if path.startswith("/r/"):
                code = unquote(path[len("/r/") :])
                try:
                    url = active_shortener.expand(code)
                except KeyError:
                    self._send_html(404, _page("", "존재하지 않는 단축 코드입니다."))
                    return
                self.send_response(302)
                self.send_header("Location", url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._send_html(404, _page("", "페이지를 찾을 수 없습니다."))

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/shorten":
                self._send_html(404, _page("", "페이지를 찾을 수 없습니다."))
                return
            try:
                body_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_html(400, _page("", "요청 본문 길이가 잘못되었습니다."))
                return
            if body_length < 0:
                self._send_html(400, _page("", "요청 본문 길이가 잘못되었습니다."))
                return
            if body_length > 1_048_576:
                self._send_html(413, _page("", "요청 본문이 너무 큽니다."))
                return
            try:
                form = self.rfile.read(body_length).decode("utf-8")
            except UnicodeDecodeError:
                self._send_html(400, _page("", "요청은 UTF-8이어야 합니다."))
                return
            url = parse_qs(form, keep_blank_values=True).get("url", [""])[0]
            try:
                code = active_shortener.shorten(url)
            except ValueError as error:
                self._send_html(400, _page("", str(error)))
                return
            except OSError:
                self._send_html(500, _page("", "단축 URL을 저장하지 못했습니다."))
                return

            result = (
                f"<p>짧은 코드: <code>{escape(code)}</code></p>"
                f'<p><a href="/r/{escape(code)}">단축 링크 열기</a></p>'
                f"<p>원본: <code>{escape(url.strip())}</code></p>"
                '<p><a href="/">다른 URL 입력</a></p>'
            )
            self._send_html(200, _page(result))

    return ThreadingHTTPServer((host, port), ShortenerHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--strategy", choices=("chaining", "linear"), default="linear")
    parser.add_argument("--data-file", type=Path, default=Path("data/urls.csv"))
    arguments = parser.parse_args()
    server = create_server(
        port=arguments.port,
        strategy=arguments.strategy,
        storage_path=arguments.data_file,
    )
    print(f"Serving on http://0.0.0.0:{arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
