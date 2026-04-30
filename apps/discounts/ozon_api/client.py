"""Safe Ozon API client baseline for Stage 2.2 connection checks."""

from __future__ import annotations

from dataclasses import dataclass
import json
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from apps.discounts.wb_api.redaction import assert_no_secret_like_values, redact


OZON_API_BASE_URL = "https://api-seller.ozon.ru"
OZON_ACTIONS_PATH = "/v1/actions"
OZON_ACTION_PRODUCTS_PATH = "/v1/actions/products"
OZON_ACTION_CANDIDATES_PATH = "/v1/actions/candidates"
OZON_ACTION_PRODUCTS_ACTIVATE_PATH = "/v1/actions/products/activate"
OZON_ACTION_PRODUCTS_DEACTIVATE_PATH = "/v1/actions/products/deactivate"
OZON_PRODUCT_INFO_LIST_PATH = "/v3/product/info/list"
OZON_PRODUCT_INFO_STOCKS_PATH = "/v4/product/info/stocks"


class OzonApiError(Exception):
    safe_message = "Ozon API request failed."
    techlog_event_type = "ozon_api_response_invalid"
    check_status = "invalid_response"


class OzonApiAuthError(OzonApiError):
    safe_message = "Ozon API authorization or access check failed."
    techlog_event_type = "ozon_api_auth_failed"
    check_status = "auth_failed"


class OzonApiRateLimitError(OzonApiError):
    safe_message = "Ozon API rate limit reached."
    techlog_event_type = "ozon_api_rate_limited"
    check_status = "rate_limited"


class OzonApiTemporaryError(OzonApiError):
    safe_message = "Ozon API temporary failure."
    techlog_event_type = "ozon_api_timeout"
    check_status = "temporary"


class OzonApiInvalidResponseError(OzonApiError):
    safe_message = "Ozon API returned an invalid response."
    techlog_event_type = "ozon_api_response_invalid"
    check_status = "invalid_response"


@dataclass(frozen=True)
class OzonApiCredentials:
    client_id: str
    api_key: str


@dataclass(frozen=True)
class OzonApiPolicy:
    connect_timeout: float = 3.0
    read_timeout: float = 10.0
    max_read_retries: int = 2
    backoff_seconds: float = 0.1
    min_interval_seconds: float = 0.5
    read_page_size: int = 100
    write_batch_size: int = 100


class OzonScopedRateLimiter:
    def __init__(self, *, interval_seconds: float = 0.5):
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


