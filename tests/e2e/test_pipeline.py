import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def offers_by_suffix(e2e_run: Path) -> dict[str, dict]:
    payload = load_json(e2e_run / "normalized_offers.json")
    return {
        offer["url"].rsplit("-", 1)[-1].removesuffix(".html"): offer for offer in payload["offers"]
    }


def test_fixture_run_normalizes_offers_and_preserves_multi_career(e2e_run: Path) -> None:
    payload = load_json(e2e_run / "normalized_offers.json")
    offers = payload["offers"]
    assert len(offers) == 12
    assert len({offer["url"] for offer in offers}) == 12

    by_id = offers_by_suffix(e2e_run)
    multi = by_id["90001"]
    assert [career["id"] for career in multi["careers"]] == ["1", "10"]
    assert [career["id"] for career in by_id["90007"]["careers"]] == ["10"]

    report = load_json(e2e_run / "ingest_report.json")
    assert report["stats"]["listing_refs"] == 13
    assert report["stats"]["duplicate_refs"] == 1
    assert report["stats"]["detail_failures"] == []
    assert report["stats"]["careers"] == 3


def test_fixture_run_surfaces_medium_hard_cases(e2e_run: Path) -> None:
    by_id = offers_by_suffix(e2e_run)

    assert by_id["90002"]["salary_amount"] is None
    assert by_id["90002"]["status"] == "expiring_soon"
    assert by_id["90003"]["deadline_at"] is None
    assert by_id["90003"]["status"] == "unknown"
    assert by_id["90004"]["published_at"] is None
    assert by_id["90005"]["salary_amount"] == 95000.0
    assert by_id["90006"]["company"] is None
    assert by_id["90006"]["company_normalized"] is None
    assert by_id["90008"]["status"] == "expired"
    assert by_id["90009"]["location"] is None
    assert by_id["90010"]["attendance"] == "Rotativo"
    assert by_id["90011"]["skills"] == []
    assert len(by_id["90012"]["skills"]) >= 2

    support = by_id["90003"]
    assert "reclutamiento@example.com" not in support["requirements_text"]
    assert "999 111 222" not in support["requirements_text"]
    assert "[contacto eliminado]" in support["requirements_text"]
