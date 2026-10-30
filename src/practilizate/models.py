from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Career(BaseModel):
    id: str
    name: str


class Page(BaseModel):
    url: str
    html: str
    career: Career
    page: int
    fetched_at: datetime


class DetailPage(BaseModel):
    url: str
    html: str
    fetched_at: datetime


class ListingCard(BaseModel):
    url: str
    title: str
    company: str | None = None
    requirements: str | None = None
    location: str | None = None
    modality: str | None = None
    attendance: str | None = None
    deadline_text: str | None = None


class DetailData(BaseModel):
    title: str | None = None
    company: str | None = None
    district: str | None = None
    department: str | None = None
    location: str | None = None
    modality: str | None = None
    attendance: str | None = None
    salary_text: str | None = None
    salary_amount: float | None = None
    salary_currency: str | None = None
    published_at: date | None = None
    published_raw: str | None = None
    deadline_at: date | None = None
    deadline_raw: str | None = None
    requirements_text: str = ""


class Offer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    offer_id: str
    url: str
    title: str
    company: str | None = None
    company_normalized: str | None = None
    location: str | None = None
    district: str | None = None
    department: str | None = None
    modality: str | None = None
    attendance: str | None = None
    salary_text: str | None = None
    salary_amount: float | None = None
    salary_currency: str | None = None
    published_at: date | None = None
    deadline_at: date | None = None
    status: str = "unknown"
    careers: list[Career] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    requirements_text: str = ""
    source_fetched_at: datetime


class IngestStats(BaseModel):
    careers: int = 0
    pages: int = 0
    listing_refs: int = 0
    unique_offers: int = 0
    duplicate_refs: int = 0
    detail_pages: int = 0
    detail_failures: list[str] = Field(default_factory=list)
    cache_hits: int = 0
    network_requests: int = 0
    duration_seconds: float = 0.0


class IngestResult(BaseModel):
    source: str
    as_of: date
    offers: list[Offer]
    stats: IngestStats


class QualityRuleResult(BaseModel):
    rule_id: str
    description: str
    severity: str
    checked: int
    failed: int
    pass_rate: float
    sample_failed_offer_ids: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    run_id: str
    source: str
    as_of: date
    generated_at: datetime
    offers_checked: int
    rules: list[QualityRuleResult]
    overall_score: float
    critical_failures: list[str] = Field(default_factory=list)
    passed: bool


class OutputPaths(BaseModel):
    run_dir: Path
    csv_path: Path
    excel_path: Path
    quality_path: Path
    manifest_path: Path
    normalized_path: Path
