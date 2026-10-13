"""Local authenticated proxy relay for Chromium and requests."""
from __future__ import annotations

import base64
import select
import socket
import socketserver
import ssl
import threading
from urllib.parse import unquote, urlsplit


class ProxyConfigError(ValueError):
    pass


def validate_proxy_url(value: str) -> str:
    value = value.strip()
    try:
        parsed = urlsplit(value)
        if (parsed.scheme.lower() not in ("http", "https", "socks5", "socks5h")
                or not parsed.hostname or parsed.port is None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or any(char in value for char in "\r\n\t ")):
            raise ValueError
        if (parsed.username is None) != (parsed.password is None):
            raise ValueError
        parsed.port
    except (ValueError, UnicodeError):
        raise ProxyConfigError(
            "Proxy URL must include a supported scheme, host and port; "
            "encode special characters in credentials.") from None
    return value


def _read_headers(sock: socket.socket) -> tuple[bytes, bytes]:
    data = bytearray()
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Proxy peer closed before sending headers")
        data.extend(chunk)
        if len(data) > 65536:
            raise ConnectionError("Proxy headers exceed limit")
    end = data.index(b"\r\n\r\n") + 4
    return bytes(data[:end]), bytes(data[end:])


def _parse_headers(raw: bytes) -> tuple[str, list[tuple[str, str]]]:
    lines = raw[:-4].decode("iso-8859-1").split("\r\n")
    request_line = lines[0]
    headers = []
    for line in lines[1:]:
        if ":" not in line:
            raise ConnectionError("Malformed proxy request header")
        name, value = line.split(":", 1)
        headers.append((name.strip(), value.strip()))
    return request_line, headers


def _format_headers(request_line: str, headers: list[tuple[str, str]]) -> bytes:
    lines = [request_line]
    lines.extend(f"{name}: {value}" for name, value in headers)
    return ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1")


def _tunnel(left: socket.socket, right: socket.socket) -> None:
    active = {left, right}
    while active:
        readable, _, _ = select.select(list(active), [], [], 60)
        if not readable:
            continue
        for source in readable:
            destination = right if source is left else left
            try:
                data = source.recv(65536)
            except OSError:
                data = b""
            if data:
                try:
                    destination.sendall(data)
                except OSError:
                    active.discard(source)
                    active.discard(destination)
            else:
                active.discard(source)
                try:
                    destination.shutdown(socket.SHUT_WR)
                except OSError:
                    pass


