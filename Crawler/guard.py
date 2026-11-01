"""
Crawler Request Guard (Rule L20)
Enforces host allowlists, denylists, HTTPS scheme enforcement,
thread-safe rate limiting, and robots.txt parsing.
"""

import time
import threading
import urllib.request
import urllib.error
import urllib.parse
import urllib.robotparser
from typing import Tuple, Optional, Dict, Any

ALLOWED_HOSTS = {
    "www.myscheme.gov.in",
    "myscheme.gov.in",
    "api.myscheme.gov.in"
}

DENIED_HOSTS = {
    "aistore.myscheme.in",
    "auth.myscheme.gov.in",
    "login.myscheme.gov.in",
    "admin.myscheme.gov.in"
}

DENIED_PATH_PREFIXES = (
    "/api/auth",
    "/api/user",
    "/api/admin",
    "/api/v1/auth"
)

DEFAULT_USER_AGENT = "JanSevaAI-SchemeDiscovery/1.0 (+https://github.com/JanSevaAI)"


class RequestGuard:
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        delay_seconds: float = 0.35,
        timeout_seconds: float = 15.0,
        max_retries: int = 3
    ):
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._last_request_time = 0.0
        self._rate_lock = threading.Lock()
        self._robots_lock = threading.Lock()
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def validate_url(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path

        if parsed.scheme != "https":
            raise PermissionError("Request denied: HTTPS is required (Rule L20)")

        if host in DENIED_HOSTS:
            raise PermissionError(f"Request denied: host '{host}' is in denylist (Rule L20)")

        for prefix in DENIED_PATH_PREFIXES:
            if path.startswith(prefix):
                raise PermissionError(f"Request denied: path prefix '{prefix}' is blocked (Rule L20)")

        if host not in ALLOWED_HOSTS:
            raise PermissionError(f"Request denied: host '{host}' is not in allowlist (Rule L20)")

    def check_robots(self, url: str) -> None:
        self.validate_url(url)
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        robots_url = f"https://{host}/robots.txt"

        with self._robots_lock:
            if host not in self._robots_cache:
                rfp = urllib.robotparser.RobotFileParser()
                rfp.set_url(robots_url)
                try:
                    req = urllib.request.Request(robots_url, headers={"User-Agent": self.user_agent})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                        rfp.parse(lines)
                except Exception:
                    # Permissive fallback if robots.txt cannot be read
                    rfp.parse(["User-agent: *", "Allow: /"])
                self._robots_cache[host] = rfp
            rfp = self._robots_cache[host]

        if not rfp.can_fetch(self.user_agent, url):
            raise PermissionError(f"Request denied: robots.txt disallows '{url}'")

    def fetch(
        self,
        url: str,
        extra_headers: Optional[Dict[str, str]] = None,
        check_robots: bool = True
    ) -> Tuple[int, bytes, Dict[str, str]]:
        if check_robots:
            self.check_robots(url)
        else:
            self.validate_url(url)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if extra_headers:
            headers.update(extra_headers)

        attempt = 0
        backoff = 1.0

        while attempt < self.max_retries:
            attempt += 1

            # Thread-safe polite delay
            with self._rate_lock:
                now = time.time()
                elapsed = now - self._last_request_time
                if elapsed < self.delay_seconds:
                    time.sleep(self.delay_seconds - elapsed)
                self._last_request_time = time.time()

            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    status = response.status
                    body = response.read()
                    resp_headers = {k.lower(): v for k, v in response.getheaders()}
                    return status, body, resp_headers
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    retry_after = e.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else (backoff * (2 ** (attempt - 1)))
                    time.sleep(sleep_time)
                    continue
                body = e.read() if hasattr(e, "read") else b""
                resp_headers = {k.lower(): v for k, v in e.headers.items()} if hasattr(e, "headers") else {}
                return e.code, body, resp_headers
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < self.max_retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                raise ConnectionError(f"Failed to fetch {url} after {attempt} attempts: {e}")

        raise ConnectionError(f"Failed to fetch {url} after {self.max_retries} attempts")