class OzonApiClient:
    def __init__(
        self,
        *,
        credentials: OzonApiCredentials,
        base_url: str = OZON_API_BASE_URL,
        session=None,
        policy: OzonApiPolicy | None = None,
        rate_limiter: OzonScopedRateLimiter | None = None,
        store_scope: str = "",
    ):
        self.credentials = credentials
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or OzonUrllibSession()
        self.policy = policy or OzonApiPolicy()
        self.rate_limiter = rate_limiter or OzonScopedRateLimiter(
            interval_seconds=self.policy.min_interval_seconds,
        )
        self.store_scope = store_scope

    def check_connection(self) -> dict:
        data = self.get_json(OZON_ACTIONS_PATH, api_category="actions")
        if "result" not in data:
            raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
        return data

    def list_actions(self, *, limit: int | None = None, offset: int = 0) -> dict:
        params = {}
        if limit is not None:
            params["limit"] = limit
            params["offset"] = offset
        return self.get_json(OZON_ACTIONS_PATH, params=params, api_category="actions")

    def list_action_products(
        self,
        *,
        action_id: str,
        limit: int | None = None,
        offset: int = 0,
        last_id: str = "",
    ) -> dict:
        return self._list_action_product_group(
            path=OZON_ACTION_PRODUCTS_PATH,
            action_id=action_id,
            limit=limit,
            offset=offset,
            last_id=last_id,
        )

    def list_action_candidates(
        self,
        *,
        action_id: str,
        limit: int | None = None,
        offset: int = 0,
        last_id: str = "",
    ) -> dict:
        return self._list_action_product_group(
            path=OZON_ACTION_CANDIDATES_PATH,
            action_id=action_id,
            limit=limit,
            offset=offset,
            last_id=last_id,
        )

    def _list_action_product_group(
        self,
        *,
        path: str,
        action_id: str,
        limit: int | None,
        offset: int,
        last_id: str,
    ) -> dict:
        payload = {
            "action_id": action_id,
            "limit": limit or self.policy.read_page_size,
            "offset": offset,
        }
        if last_id:
            payload["last_id"] = last_id
        return self.post_json(path, payload=payload, api_category="actions")

    def product_info_list(self, *, product_ids: list[str | int]) -> dict:
        return self.post_json(
            OZON_PRODUCT_INFO_LIST_PATH,
            payload={"product_id": [str(product_id) for product_id in product_ids]},
            api_category="product_info",
        )

    def product_info_stocks(self, *, product_ids: list[str | int]) -> dict:
        return self.post_json(
            OZON_PRODUCT_INFO_STOCKS_PATH,
            payload={
                "filter": {
                    "product_id": [str(product_id) for product_id in product_ids],
                    "visibility": "ALL",
                },
                "limit": self.policy.read_page_size,
            },
            api_category="stocks",
        )

    def activate_action_products(self, *, action_id: str, products: list[dict]) -> dict:
        payload = {"action_id": str(action_id), "products": products}
        return self.post_json(
            OZON_ACTION_PRODUCTS_ACTIVATE_PATH,
            payload=payload,
            api_category="actions_write",
            retry=False,
        )

    def deactivate_action_products(self, *, action_id: str, products: list[dict]) -> dict:
        payload = {"action_id": str(action_id), "products": products}
        return self.post_json(
            OZON_ACTION_PRODUCTS_DEACTIVATE_PATH,
            payload=payload,
            api_category="actions_write",
            retry=False,
        )

    def get_json(
        self,
        path: str,
        *,
        params: dict | None = None,
        api_category: str,
    ) -> dict:
        safe_params = redact(params or {})
        assert_no_secret_like_values(safe_params, field_name="Ozon request params")
        url = urljoin(self.base_url, path.lstrip("/"))
        return self._request_json(
            "GET",
            url,
            params=params or {},
            payload=None,
            api_category=api_category,
            retry=True,
        )

    def post_json(
        self,
        path: str,
        *,
        payload: dict,
        api_category: str,
        retry: bool = True,
    ) -> dict:
        safe_payload = redact(payload)
        assert_no_secret_like_values(safe_payload, field_name="Ozon request payload")
        url = urljoin(self.base_url, path.lstrip("/"))
        return self._request_json(
            "POST",
            url,
            params={},
            payload=payload,
            api_category=api_category,
            retry=retry,
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict | None,
        payload: dict | None,
        api_category: str,
        retry: bool,
    ) -> dict:
        if method not in {"GET", "POST"}:
            raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)

        timeout = (self.policy.connect_timeout, self.policy.read_timeout)
        max_retries = self.policy.max_read_retries if retry else 0
        last_error = None

        for attempt in range(max_retries + 1):
            self.rate_limiter.wait(store_scope=self.store_scope, api_category=api_category)
            try:
                headers = {
                    "Client-Id": self.credentials.client_id,
                    "Api-Key": self.credentials.api_key,
                }
                if method == "GET":
                    response = self.session.get(
                        url,
                        params=params or {},
                        headers=headers,
                        timeout=timeout,
                    )
                else:
                    response = self.session.post(
                        url,
                        json=payload or {},
                        headers=headers,
                        timeout=timeout,
                    )
            except (TimeoutError, OSError) as exc:
                last_error = OzonApiTemporaryError(OzonApiTemporaryError.safe_message)
                if attempt >= max_retries:
                    raise last_error from exc
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue

            if response.status_code in {401, 403}:
                raise OzonApiAuthError(OzonApiAuthError.safe_message)
            if response.status_code == 429:
                last_error = OzonApiRateLimitError(OzonApiRateLimitError.safe_message)
                if attempt >= max_retries:
                    raise last_error
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue
            if response.status_code >= 500:
                last_error = OzonApiTemporaryError(OzonApiTemporaryError.safe_message)
                if attempt >= max_retries:
                    raise last_error
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue
            if response.status_code >= 400:
                raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)

            try:
                data = response.json()
            except ValueError as exc:
                raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message) from exc
            if not isinstance(data, dict):
                raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
            return data

        if isinstance(last_error, OzonApiError):
            raise last_error
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)


class OzonUrllibResponse:
    def __init__(self, *, status_code: int, body: bytes):
        self.status_code = status_code
        self._body = body

    def json(self):
        return json.loads(self._body.decode("utf-8"))


class OzonUrllibSession:
    def get(self, url: str, *, params=None, headers=None, timeout=None):
        query = urlencode(params or {}, doseq=True)
        full_url = f"{url}?{query}" if query else url
        request = Request(full_url, headers=headers or {}, method="GET")
        return self._open(request, timeout=timeout)

    def post(self, url: str, *, json=None, headers=None, timeout=None):
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        body = globals()["json"].dumps(json or {}).encode("utf-8")
        request = Request(url, data=body, headers=request_headers, method="POST")
        return self._open(request, timeout=timeout)

    def _open(self, request: Request, *, timeout=None):
        try:
            with urlopen(request, timeout=(timeout or (None, None))[1]) as response:
                return OzonUrllibResponse(status_code=response.status, body=response.read())
        except HTTPError as exc:
            return OzonUrllibResponse(status_code=exc.code, body=exc.read())