class ProxyRelay:
    """Expose an authenticated HTTP or SOCKS5 proxy as a local HTTP proxy."""

    def __init__(self, proxy_url: str):
        parsed = urlsplit(validate_proxy_url(proxy_url))
        self.scheme = parsed.scheme.lower()
        self.host = parsed.hostname or ""
        self.port = parsed.port or 0
        self.username = unquote(parsed.username) if parsed.username is not None else None
        self.password = unquote(parsed.password) if parsed.password is not None else None

        relay = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                client = self.request
                response_started = False
                try:
                    raw, pending = _read_headers(client)
                    request_line, headers = _parse_headers(raw)
                    method, target, version = request_line.split(" ", 2)
                    if relay.scheme.startswith("socks5"):
                        relay._handle_socks(client, pending, method, target, version, headers)
                    else:
                        relay._handle_http(client, pending, method, target, version,
                                           headers)
                    response_started = True
                except Exception:
                    if not response_started:
                        try:
                            client.sendall(
                                b"HTTP/1.1 502 Bad Gateway\r\n"
                                b"Connection: close\r\nContent-Length: 0\r\n\r\n")
                        except OSError:
                            pass

        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.server = Server(("127.0.0.1", 0), Handler)
        self.port_local = self.server.server_address[1]
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        self.url = f"http://127.0.0.1:{self.port_local}"

    def _connect_upstream(self) -> socket.socket:
        upstream = socket.create_connection((self.host, self.port), timeout=20)
        if self.scheme == "https":
            try:
                upstream = ssl.create_default_context().wrap_socket(
                    upstream, server_hostname=self.host)
            except Exception:
                upstream.close()
                raise
        upstream.settimeout(None)
        return upstream

    def _proxy_authorization(self) -> str | None:
        if self.username is None:
            return None
        raw = f"{self.username}:{self.password}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _with_connection_close(headers: list[tuple[str, str]]) -> list[tuple[str, str]]:
        result = [(name, value) for name, value in headers
                  if name.lower() not in (
                      "connection", "proxy-connection", "proxy-authorization")]
        result.append(("Connection", "close"))
        return result

    def _handle_http(self, client: socket.socket, pending: bytes, method: str,
                     target: str, version: str, headers: list[tuple[str, str]]) -> None:
        upstream = self._connect_upstream()
        try:
            outgoing = self._with_connection_close(headers)
            auth = self._proxy_authorization()
            if auth:
                outgoing.append(("Proxy-Authorization", auth))
            if method.upper() == "CONNECT":
                outgoing.append(("Proxy-Connection", "Keep-Alive"))
            upstream.sendall(_format_headers(f"{method} {target} {version}", outgoing))
            if pending:
                upstream.sendall(pending)

            if method.upper() == "CONNECT":
                response, rest = _read_headers(upstream)
                client.sendall(response)
                if rest:
                    client.sendall(rest)
                if not response.split(b"\r\n", 1)[0].split()[1:2] == [b"200"]:
                    return
            _tunnel(client, upstream)
        finally:
            upstream.close()

    def _socks_connect(self, sock: socket.socket, host: str, port: int) -> None:
        methods = b"\x02" if self.username is not None else b"\x00"
        sock.sendall(b"\x05" + bytes((len(methods),)) + methods)
        reply = self._recv_exact(sock, 2)
        if reply[0] != 5 or reply[1] == 0xFF:
            raise ConnectionError("SOCKS5 proxy rejected authentication methods")
        if reply[1] == 2:
            user = (self.username or "").encode("utf-8")
            password = (self.password or "").encode("utf-8")
            if len(user) > 255 or len(password) > 255:
                raise ConnectionError("SOCKS5 credentials exceed protocol limit")
            sock.sendall(b"\x01" + bytes((len(user),)) + user
                         + bytes((len(password),)) + password)
            auth_reply = self._recv_exact(sock, 2)
            if auth_reply != b"\x01\x00":
                raise ConnectionError("SOCKS5 proxy authentication failed")
        elif reply[1] != 0:
            raise ConnectionError("SOCKS5 proxy selected an unsupported method")

        try:
            address = socket.inet_aton(host)
            address_type = b"\x01"
        except OSError:
            try:
                address = socket.inet_pton(socket.AF_INET6, host)
                address_type = b"\x04"
            except OSError:
                address = host.encode("idna")
                if len(address) > 255:
                    raise ConnectionError("SOCKS5 destination name exceeds protocol limit")
                address_type = b"\x03" + bytes((len(address),))
        sock.sendall(b"\x05\x01\x00" + address_type + address
                     + int(port).to_bytes(2, "big"))
        response = self._recv_exact(sock, 4)
        if response[0] != 5 or response[1] != 0:
            raise ConnectionError("SOCKS5 proxy could not connect to destination")
        if response[3] == 1:
            self._recv_exact(sock, 4)
        elif response[3] == 4:
            self._recv_exact(sock, 16)
        elif response[3] == 3:
            self._recv_exact(sock, self._recv_exact(sock, 1)[0])
        else:
            raise ConnectionError("SOCKS5 proxy returned an invalid address")
        self._recv_exact(sock, 2)

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            chunk = sock.recv(size - len(result))
            if not chunk:
                raise ConnectionError("SOCKS5 proxy closed the connection")
            result.extend(chunk)
        return bytes(result)

    def _handle_socks(self, client: socket.socket, pending: bytes, method: str,
                      target: str, version: str,
                      headers: list[tuple[str, str]]) -> None:
        if method.upper() == "CONNECT":
            parsed = urlsplit("//" + target)
            host, port = parsed.hostname, parsed.port
        else:
            parsed = urlsplit(target)
            if parsed.scheme.lower() != "http":
                raise ConnectionError("SOCKS5 HTTP relay only accepts HTTP or CONNECT")
            host, port = parsed.hostname, parsed.port or 80
        if not host or not port:
            raise ConnectionError("Proxy request has an invalid destination")

        upstream = socket.create_connection((self.host, self.port), timeout=20)
        upstream.settimeout(20)
        try:
            self._socks_connect(upstream, host, port)
            upstream.settimeout(None)
            if method.upper() == "CONNECT":
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n"
                               b"Proxy-Agent: muse2api\r\n\r\n")
                if pending:
                    upstream.sendall(pending)
            else:
                path = parsed.path or "/"
                if parsed.query:
                    path += "?" + parsed.query
                outgoing = self._with_connection_close(headers)
                upstream.sendall(_format_headers(
                    f"{method} {path} {version}", outgoing))
                if pending:
                    upstream.sendall(pending)
            _tunnel(client, upstream)
        finally:
            upstream.close()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=2)


class ProxyRelayPool:
    def __init__(self):
        self._lock = threading.Lock()
        self._relays: dict[str, ProxyRelay] = {}

    def get(self, proxy_url: str) -> ProxyRelay:
        normalized = validate_proxy_url(proxy_url)
        with self._lock:
            relay = self._relays.get(normalized)
            if relay is None:
                relay = ProxyRelay(normalized)
                self._relays[normalized] = relay
            return relay

    def close(self) -> None:
        with self._lock:
            relays = list(self._relays.values())
            self._relays.clear()
        for relay in relays:
            relay.close()
