from collections.abc import Iterator
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from practilizate.logging import get_logger
from practilizate.models import Career, DetailPage, Page

LOGGER = get_logger("practilizate.sources")


class SourceError(RuntimeError):
    pass


class OfferSource(Protocol):
    name: str

    def discover_careers(self) -> list[Career]: ...

    def iter_pages(self, career: Career) -> Iterator[Page]: ...

    def fetch_detail(self, url: str) -> DetailPage: ...


def parse_careers(html: str) -> list[Career]:
    soup = BeautifulSoup(html, "html.parser")
    careers: dict[str, Career] = {}
    for field in soup.select('input[name="carrera"]'):
        career_id = (field.get("value") or "").strip()
        name = (field.get("data-nombre") or "").strip()
        if not career_id or not name or career_id in careers:
            continue
        careers[career_id] = Career(id=career_id, name=name)
    return list(careers.values())


class FixtureSource:
    name = "fixtures"

    def __init__(self, fixtures_dir: Path, as_of: date, max_pages: int = 50) -> None:
        self.fixtures_dir = fixtures_dir
        self.as_of = as_of
        self.max_pages = max_pages
        self._fetched_at = datetime.combine(as_of, time(0, 0), tzinfo=UTC)

    def _read(self, path: Path) -> str:
        if not path.is_file():
            raise SourceError(f"fixture file not found: {path}")
        return path.read_text(encoding="utf-8")

    def discover_careers(self) -> list[Career]:
        careers = parse_careers(self._read(self.fixtures_dir / "filter.html"))
        if not careers:
            raise SourceError("fixture filter has no careers")
        LOGGER.info("discovered careers", extra={"count": len(careers), "source": self.name})
        return careers

    def iter_pages(self, career: Career) -> Iterator[Page]:
        for page_number in range(1, self.max_pages + 1):
            path = self.fixtures_dir / "search" / f"{career.id}-page-{page_number}.html"
            if not path.is_file():
                return
            url = (
                "https://www.practicas.pe/resultados-busqueda.php"
                f"?carrera={career.id}&modalidad=PREPROFESIONAL&dep=15&page={page_number}"
            )
            yield Page(
                url=url,
                html=self._read(path),
                career=career,
                page=page_number,
                fetched_at=self._fetched_at,
            )

    def fetch_detail(self, url: str) -> DetailPage:
        name = Path(urlparse(url).path).name
        path = self.fixtures_dir / "detail" / name
        return DetailPage(url=url, html=self._read(path), fetched_at=self._fetched_at)
