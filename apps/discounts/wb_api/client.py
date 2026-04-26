"""Mockable WB API client with TASK-011 safety defaults."""

from __future__ import annotations

from dataclasses import dataclass
import json
from time import monotonic, sleep
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .redaction import assert_no_secret_like_values, redact


WB_DISCOUNTS_API_BASE_URL = "https://discounts-prices-api.wildberries.ru"
WB_CONNECTION_CHECK_PATH = "/api/v2/list/goods/filter"


class WBApiError(Exception):
    safe_message = "WB API request failed."
    techlog_event_type = "wb_api_response_invalid"


class WBApiAuthError(WBApiError):
    safe_message = "WB API authorization or access check failed."
    techlog_event_type = "wb_api_auth_failed"


class WBApiRateLimitError(WBApiError):
    safe_message = "WB API rate limit reached."
    techlog_event_type = "wb_api_rate_limited"


class WBApiTimeoutError(WBApiError):
    safe_message = "WB API request timed out."
    techlog_event_type = "wb_api_timeout"


class WBApiInvalidResponseError(WBApiError):
    safe_message = "WB API returned an invalid response."
    techlog_event_type = "wb_api_response_invalid"


@dataclass(frozen=True)
class WBApiPolicy:
    connect_timeout: float = 3.0
    read_timeout: float = 10.0
    max_retries: int = 2
    backoff_seconds: float = 0.1


class ScopedRateLimiter:
    def __init__(self, *, interval_seconds: float = 0.6):
        self.interval_seconds = interval_seconds
        self._last_seen_by_scope: dict[tuple[str, str], float] = {}

    def wait(self, *, store_scope: str, api_category: str) -> None:
        scope = (str(store_scope), api_category)
        now = monotonic()
        last_seen = self._last_seen_by_scope.get(scope)
        if last_seen is not None:
            wait_for = self.interval_seconds - (now - last_seen)
            if wait_for > 0:
                sleep(wait_for)
        self._last_seen_by_scope[scope] = monotonic()


class WBApiClient:
    def __init__(
        self,
        *,
        token: str,
        base_url: str = WB_DISCOUNTS_API_BASE_URL,
        session=None,
        policy: WBApiPolicy | None = None,
        rate_limiter: ScopedRateLimiter | None = None,
        store_scope: str = "",
    ):
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or UrllibSession()
        self.policy = policy or WBApiPolicy()
        self.rate_limiter = rate_limiter or ScopedRateLimiter()
        self.store_scope = store_scope

    def check_connection(self) -> dict:
        return self.get_json(
            WB_CONNECTION_CHECK_PATH,
            params={"limit": 1, "offset": 0},
            api_category="prices_and_discounts",
        )

    def list_goods_filter(self, *, limit: int = 1000, offset: int = 0) -> dict:
        return self.get_json(
            WB_CONNECTION_CHECK_PATH,
            params={"limit": limit, "offset": offset},
            api_category="prices_and_discounts",
        )

    def get_json(self, path: str, *, params: dict | None = None, api_category: str) -> dict:
        safe_params = redact(params or {})
        assert_no_secret_like_values(safe_params, field_name="request params")
        url = urljoin(self.base_url, path.lstrip("/"))
        timeout = (self.policy.connect_timeout, self.policy.read_timeout)
        last_error = None

        for attempt in range(self.policy.max_retries + 1):
            self.rate_limiter.wait(store_scope=self.store_scope, api_category=api_category)
            try:
                response = self.session.get(
                    url,
                    params=params or {},
                    headers={"Authorization": self.token},
                    timeout=timeout,
                )
            except TimeoutError as exc:
                last_error = exc
                if attempt >= self.policy.max_retries:
                    raise WBApiTimeoutError(WBApiTimeoutError.safe_message) from exc
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue

            if response.status_code in {401, 403}:
                raise WBApiAuthError(WBApiAuthError.safe_message)
            if response.status_code == 429:
                last_error = WBApiRateLimitError(WBApiRateLimitError.safe_message)
                if attempt >= self.policy.max_retries:
                    raise last_error
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue
            if response.status_code >= 400:
                raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)

            try:
                data = response.json()
            except ValueError as exc:
                raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message) from exc
            if not isinstance(data, dict):
                raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)
            return data

        if isinstance(last_error, WBApiError):
            raise last_error
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)


class UrllibResponse:
    def __init__(self, *, status_code: int, body: bytes):
        self.status_code = status_code
        self._body = body

    def json(self):
        return json.loads(self._body.decode("utf-8"))


class UrllibSession:
    def get(self, url: str, *, params=None, headers=None, timeout=None):
        query = urlencode(params or {})
        full_url = f"{url}?{query}" if query else url
        request = Request(full_url, headers=headers or {}, method="GET")
        try:
            with urlopen(request, timeout=(timeout or (None, None))[1]) as response:
                return UrllibResponse(status_code=response.status, body=response.read())
        except HTTPError as exc:
            return UrllibResponse(status_code=exc.code, body=exc.read())
        except TimeoutError:
            raise
        except OSError as exc:
            raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message) from exc
