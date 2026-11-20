"""HTTP interface for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from src.shortener import Shortener


def _page(content: str, message: str = "") -> str:
    escaped_message = f"<p class=\"error\">{escape(message)}</p>" if message else ""
    return (
        "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
        "<title>URL 단축기</title><body>"
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
    strategy: str = "chaining",
) -> ThreadingHTTPServer:
    active_shortener = shortener if shortener is not None else Shortener(strategy)

    class ShortenerHandler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _table_page(self) -> str:
            sections = []
            for table_number, table in enumerate(active_shortener.tables, start=1):
                bucket_name = "슬롯" if table.strategy_name == "선형 탐지" else "버킷"
                rows = [
                    f"<h2>테이블 {table_number} ({escape(table.strategy_name)})</h2>"
                    f"<p>용량: {table.capacity}, 항목 수: {len(table)}, "
                    f"적재율: {table.load_factor:.3f}</p>"
                ]
                for bucket_index, bucket in enumerate(table.slots()):
                    rows.append(f"<h3>{bucket_name} {bucket_index}</h3>")
                    if not bucket:
                        rows.append("<p>(비어 있음)</p>")
                        continue
                    rows.append("<ol>")
                    for position, (key, value) in enumerate(bucket, start=1):
                        escaped_key = escape(key)
                        escaped_value = escape(value)
                        if bucket_name == "슬롯":
                            visited = " → ".join(
                                str(index) for index in table.probe_path(key)
                            )
                            search_detail = f"방문 슬롯 {visited}"
                        else:
                            visited_nodes = " → ".join(
                                escape(node_key)
                                for node_key, _ in bucket[:position]
                            )
                            search_detail = f"방문 노드 {visited_nodes}"
                        rows.append(
                            "<li>"
                            f"키 <code>{escaped_key}</code>, 값 <code>{escaped_value}</code>; "
                            f"{search_detail}; "
                            f"<code>{escape(_hash_explanation(key, table.capacity))}</code>"
                            "</li>"
                        )
                    rows.append("</ol>")
                sections.append("".join(rows))
            return _page("".join(sections), "충돌 처리 방식과 탐색 근거")

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
    parser.add_argument("--strategy", choices=("chaining", "linear"), default="chaining")
    arguments = parser.parse_args()
    server = create_server(port=arguments.port, strategy=arguments.strategy)
    print(f"Serving on http://0.0.0.0:{arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
