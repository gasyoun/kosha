"""Request correlation + low-cardinality ops metrics (W2C, H2348).

Release observability, not a visitor-analytics product. History/auth stay
off (D10). Metric labels are a closed set: HTTP method, FastAPI *route
template*, status class, readiness check name/status, and a single
``data_version`` info label. Headwords, query strings, raw paths, request
IDs, IPs, and dataset ids are forbidden as labels — those would explode
cardinality and leak lookup traffic.

Correlation:

* incoming ``X-Request-ID`` or ``X-Correlation-ID`` is accepted when it
  matches a bounded safe token; otherwise a UUID4 is minted;
* every response echoes ``X-Request-ID``;
* structured logs carry ``request_id=`` and the *template* route, never
  the raw path.

Metrics export as Prometheus text at ``GET /metrics`` (stdlib renderer —
no prometheus-client dependency, no history router).
"""

from __future__ import annotations

import logging
import re
import threading
import time
import uuid
from typing import Any, Iterable, Mapping

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from kosha.api.readiness import ReadinessReport

CHECK_STATUSES: tuple[str, ...] = (
    "ok",
    "fail",
    "disabled",
    "absent",
    "unconfigured",
)

log = logging.getLogger("kosha.api")

REQUEST_ID_HEADER = "x-request-id"
CORRELATION_ID_HEADER = "x-correlation-id"
RESPONSE_HEADER = "X-Request-ID"
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")

KNOWN_METHODS = frozenset(
    {"GET", "POST", "DELETE", "HEAD", "OPTIONS", "PUT", "PATCH"}
)
STATUS_CLASSES = frozenset({"1xx", "2xx", "3xx", "4xx", "5xx"})
# H2343 check names. data_version_match is only present when expected
# version is configured; others always appear.
H2343_CHECK_NAMES = frozenset(
    {
        "core_db",
        "inflections_db",
        "layers_db",
        "data_version",
        "data_version_match",
        "citation_archives",
        "history",
    }
)
CHECK_STATUSES_FROZEN = frozenset(CHECK_STATUSES)

#: Closed label-key vocabulary. Tests pin this so a new high-card key
#: cannot land silently.
ALLOWED_LABEL_KEYS = frozenset(
    {"method", "route", "status_class", "name", "status", "check", "version"}
)
FORBIDDEN_LABEL_KEYS = frozenset(
    {
        "headword",
        "query",
        "q",
        "key",
        "path",
        "lemma",
        "form",
        "sense_id",
        "request_id",
        "ip",
        "user",
        "anon_id",
        "dataset_id",
    }
)

DURATION_BUCKETS: tuple[float, ...] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

METRIC_HTTP_REQUESTS = "kosha_http_requests_total"
METRIC_HTTP_DURATION = "kosha_http_request_duration_seconds"
METRIC_READY = "kosha_ready"
METRIC_READY_CHECK = "kosha_ready_check"
METRIC_READY_FAILURES = "kosha_ready_failures_total"
METRIC_DATA_VERSION = "kosha_data_version_info"

METRIC_NAMES: tuple[str, ...] = (
    METRIC_HTTP_REQUESTS,
    METRIC_HTTP_DURATION,
    METRIC_READY,
    METRIC_READY_CHECK,
    METRIC_READY_FAILURES,
    METRIC_DATA_VERSION,
)

_ROUTE_SAFE = re.compile(r"^[A-Za-z0-9_{}/.\-]+$")
_VERSION_SAFE = re.compile(r"^[A-Za-z0-9._+\-]+$")


class LabelError(ValueError):
    """Raised when a metric would take a forbidden or unknown label key."""


def _assert_labels(labels: Mapping[str, str]) -> None:
    keys = set(labels)
    banned = keys & FORBIDDEN_LABEL_KEYS
    if banned:
        raise LabelError(f"forbidden high-cardinality label key(s): {sorted(banned)}")
    unknown = keys - ALLOWED_LABEL_KEYS
    if unknown:
        raise LabelError(f"unknown metric label key(s): {sorted(unknown)}")


def sanitize_route(template: str) -> str:
    if template and _ROUTE_SAFE.match(template):
        return template
    return "other"


def sanitize_version(value: str | None) -> str:
    if value and _VERSION_SAFE.match(value):
        return value
    return "unknown"


