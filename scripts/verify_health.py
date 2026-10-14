"""Smoke-test the local API health endpoint using only the Python standard library."""

import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

URL = "http://127.0.0.1:8000/health"

try:
    with urlopen(URL, timeout=5) as response:
        body = response.read().decode("utf-8")
        payload = json.loads(body)
        assert response.status == 200, f"Expected HTTP 200, got {response.status}"
        assert payload.get("status") == "ok", f"Unexpected status field: {payload!r}"
        assert isinstance(payload.get("version"), str), "Expected version to be a string"
        print(f"PASS: HTTP {response.status} {URL}")
        print(json.dumps(payload, indent=2))
except (URLError, TimeoutError, json.JSONDecodeError, AssertionError) as exc:
    print(f"FAIL: {exc}", file=sys.stderr)
    sys.exit(1)
