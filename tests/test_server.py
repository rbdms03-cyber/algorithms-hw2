import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server
from src.shortener import Shortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0, Shortener())
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

    def test_table_shows_horner_hash_calculation(self):
        self.request(
            "POST",
            "/shorten",
            urlencode({"url": "https://example.com/hash"}),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        status, _, table = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("h(key) =", table)
        self.assertIn("ord(", table)

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