def resolve_request_id(scope: Scope) -> str:
    """Accept a bounded incoming token or mint a UUID4."""
    incoming: dict[str, str] = {}
    for raw_k, raw_v in scope.get("headers") or ():
        incoming[raw_k.decode("latin-1").lower()] = raw_v.decode("latin-1")
    for header in (REQUEST_ID_HEADER, CORRELATION_ID_HEADER):
        token = incoming.get(header, "").strip()
        if token and REQUEST_ID_RE.match(token):
            return token
    return str(uuid.uuid4())


def route_template(scope: Scope) -> str:
    """FastAPI/Starlette route path template — never the raw URL path."""
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return sanitize_route(path)
    return "unmatched"


def status_class_of(status: int) -> str:
    bucket = f"{int(status) // 100}xx"
    return bucket if bucket in STATUS_CLASSES else "5xx"


class _Histogram:
    __slots__ = ("counts", "sum", "n")

    def __init__(self) -> None:
        self.counts = [0] * (len(DURATION_BUCKETS) + 1)
        self.sum = 0.0
        self.n = 0

    def observe(self, value: float) -> None:
        self.sum += value
        self.n += 1
        for i, le in enumerate(DURATION_BUCKETS):
            if value <= le:
                self.counts[i] += 1
        self.counts[-1] += 1


