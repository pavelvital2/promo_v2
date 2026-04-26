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
WB_PROMOTIONS_API_BASE_URL = "https://dp-calendar-api.wildberries.ru"
WB_CONNECTION_CHECK_PATH = "/api/v2/list/goods/filter"
WB_UPLOAD_TASK_PATH = "/api/v2/upload/task"
WB_HISTORY_TASKS_PATH = "/api/v2/history/tasks"
WB_HISTORY_GOODS_TASK_PATH = "/api/v2/history/goods/task"
WB_BUFFER_TASKS_PATH = "/api/v2/buffer/tasks"
WB_BUFFER_GOODS_TASK_PATH = "/api/v2/buffer/goods/task"
WB_QUARANTINE_GOODS_PATH = "/api/v2/quarantine/goods"
WB_PROMOTIONS_LIST_PATH = "/api/v1/calendar/promotions"
WB_PROMOTIONS_DETAILS_PATH = "/api/v1/calendar/promotions/details"
WB_PROMOTIONS_NOMENCLATURES_PATH = "/api/v1/calendar/promotions/nomenclatures"


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


class WBApiAlreadyExistsError(WBApiError):
    safe_message = "WB API upload task already exists."
    techlog_event_type = "wb_api_upload_failed"

    def __init__(self, message: str | None = None, *, response: dict | None = None):
        super().__init__(message or self.safe_message)
        self.response = response or {}


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

    def list_goods_filter_by_nm_list(self, *, nm_list: list[int | str]) -> dict:
        return self.post_json(
            WB_CONNECTION_CHECK_PATH,
            payload={"nmList": list(nm_list)},
            api_category="prices_and_discounts",
            retry=True,
        )

    def upload_discount_task(self, *, data: list[dict]) -> dict:
        return self.post_json(
            WB_UPLOAD_TASK_PATH,
            payload={"data": data},
            api_category="prices_and_discounts",
            retry=False,
        )

    def history_tasks(self, *, upload_id: str | int) -> dict:
        return self.get_json(
            WB_HISTORY_TASKS_PATH,
            params={"uploadID": upload_id},
            api_category="prices_and_discounts",
        )

    def history_goods_task(self, *, upload_id: str | int) -> dict:
        return self.get_json(
            WB_HISTORY_GOODS_TASK_PATH,
            params={"uploadID": upload_id},
            api_category="prices_and_discounts",
        )

    def buffer_tasks(self, *, upload_id: str | int) -> dict:
        return self.get_json(
            WB_BUFFER_TASKS_PATH,
            params={"uploadID": upload_id},
            api_category="prices_and_discounts",
        )

    def buffer_goods_task(self, *, upload_id: str | int) -> dict:
        return self.get_json(
            WB_BUFFER_GOODS_TASK_PATH,
            params={"uploadID": upload_id},
            api_category="prices_and_discounts",
        )

    def quarantine_goods(self, *, nm_list: list[int | str]) -> dict:
        return self.get_json(
            WB_QUARANTINE_GOODS_PATH,
            params={"nmList": ",".join(str(item) for item in nm_list)},
            api_category="prices_and_discounts",
        )

    def list_promotions(
        self,
        *,
        start_datetime: str,
        end_datetime: str,
        all_promo: bool = True,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        return self.get_json(
            WB_PROMOTIONS_LIST_PATH,
            params={
                "startDateTime": start_datetime,
                "endDateTime": end_datetime,
                "allPromo": str(bool(all_promo)).lower(),
                "limit": limit,
                "offset": offset,
            },
            api_category="promotions_calendar",
        )

    def promotion_details(self, *, promotion_ids: list[int]) -> dict:
        return self.get_json(
            WB_PROMOTIONS_DETAILS_PATH,
            params={"promotionIDs": [str(promotion_id) for promotion_id in promotion_ids]},
            api_category="promotions_calendar",
        )

    def promotion_nomenclatures(
        self,
        *,
        promotion_id: int,
        in_action: bool,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        return self.get_json(
            WB_PROMOTIONS_NOMENCLATURES_PATH,
            params={
                "promotionID": promotion_id,
                "inAction": str(bool(in_action)).lower(),
                "limit": limit,
                "offset": offset,
            },
            api_category="promotions_calendar",
        )

    def get_json(self, path: str, *, params: dict | None = None, api_category: str) -> dict:
        safe_params = redact(params or {})
        assert_no_secret_like_values(safe_params, field_name="request params")
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
        payload: dict | None = None,
        api_category: str,
        retry: bool,
    ) -> dict:
        safe_payload = redact(payload or {})
        assert_no_secret_like_values(safe_payload, field_name="request body")
        url = urljoin(self.base_url, path.lstrip("/"))
        return self._request_json(
            "POST",
            url,
            params=None,
            payload=payload or {},
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
        timeout = (self.policy.connect_timeout, self.policy.read_timeout)
        last_error = None
        max_retries = self.policy.max_retries if retry else 0

        for attempt in range(max_retries + 1):
            self.rate_limiter.wait(store_scope=self.store_scope, api_category=api_category)
            try:
                if method == "GET":
                    response = self.session.get(
                        url,
                        params=params or {},
                        headers={"Authorization": self.token},
                        timeout=timeout,
                    )
                elif method == "POST":
                    response = self.session.post(
                        url,
                        json=payload or {},
                        headers={"Authorization": self.token},
                        timeout=timeout,
                    )
                else:
                    raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)
            except TimeoutError as exc:
                last_error = exc
                if attempt >= max_retries:
                    raise WBApiTimeoutError(WBApiTimeoutError.safe_message) from exc
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue

            if response.status_code in {401, 403}:
                raise WBApiAuthError(WBApiAuthError.safe_message)
            if response.status_code == 429:
                last_error = WBApiRateLimitError(WBApiRateLimitError.safe_message)
                if attempt >= max_retries:
                    raise last_error
                sleep(self.policy.backoff_seconds * (2**attempt))
                continue
            if response.status_code == 208:
                try:
                    data = response.json()
                except ValueError as exc:
                    raise WBApiAlreadyExistsError(response={}) from exc
                if not isinstance(data, dict):
                    raise WBApiAlreadyExistsError(response={})
                raise WBApiAlreadyExistsError(response=data)
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
        query = urlencode(params or {}, doseq=True)
        full_url = f"{url}?{query}" if query else url
        request = Request(full_url, headers=headers or {}, method="GET")
        return self._open(request, timeout=timeout)

    def post(self, url: str, *, json=None, headers=None, timeout=None):
        body = json_module_dumps(json or {})
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        request = Request(url, data=body, headers=request_headers, method="POST")
        return self._open(request, timeout=timeout)

    def _open(self, request: Request, *, timeout=None):
        try:
            with urlopen(request, timeout=(timeout or (None, None))[1]) as response:
                return UrllibResponse(status_code=response.status, body=response.read())
        except HTTPError as exc:
            return UrllibResponse(status_code=exc.code, body=exc.read())
        except TimeoutError:
            raise
        except OSError as exc:
            raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message) from exc


def json_module_dumps(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
