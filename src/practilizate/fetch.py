import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.robotparser import RobotFileParser

import httpx

from practilizate.logging import get_logger
from practilizate.models import Career, DetailPage, Page

LOGGER = get_logger("practilizate.fetch")

ROBOTS_URL = "https://www.practicas.pe/robots.txt"


class FetchError(RuntimeError):
    pass


@dataclass
class FetchStats:
    cache_hits: int = 0
    network_requests: int = 0
    failures: list[str] = field(default_factory=list)


class HttpCache:
    def __init__(
        self,
        cache_dir: Path,
        *,
        user_agent: str,
        rate_limit_seconds: float = 1.0,
        timeout_seconds: float = 30.0,
        max_age_hours: float = 24.0,
    ) -> None:
        self.cache_dir = cache_dir
        self.rate_limit_seconds = max(rate_limit_seconds, 0.0)
        self.max_age = timedelta(hours=max_age_hours)
        self.stats = FetchStats()
        self._last_request = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"},
            timeout=timeout_seconds,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def _paths(self, url: str) -> tuple[Path, Path]:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.html", self.cache_dir / f"{key}.json"

    def _read_cache(self, url: str) -> str | None:
        html_path, meta_path = self._paths(url)
        if not html_path.is_file() or not meta_path.is_file():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(meta["fetched_at"])
        except (ValueError, KeyError, json.JSONDecodeError):
            return None
        if datetime.now(UTC) - fetched_at > self.max_age:
            return None
        try:
            with html_path.open("r", encoding="utf-8", newline="") as handle:
                html = handle.read()
        except OSError:
            return None
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        if meta.get("sha256") != digest:
            LOGGER.warning("cache entry checksum mismatch", extra={"url": url})
            return None
        return html

    def _write_cache(self, url: str, html: str, content_type: str | None) -> None:
        html_path, meta_path = self._paths(url)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        meta = {
            "url": url,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "sha256": digest,
            "content_type": content_type,
        }
        html_tmp = html_path.with_suffix(".html.tmp")
        meta_tmp = meta_path.with_suffix(".json.tmp")
        html_tmp.write_text(html, encoding="utf-8", newline="\n")
        meta_tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        html_tmp.replace(html_path)
        meta_tmp.replace(meta_path)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        remaining = self.rate_limit_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request = time.monotonic()

    def _request(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            self._throttle()
            try:
                response = self._client.get(url)
            except httpx.HTTPError as error:
                last_error = error
                LOGGER.warning(
                    "request failed",
                    extra={"url": url, "attempt": attempt + 1, "error": str(error)},
                )
                time.sleep(2**attempt)
                continue
            self.stats.network_requests += 1
            if response.status_code == 429 or response.status_code >= 500:
                last_error = FetchError(f"HTTP {response.status_code} for {url}")
                LOGGER.warning(
                    "retryable response",
                    extra={"url": url, "status": response.status_code, "attempt": attempt + 1},
                )
                time.sleep(2**attempt)
                continue
            if response.status_code >= 400:
                raise FetchError(f"HTTP {response.status_code} for {url}")
            return response
        raise FetchError(f"could not fetch {url}: {last_error}")

    def get(self, url: str, *, force: bool = False) -> str:
        if not force:
            cached = self._read_cache(url)
            if cached is not None:
                self.stats.cache_hits += 1
                return cached
        response = self._request(url)
        html = response.text
        self._write_cache(url, html, response.headers.get("content-type"))
        return html


class RobotsPolicy:
    def __init__(self, user_agent: str, timeout_seconds: float) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._parser: RobotFileParser | None = None

    def load(self) -> None:
        try:
            response = httpx.get(
                ROBOTS_URL,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout_seconds,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise FetchError(f"could not load robots.txt: {error}") from error
        parser = RobotFileParser()
        parser.set_url(ROBOTS_URL)
        parser.parse(response.text.splitlines())
        self._parser = parser

    def ensure_allowed(self, url: str) -> None:
        if self._parser is None:
            self.load()
        assert self._parser is not None
        if not self._parser.can_fetch(self.user_agent, url):
            raise FetchError(f"robots.txt disallows {url}")


class LiveSource:
    name = "live"

    def __init__(
        self,
        *,
        cache_dir: Path,
        user_agent: str,
        rate_limit_seconds: float,
        timeout_seconds: float,
        max_pages: int,
    ) -> None:
        self.cache = HttpCache(
            cache_dir,
            user_agent=user_agent,
            rate_limit_seconds=rate_limit_seconds,
            timeout_seconds=timeout_seconds,
        )
        self.robots = RobotsPolicy(user_agent, timeout_seconds)
        self.max_pages = max_pages
        self._careers: list[Career] = []

    def discover_careers(self) -> list[Career]:
        from practilizate.parsing import parse_careers

        url = self._search_url(page=1)
        self.robots.ensure_allowed(url)
        html = self.cache.get(url)
        careers = parse_careers(html)
        if not careers:
            raise FetchError("no careers found in the live filter form")
        self._careers = careers
        LOGGER.info("discovered careers", extra={"count": len(careers), "source": self.name})
        return careers

    def _search_url(self, page: int, career_id: str | None = None) -> str:
        url = (
            "https://www.practicas.pe/resultados-busqueda.php"
            f"?page={page}&sort=1-fecha_publicacion&modalidad=PREPROFESIONAL&dep=15"
        )
        if career_id is not None:
            url += f"&carrera={career_id}"
        return url

    def iter_pages(self, career: Career):
        from practilizate.parsing import parse_last_page, parse_listing_cards

        last_page: int | None = None
        for page_number in range(1, self.max_pages + 1):
            url = self._search_url(page=page_number, career_id=career.id)
            self.robots.ensure_allowed(url)
            html = self.cache.get(url)
            cards = parse_listing_cards(html)
            if not cards:
                LOGGER.info(
                    "empty listing page; stopping career",
                    extra={"career": career.name, "page": page_number},
                )
                return
            if last_page is None:
                last_page = parse_last_page(html)
            yield Page(
                url=url,
                html=html,
                career=career,
                page=page_number,
                fetched_at=datetime.now(UTC),
            )
            if last_page is not None and page_number >= last_page:
                return

    def fetch_detail(self, url: str) -> DetailPage:
        self.robots.ensure_allowed(url)
        html = self.cache.get(url)
        return DetailPage(url=url, html=html, fetched_at=datetime.now(UTC))

    def close(self) -> None:
        self.cache.close()