class MetricsRegistry:
    """In-process, process-local counters/gauges/histograms. Not a product."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._hists: dict[tuple[str, tuple[tuple[str, str], ...]], _Histogram] = {}

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._hists.clear()

    def inc(self, name: str, labels: Mapping[str, str], amount: float = 1.0) -> None:
        _assert_labels(labels)
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + amount

    def set_gauge(self, name: str, labels: Mapping[str, str], value: float) -> None:
        _assert_labels(labels)
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, labels: Mapping[str, str], value: float) -> None:
        _assert_labels(labels)
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            hist = self._hists.get(key)
            if hist is None:
                hist = _Histogram()
                self._hists[key] = hist
            hist.observe(value)

    def clear_gauges(self, name: str) -> None:
        with self._lock:
            self._gauges = {k: v for k, v in self._gauges.items() if k[0] != name}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "hists": {
                    k: (h.counts[:], h.sum, h.n) for k, h in self._hists.items()
                },
            }


REGISTRY = MetricsRegistry()


def reset_metrics() -> None:
    """Test helper — empty the process-local registry."""
    REGISTRY.reset()


def record_http_request(
    method: str, route: str, status_class: str, duration_s: float
) -> None:
    labels = {
        "method": method if method in KNOWN_METHODS else "OTHER",
        "route": sanitize_route(route),
        "status_class": status_class if status_class in STATUS_CLASSES else "5xx",
    }
    REGISTRY.inc(METRIC_HTTP_REQUESTS, labels)
    REGISTRY.observe(
        METRIC_HTTP_DURATION,
        {"method": labels["method"], "route": labels["route"]},
        duration_s,
    )


def record_readiness(
    report: ReadinessReport,
    *,
    increment_failures: bool = False,
    request_id: str | None = None,
) -> None:
    """Export H2343 check names/statuses as gauges.

    ``increment_failures`` is True only for the ``GET /ready`` path so a
    scrape of ``/metrics`` does not inflate the failure counter.
    """
    REGISTRY.set_gauge(METRIC_READY, {}, 1.0 if report.ready else 0.0)
    REGISTRY.clear_gauges(METRIC_READY_CHECK)
    REGISTRY.clear_gauges(METRIC_DATA_VERSION)

    failed: list[str] = []
    for check in report.checks:
        name = check.name
        for status in CHECK_STATUSES_FROZEN:
            REGISTRY.set_gauge(
                METRIC_READY_CHECK,
                {"name": name, "status": status},
                1.0 if check.status == status else 0.0,
            )
        if increment_failures and check.required and check.status == "fail":
            REGISTRY.inc(METRIC_READY_FAILURES, {"check": name})
            failed.append(name)

    REGISTRY.set_gauge(
        METRIC_DATA_VERSION,
        {"version": sanitize_version(report.data_version)},
        1.0,
    )

    if increment_failures and not report.ready:
        log.warning(
            "readiness_fail request_id=%s data_version=%s failed=%s",
            request_id or "-",
            report.data_version or "-",
            ",".join(failed) or "-",
        )


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _fmt_labels(labels: Iterable[tuple[str, str]]) -> str:
    items = list(labels)
    if not items:
        return ""
    inner = ",".join(f'{k}="{_escape_label(v)}"' for k, v in items)
    return "{" + inner + "}"


def render_prometheus() -> str:
    """Prometheus 0.0.4 text exposition. Help/type lines are stable."""
    snap = REGISTRY.snapshot()
    lines: list[str] = []

    lines.append("# HELP kosha_http_requests_total HTTP requests by method, route template, status class")
    lines.append("# TYPE kosha_http_requests_total counter")
    for (name, labels), value in sorted(snap["counters"].items()):
        if name != METRIC_HTTP_REQUESTS:
            continue
        lines.append(f"{name}{_fmt_labels(labels)} {value:.0f}")

    lines.append(
        "# HELP kosha_http_request_duration_seconds HTTP request duration in seconds (route template only)"
    )
    lines.append("# TYPE kosha_http_request_duration_seconds histogram")
    for (name, labels), (counts, total, n) in sorted(snap["hists"].items()):
        if name != METRIC_HTTP_DURATION:
            continue
        for i, le in enumerate(DURATION_BUCKETS):
            bucket_labels = labels + (("le", f"{le:g}"),)
            lines.append(
                f"{name}_bucket{_fmt_labels(bucket_labels)} {counts[i]:.0f}"
            )
        inf_labels = labels + (("le", "+Inf"),)
        lines.append(f"{name}_bucket{_fmt_labels(inf_labels)} {counts[-1]:.0f}")
        lines.append(f"{name}_sum{_fmt_labels(labels)} {total}")
        lines.append(f"{name}_count{_fmt_labels(labels)} {n:.0f}")

    lines.append("# HELP kosha_ready 1 if GET /ready would succeed, else 0")
    lines.append("# TYPE kosha_ready gauge")
    ready_rows = [
        (labels, value)
        for (name, labels), value in snap["gauges"].items()
        if name == METRIC_READY
    ]
    if ready_rows:
        for labels, value in sorted(ready_rows):
            lines.append(f"{METRIC_READY}{_fmt_labels(labels)} {value:.0f}")
    else:
        lines.append(f"{METRIC_READY} 0")

    lines.append(
        "# HELP kosha_ready_check 1 when the named H2343 readiness check is in this status"
    )
    lines.append("# TYPE kosha_ready_check gauge")
    for (name, labels), value in sorted(snap["gauges"].items()):
        if name != METRIC_READY_CHECK:
            continue
        lines.append(f"{name}{_fmt_labels(labels)} {value:.0f}")

    lines.append(
        "# HELP kosha_ready_failures_total Required H2343 checks that failed on GET /ready"
    )
    lines.append("# TYPE kosha_ready_failures_total counter")
    for (name, labels), value in sorted(snap["counters"].items()):
        if name != METRIC_READY_FAILURES:
            continue
        lines.append(f"{name}{_fmt_labels(labels)} {value:.0f}")

    lines.append("# HELP kosha_data_version_info Store meta.data_version (info gauge)")
    lines.append("# TYPE kosha_data_version_info gauge")
    for (name, labels), value in sorted(snap["gauges"].items()):
        if name != METRIC_DATA_VERSION:
            continue
        lines.append(f"{name}{_fmt_labels(labels)} {value:.0f}")

    lines.append("")
    return "\n".join(lines)


class ObservabilityMiddleware:
    """ASGI middleware: correlation header + request counters + structured log."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        request_id = resolve_request_id(scope)
        state = scope.get("state")
        if not isinstance(state, dict):
            state = {}
            scope["state"] = state
        state["request_id"] = request_id

        status_holder = {"code": 500}

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = int(message.get("status") or 500)
                headers = MutableHeaders(raw=message.setdefault("headers", []))
                if RESPONSE_HEADER.lower().encode("latin-1") not in {
                    k.lower() for k, _ in message["headers"]
                }:
                    headers.append(RESPONSE_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - started
            method = (scope.get("method") or "GET").upper()
            route = route_template(scope)
            status = status_holder["code"]
            klass = status_class_of(status)
            record_http_request(method, route, klass, duration)
            log.info(
                "http_request request_id=%s method=%s route=%s status=%s duration_ms=%.1f",
                request_id,
                method if method in KNOWN_METHODS else "OTHER",
                route,
                status,
                duration * 1000.0,
            )
