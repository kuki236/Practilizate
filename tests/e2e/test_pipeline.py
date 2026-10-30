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


def test_quality_report_flags_expected_failures(e2e_run: Path) -> None:
    report = load_json(e2e_run / "quality_report.json")
    assert report["offers_checked"] == 12
    assert report["passed"] is True
    assert report["critical_failures"] == []
    assert report["overall_score"] == 0.9427

    rules = {rule["rule_id"]: rule for rule in report["rules"]}
    expected = {
        "R01": ["90006"],
        "R04": ["90004"],
        "R05": ["90003"],
        "R06": ["90008"],
        "R08": ["90005"],
        "R09": ["90006"],
        "R10": ["90009"],
        "R12": ["90010"],
        "R14": ["90001", "90007"],
        "R15": ["90011"],
    }
    for rule_id, samples in expected.items():
        assert rules[rule_id]["failed"] == len(samples), rule_id
        assert rules[rule_id]["sample_failed_offer_ids"] == samples, rule_id

    for rule_id in ("R02", "R03", "R07", "R11", "R13", "R16", "R17"):
        assert rules[rule_id]["failed"] == 0, rule_id

    scores = {
        offer["offer_id"]: offer["quality_score"]
        for offer in load_json(e2e_run / "normalized_offers.json")["offers"]
    }
    assert scores["90002"] == 1.0
    assert scores["90012"] == 1.0
    assert scores["90006"] < 0.9
    assert scores["90001"] < 1.0


def test_strict_mode_blocks_warning_only_runs(e2e_strict_run: Path) -> None:
    manifest = load_json(e2e_strict_run / "run_manifest.json")
    assert manifest["status"] == "failed_quality"
    assert manifest["quality"]["passed"] is True
    assert manifest["quality"]["strict"] is True
    assert manifest["quality"]["failed_rules"]
    report = load_json(e2e_strict_run / "quality_report.json")
    assert report["passed"] is True


def test_database_contains_expected_star_schema_rows(e2e_run: Path, e2e_db) -> None:
    from sqlalchemy import text

    expected = {
        "fact_ofertas": 12,
        "dim_fecha": 20,
        "dim_empresa": 10,
        "dim_ubicacion": 8,
        "dim_carrera": 3,
        "dim_habilidad": 21,
        "dim_modalidad": 1,
        "dim_asistencia": 3,
        "bridge_oferta_carrera": 13,
        "bridge_oferta_habilidad": 34,
    }
    with e2e_db.connect() as connection:
        for table, count in expected.items():
            actual = connection.execute(text(f"select count(*) from {table}")).scalar_one()
            assert actual == count, table

        duplicate_urls = connection.execute(
            text(
                "select count(*) from (select url from fact_ofertas group by url having count(*) > 1) d"
            )
        ).scalar_one()
        assert duplicate_urls == 0

        multi_career = connection.execute(
            text("select count(*) from bridge_oferta_carrera where offer_id = 90001")
        ).scalar_one()
        assert multi_career == 2

        snapshot = connection.execute(
            text(
                "select title, company_id, location_id, date_id, salary_amount, deadline_at, "
                "status, quality_score, url from fact_ofertas where offer_id = :id"
            ),
            {"id": 90006},
        ).one()
        assert snapshot.company_id is None
        assert snapshot.status == "active"
        assert 0 < float(snapshot.quality_score) < 1

        expired = connection.execute(
            text("select status, deadline_at from fact_ofertas where offer_id = 90008")
        ).one()
        assert expired.status == "expired"

        invalid_date = connection.execute(
            text("select date_id, published_at from fact_ofertas where offer_id = 90004")
        ).one()
        assert invalid_date.date_id is None
        assert invalid_date.published_at is None

        view_rows = connection.execute(
            text(
                "select offer_id, company, careers, skills from v_dashboard_ofertas "
                "where offer_id = 90001"
            )
        ).one()
        assert view_rows.company == "Banco Andino"
        assert view_rows.careers.count(";") == 1
        assert view_rows.skills.count(";") == 4

        schema_version = connection.execute(
            text("select value from practilizate_meta where key = 'schema_version'")
        ).scalar_one()
        assert schema_version == "1"

        view_count = connection.execute(
            text("select count(*) from v_dashboard_ofertas")
        ).scalar_one()
        assert view_count == 12

        load_report = load_json(e2e_run / "database_load.json")
        assert load_report["counts"]["fact_ofertas"] == 12


def test_load_command_is_repeatable(e2e_run: Path, e2e_db, e2e_database_url: str) -> None:
    from conftest import run_cli
    from sqlalchemy import text

    result = run_cli(
        "load",
        "--run-id",
        "e2e",
        "--artifacts-dir",
        str(e2e_run),
        database_url=e2e_database_url,
    )
    assert result.returncode == 0, result.stderr
    counts = json.loads(result.stdout)
    assert counts["fact_ofertas"] == 12
    assert counts["bridge_oferta_carrera"] == 13

    with e2e_db.connect() as connection:
        assert connection.execute(text("select count(*) from fact_ofertas")).scalar_one() == 12
        assert (
            connection.execute(text("select count(*) from bridge_oferta_habilidad")).scalar_one()
            == 34
        )


def test_quality_command_prints_report(e2e_run: Path) -> None:
    from conftest import run_cli

    result = run_cli("quality", "--run-id", "e2e", "--artifacts-dir", str(e2e_run))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["overall_score"] == 0.9427
    assert report["passed"] is True
