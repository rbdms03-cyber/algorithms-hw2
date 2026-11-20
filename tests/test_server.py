import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server
from src.shortener import Shortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener()
        self.server = create_server("127.0.0.1", 0, self.shortener)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1], timeout=5
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        return response.status, response.getheaders(), response.read().decode("utf-8")

    def test_form_and_table_page(self):
        status, _, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('action="/shorten"', page)

        status, _, table = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("용량", table)
        self.assertIn("버킷 0", table)

    def test_shorten_redirect_and_unknown_code(self):
        body = urlencode({"url": "https://example.com/a"})
        status, _, result = self.request(
            "POST",
            "/shorten",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 200)
        self.assertIn("<code>1</code>", result)

        status, headers, _ = self.request("GET", "/r/1")
        self.assertEqual(status, 302)
        self.assertIn(("Location", "https://example.com/a"), headers)

        status, _, page = self.request("GET", "/r/missing")
        self.assertEqual(status, 404)
        self.assertIn("존재하지 않는", page)

    def test_table_shows_chained_url_nodes_and_expandable_horner_steps(self):
        table = self.shortener.tables[0]
        first_url = "https://example.com/collision/0"
        first_index = table.hash_index(first_url)
        second_url = next(
            f"https://example.com/collision/{number}"
            for number in range(1, 1000)
            if table.hash_index(f"https://example.com/collision/{number}")
            == first_index
        )
        for url in (first_url, second_url):
            status, _, _ = self.request(
                "POST",
                "/shorten",
                urlencode({"url": url}),
                {"Content-Type": "application/x-www-form-urlencoded"},
            )
            self.assertEqual(status, 200)

        status, _, table = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("URL 키", table)
        self.assertIn(first_url, table)
        self.assertIn(second_url, table)
        self.assertIn("짧은 코드", table)
        self.assertIn('href="/r/1">/r/1</a>', table)
        self.assertIn('href="/r/2">/r/2</a>', table)
        self.assertIn("→", table)
        self.assertIn("<details>", table)
        self.assertIn("<summary>호너 해시 계산 과정</summary>", table)
        self.assertIn("h0 = 0", table)
        self.assertIn("h(key) =", table)
        self.assertIn("ord(", table)

    def test_table_escapes_url_keys(self):
        url = "https://example.com/<script>"
        status, _, _ = self.request(
            "POST",
            "/shorten",
            urlencode({"url": url}),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 200)

        status, _, table = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;", table)
        self.assertNotIn("<script>", table)

    def test_linear_table_shows_visited_slots(self):
        server = create_server("127.0.0.1", 0, strategy="linear")
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            connection.request(
                "POST",
                "/shorten",
                urlencode({"url": "https://example.com/linear"}),
                {"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = connection.getresponse()
            response.read()
            connection.request("GET", "/table")
            response = connection.getresponse()
            page = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("선형 탐지", page)
            self.assertIn("방문 슬롯", page)
            self.assertIn("h(key) =", page)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_invalid_url_returns_bad_request_and_is_escaped(self):
        body = urlencode({"url": "ftp://example.com/?q=<script>"})
        status, _, page = self.request(
            "POST",
            "/shorten",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)
        self.assertNotIn("<script>", page)

    def test_unknown_route_returns_not_found(self):
        status, _, _ = self.request("GET", "/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
