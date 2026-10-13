import base64
import socket
import socketserver
import threading
import tempfile
import unittest
from types import SimpleNamespace

from proxy_relay import ProxyConfigError, ProxyRelay, validate_proxy_url
from store import Store


def _read_header(sock):
    data = bytearray()
    while b"\r\n\r\n" not in data:
        data.extend(sock.recv(4096))
    return bytes(data[:data.index(b"\r\n\r\n") + 4])


def _recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        data.extend(sock.recv(size - len(data)))
    return bytes(data)


class ProxyRelayTests(unittest.TestCase):
    def test_validate_supported_proxy_urls_without_echoing_credentials(self):
        self.assertEqual(
            validate_proxy_url("socks5://user:p%40ss@proxy.example:1080"),
            "socks5://user:p%40ss@proxy.example:1080")
        with self.assertRaises(ProxyConfigError) as caught:
            validate_proxy_url("ftp://private-user:private-pass@example.com:21")
        self.assertNotIn("private-pass", str(caught.exception))

    def test_account_listing_does_not_expose_proxy_credentials(self):
        with tempfile.TemporaryDirectory() as data_dir:
            store = Store(SimpleNamespace(
                accounts_file=f"{data_dir}/accounts.json",
                tasks_file=f"{data_dir}/tasks.json"))
            account = store.add_account({"hatch_sess": "cookie"})
            store.update_account(
                account["id"],
                proxy_url="http://private-user:private-pass@proxy.example:8080")
            public_account = store.list_accounts()[0]
            self.assertTrue(public_account["proxy_configured"])
            self.assertNotIn("proxy_url", public_account)
            self.assertNotIn("private-pass", str(public_account))

    def test_http_proxy_auth_and_connect_tunnel(self):
        seen = {}

        class UpstreamHandler(socketserver.BaseRequestHandler):
            def handle(self):
                seen["headers"] = _read_header(self.request)
                self.request.sendall(
                    b"HTTP/1.1 200 Connection Established\r\n\r\n")
                data = self.request.recv(1024)
                self.request.sendall(data)

        class Upstream(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        upstream = Upstream(("127.0.0.1", 0), UpstreamHandler)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        relay = ProxyRelay(
            f"http://proxy-user:proxy-pass@127.0.0.1:{upstream.server_address[1]}")
        client = socket.create_connection(("127.0.0.1", relay.port_local), timeout=5)
        try:
            client.sendall(
                b"CONNECT example.com:443 HTTP/1.1\r\n"
                b"Host: example.com:443\r\n\r\n")
            self.assertIn(b"200 Connection Established", _read_header(client))
            client.sendall(b"relay-check")
            self.assertEqual(client.recv(32), b"relay-check")
            expected = base64.b64encode(b"proxy-user:proxy-pass")
            self.assertIn(b"Proxy-Authorization: Basic " + expected, seen["headers"])
        finally:
            client.close()
            relay.close()
            upstream.shutdown()
            upstream.server_close()

    def test_http_proxy_forwards_regular_http_requests_with_auth(self):
        seen = {}

        class UpstreamHandler(socketserver.BaseRequestHandler):
            def handle(self):
                seen["request"] = _read_header(self.request)
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                    b"Connection: close\r\n\r\nok")

        class Upstream(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        upstream = Upstream(("127.0.0.1", 0), UpstreamHandler)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        relay = ProxyRelay(
            f"http://proxy-user:proxy-pass@127.0.0.1:{upstream.server_address[1]}")
        client = socket.create_connection(("127.0.0.1", relay.port_local), timeout=5)
        try:
            client.sendall(
                b"GET http://example.com/check HTTP/1.1\r\n"
                b"Host: example.com\r\n\r\n")
            response = bytearray()
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response.extend(chunk)
            expected = base64.b64encode(b"proxy-user:proxy-pass")
            self.assertIn(b"Proxy-Authorization: Basic " + expected, seen["request"])
            self.assertIn(b"GET http://example.com/check HTTP/1.1", seen["request"])
            self.assertTrue(bytes(response).endswith(b"ok"))
        finally:
            client.close()
            relay.close()
            upstream.shutdown()
            upstream.server_close()

    def test_socks5_username_password_and_connect_tunnel(self):
        seen = {}

        class UpstreamHandler(socketserver.BaseRequestHandler):
            def handle(self):
                _recv_exact(self.request, 2)
                _recv_exact(self.request, 1)
                self.request.sendall(b"\x05\x02")
                self.assert_auth()
                self.request.sendall(b"\x01\x00")
                head = _recv_exact(self.request, 4)
                atyp = head[3]
                if atyp == 3:
                    name_len = _recv_exact(self.request, 1)[0]
                    seen["host"] = _recv_exact(self.request, name_len)
                elif atyp == 1:
                    seen["host"] = _recv_exact(self.request, 4)
                else:
                    seen["host"] = _recv_exact(self.request, 16)
                seen["port"] = int.from_bytes(_recv_exact(self.request, 2), "big")
                self.request.sendall(
                    b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x50")
                data = self.request.recv(1024)
                self.request.sendall(data)

            def assert_auth(self):
                if _recv_exact(self.request, 1) != b"\x01":
                    raise AssertionError("Invalid SOCKS5 auth version")
                user_len = _recv_exact(self.request, 1)[0]
                seen["user"] = _recv_exact(self.request, user_len)
                pass_len = _recv_exact(self.request, 1)[0]
                seen["password"] = _recv_exact(self.request, pass_len)

        class Upstream(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        upstream = Upstream(("127.0.0.1", 0), UpstreamHandler)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        relay = ProxyRelay(
            f"socks5://proxy-user:proxy-pass@127.0.0.1:{upstream.server_address[1]}")
        client = socket.create_connection(("127.0.0.1", relay.port_local), timeout=5)
        try:
            client.sendall(
                b"CONNECT example.com:443 HTTP/1.1\r\n"
                b"Host: example.com:443\r\n\r\n")
            self.assertIn(b"200 Connection Established", _read_header(client))
            client.sendall(b"relay-check")
            self.assertEqual(client.recv(32), b"relay-check")
            self.assertEqual(seen["user"], b"proxy-user")
            self.assertEqual(seen["password"], b"proxy-pass")
            self.assertEqual(seen["host"], b"example.com")
            self.assertEqual(seen["port"], 443)
        finally:
            client.close()
            relay.close()
            upstream.shutdown()
            upstream.server_close()


if __name__ == "__main__":
    unittest.main()
