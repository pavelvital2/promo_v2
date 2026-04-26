from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from apps.discounts.wb_api.client import (
    WBApiAuthError,
    WBApiClient,
    WBApiInvalidResponseError,
    WBApiPolicy,
    WBApiRateLimitError,
    WBApiTimeoutError,
)
from apps.discounts.wb_api.redaction import contains_secret_like, redact


class FakeResponse:
    def __init__(self, status_code, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            },
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class WBApiClientTask011Tests(SimpleTestCase):
    def _client(self, session):
        return WBApiClient(
            token="Bearer abcdefghijklmnopqrstuvwxyz1234567890",
            session=session,
            policy=WBApiPolicy(max_retries=1, backoff_seconds=0),
            store_scope="STORE-000001",
        )

    def test_check_connection_uses_read_only_endpoint_and_safe_timeout(self):
        session = FakeSession([FakeResponse(200, {"data": {"listGoods": []}})])

        result = self._client(session).check_connection()

        self.assertEqual(result, {"data": {"listGoods": []}})
        call = session.calls[0]
        self.assertTrue(call["url"].endswith("/api/v2/list/goods/filter"))
        self.assertEqual(call["params"], {"limit": 1, "offset": 0})
        self.assertEqual(call["timeout"], (3.0, 10.0))

    def test_auth_failures_map_to_safe_exception(self):
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                session = FakeSession([FakeResponse(status_code, {})])
                with self.assertRaises(WBApiAuthError):
                    self._client(session).check_connection()

    @patch("apps.discounts.wb_api.client.sleep", lambda seconds: None)
    def test_429_retries_then_fails_safely(self):
        session = FakeSession([FakeResponse(429, {}), FakeResponse(429, {})])

        with self.assertRaises(WBApiRateLimitError):
            self._client(session).check_connection()

        self.assertEqual(len(session.calls), 2)

    @patch("apps.discounts.wb_api.client.sleep", lambda seconds: None)
    def test_timeout_retries_then_fails_safely(self):
        session = FakeSession([TimeoutError("network timeout"), TimeoutError("network timeout")])

        with self.assertRaises(WBApiTimeoutError):
            self._client(session).check_connection()

        self.assertEqual(len(session.calls), 2)

    def test_invalid_response_fails_safely(self):
        invalid_cases = (
            FakeResponse(200, ["not", "dict"]),
            FakeResponse(200, json_error=ValueError("invalid json")),
            FakeResponse(500, {}),
        )
        for response in invalid_cases:
            with self.subTest(response=response):
                session = FakeSession([response])
                with self.assertRaises(WBApiInvalidResponseError):
                    self._client(session).check_connection()

    def test_redaction_detects_headers_tokens_and_secret_like_values(self):
        unsafe = {
            "Authorization": "Bearer abcdefghijklmnopqrstuvwxyz1234567890",
            "safe": {"note": "public"},
        }

        redacted = redact(unsafe)

        self.assertTrue(contains_secret_like(unsafe))
        self.assertFalse(contains_secret_like(redacted))
        self.assertEqual(redacted["redacted_field_1"], "[redacted]")
        self.assertEqual(redacted["safe"]["note"], "public")
