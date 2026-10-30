import time
from dataclasses import dataclass, field
from datetime import date, datetime

from practilizate.fetch import FetchError
from practilizate.logging import get_logger
from practilizate.models import Career, IngestResult, IngestStats, ListingCard, Offer
from practilizate.normalize import build_offer
from practilizate.parsing import parse_detail, parse_listing_cards
from practilizate.sources import OfferSource, SourceError

LOGGER = get_logger("practilizate.ingest")


@dataclass
class _Bucket:
    card: ListingCard
    careers: dict[str, Career] = field(default_factory=dict)
    fetched_at: datetime | None = None


def ingest_offers(source: OfferSource, *, as_of: date) -> IngestResult:
    started = time.perf_counter()
    stats = IngestStats()
    careers = source.discover_careers()
    stats.careers = len(careers)
    buckets: dict[str, _Bucket] = {}

    for career in careers:
        for page in source.iter_pages(career):
            stats.pages += 1
            cards = parse_listing_cards(page.html)
            for card in cards:
                stats.listing_refs += 1
                bucket = buckets.get(card.url)
                if bucket is None:
                    buckets[card.url] = _Bucket(
                        card=card,
                        careers={career.id: career},
                        fetched_at=page.fetched_at,
                    )
                else:
                    stats.duplicate_refs += 1
                    bucket.careers[career.id] = career

    offers: list[Offer] = []
    for url in sorted(buckets):
        bucket = buckets[url]
        detail = None
        try:
            detail_page = source.fetch_detail(url)
            stats.detail_pages += 1
            detail = parse_detail(detail_page.html)
            fetched_at = detail_page.fetched_at
        except (SourceError, FetchError, OSError) as error:
            stats.detail_failures.append(url)
            fetched_at = bucket.fetched_at
            LOGGER.warning("detail fetch failed", extra={"url": url, "error": str(error)})

        offer = build_offer(
            url=url,
            card=bucket.card,
            detail=detail,
            careers=list(bucket.careers.values()),
            as_of=as_of,
            fetched_at=fetched_at or datetime.now().astimezone(),
        )
        offers.append(offer)

    cache = getattr(source, "cache", None)
    if cache is not None:
        stats.cache_hits = cache.stats.cache_hits
        stats.network_requests = cache.stats.network_requests

    stats.unique_offers = len(offers)
    stats.duration_seconds = round(time.perf_counter() - started, 3)
    result = IngestResult(
        source=source.name,
        as_of=as_of,
        offers=offers,
        stats=stats,
    )
    LOGGER.info(
        "ingestion finished",
        extra={
            "source": source.name,
            "careers": stats.careers,
            "pages": stats.pages,
            "offers": stats.unique_offers,
            "duplicates": stats.duplicate_refs,
            "detail_failures": len(stats.detail_failures),
        },
    )
    return result
